import asyncio
from typing import List, Tuple, Optional, Any, Dict
from fastapi import UploadFile
from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.invoice_repository import InvoiceRepository
from app.services.storage.base import BaseStorageProvider
from app.services.ocr.base import BaseOCRProvider
from app.services.llm.base import BaseLLMProvider
from app.validators.file_validator import FileValidator
from app.validators.invoice_validator import validate_extracted_invoice
from app.core.config import settings
from app.core.exceptions import (
    AIExtractionError,
    OCRExtractionError,
    BaseAppException,
    InvoiceCorrectionError,
)
from app.core.logging import logger, log_timing
from app.services.processors.base import BaseDocumentProcessor
from app.services.processors.invoice_processor import InvoiceDocumentProcessor
from app.schemas.invoice import ExtractedInvoiceData


class InvoiceService:
    """Service layer orchestrating storage, OCR, AI extraction, and DB operations."""

    def __init__(
        self,
        repository: InvoiceRepository,
        storage_provider: BaseStorageProvider,
        ocr_provider: BaseOCRProvider,
        llm_provider: BaseLLMProvider,
        document_processor: BaseDocumentProcessor | None = None,
    ):
        self.repo = repository
        self.storage = storage_provider
        self.ocr = ocr_provider
        self.document_processor = document_processor or InvoiceDocumentProcessor(llm_provider)

    async def upload_invoice(self, file: UploadFile) -> Invoice:
        """Validates uploaded file, stores binary stream, and creates DB record."""
        extra_logs = {"filename": file.filename or "unknown"}
        
        with log_timing("File_Upload_And_Validation", extra=extra_logs):
            # 1. Validate file format, extension, size, and header magic bytes
            file_bytes, safe_filename, ext = await FileValidator.validate_upload(file)
            
            # 2. Save file to storage target
            file.file.seek(0)
            relative_path, full_path, file_size = await self.storage.save_file(
                file.file, safe_filename
            )

            # 3. Create database entity
            invoice = self.repo.create(
                filename=file.filename or safe_filename,
                file_path=relative_path,
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                status=InvoiceStatus.UPLOADED,
            )
            return invoice

    async def extract_invoice(self, invoice_id: str) -> Invoice:
        """
        Runs OCR and LLM structured data extraction pipeline for an uploaded invoice.
        Updates database record at each lifecycle stage and records timing metrics.
        """
        invoice = self.repo.get_by_id(invoice_id)
        full_file_path = await self.storage.get_file_path(invoice.file_path)

        ocr_metrics: Dict[str, Any] = {"invoice_id": invoice_id, "file_path": full_file_path}

        try:
            processing_limit = max(1, settings.MAX_CONCURRENT_PROCESSING)
            semaphore = getattr(self, "_processing_semaphore", None)
            if semaphore is None or getattr(self, "_processing_limit", None) != processing_limit:
                semaphore = asyncio.Semaphore(processing_limit)
                self._processing_semaphore = semaphore
                self._processing_limit = processing_limit

            async with semaphore:
                return await self._extract_invoice_with_limit(
                    invoice_id,
                    invoice,
                    full_file_path,
                    ocr_metrics,
                )
        except Exception as e:
            logger.error(f"Invoice pipeline processing failed for ID '{invoice_id}': {str(e)}")
            self.repo.mark_failed(invoice_id, str(e))
            raise

    async def _extract_invoice_with_limit(
        self,
        invoice_id: str,
        invoice: Invoice,
        full_file_path: str,
        ocr_metrics: Dict[str, Any],
    ) -> Invoice:
        try:
            # Stage 1: OCR Text Extraction
            with log_timing("OCR_Extraction", extra=ocr_metrics) as t_metrics:
                ocr_result = await self._with_retry(
                    operation_name="OCR extraction",
                    operation=lambda: self.ocr.extract_text(
                        file_path=full_file_path,
                        mime_type=invoice.mime_type,
                    ),
                    retryable_exceptions=(OCRExtractionError,),
                )
                t_metrics["pages"] = ocr_result.pages
                t_metrics["ocr_confidence"] = ocr_result.confidence

            # Update DB with raw OCR text and metadata
            ocr_metadata = {
                "pages": ocr_result.pages,
                "detected_language": ocr_result.detected_language,
                "confidence": ocr_result.confidence,
                "duration_ms": ocr_metrics.get("duration_ms", 0),
            }
            invoice = self.repo.update_ocr_data(
                invoice_id=invoice_id,
                raw_ocr_text=ocr_result.raw_text,
                ocr_metadata=ocr_metadata,
                status=InvoiceStatus.OCR_COMPLETED,
            )

            # Stage 2: LLM Structured Data Parsing
            llm_metrics: Dict[str, Any] = {"invoice_id": invoice_id}
            with log_timing("LLM_Structured_Extraction", extra=llm_metrics) as t_llm:
                extracted_data = await self._with_retry(
                    operation_name="LLM extraction",
                    operation=lambda: self.document_processor.extract(ocr_result.raw_text),
                    retryable_exceptions=(AIExtractionError,),
                )
                if extracted_data.validation_warnings:
                    logger.warning(
                        "Invoice extraction validation warnings: "
                        + "; ".join(extracted_data.validation_warnings),
                        extra={"invoice_id": invoice_id},
                    )
                t_llm["llm_confidence"] = extracted_data.confidence_score

            # Update DB with structured JSON and mark EXTRACTED
            invoice = self.repo.update_extracted_data(
                invoice_id=invoice_id,
                extracted_data=extracted_data.model_dump(),
                overall_confidence=extracted_data.confidence_score,
                status=InvoiceStatus.EXTRACTED,
            )
            return invoice
        except Exception:
            raise

    async def _with_retry(
        self,
        operation_name: str,
        operation,
        retryable_exceptions: tuple[type[BaseAppException], ...],
    ):
        max_attempts = max(1, settings.EXTRACTION_MAX_ATTEMPTS)
        for attempt in range(1, max_attempts + 1):
            try:
                return await operation()
            except retryable_exceptions as exc:
                if attempt == max_attempts:
                    raise
                delay = settings.EXTRACTION_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    f"{operation_name} failed on attempt {attempt}/{max_attempts}; "
                    f"retrying in {delay:.2f}s: {exc}"
                )
                await asyncio.sleep(delay)

    async def process_invoice(self, file: UploadFile) -> Invoice:
        """Helper combining upload and immediate extraction into a single call."""
        invoice = await self.upload_invoice(file)
        processed_invoice = await self.extract_invoice(invoice.id)
        return processed_invoice

    def get_invoice(self, invoice_id: str) -> Invoice:
        """Retrieves invoice by ID."""
        return self.repo.get_by_id(invoice_id)

    async def delete_invoice(self, invoice_id: str) -> None:
        """Removes the invoice record and its source document from storage."""
        invoice = self.repo.get_by_id(invoice_id)
        await self.storage.delete_file(invoice.file_path)
        self.repo.delete(invoice_id)

    def correct_invoice(
        self,
        invoice_id: str,
        extracted_data: ExtractedInvoiceData,
    ) -> Invoice:
        """Validates and persists user corrections without changing AI confidence."""
        invoice = self.repo.get_by_id(invoice_id)
        if invoice.status != InvoiceStatus.EXTRACTED or invoice.extracted_data is None:
            raise InvoiceCorrectionError()

        extracted_data.validation_warnings = validate_extracted_invoice(extracted_data)
        return self.repo.update_corrected_data(
            invoice_id=invoice_id,
            extracted_data=extracted_data.model_dump(),
        )

    def list_invoices(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[InvoiceStatus] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Invoice], int]:
        """Lists paginated invoices."""
        return self.repo.list_invoices(
            skip=skip,
            limit=limit,
            status=status,
            search=search,
        )
