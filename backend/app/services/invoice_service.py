from typing import List, Tuple, Optional, Any, Dict
from fastapi import UploadFile
from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.invoice_repository import InvoiceRepository
from app.services.storage.base import BaseStorageProvider
from app.services.ocr.base import BaseOCRProvider
from app.services.llm.base import BaseLLMProvider
from app.validators.file_validator import FileValidator
from app.core.logging import logger, log_timing


class InvoiceService:
    """Service layer orchestrating storage, OCR, AI extraction, and DB operations."""

    def __init__(
        self,
        repository: InvoiceRepository,
        storage_provider: BaseStorageProvider,
        ocr_provider: BaseOCRProvider,
        llm_provider: BaseLLMProvider,
    ):
        self.repo = repository
        self.storage = storage_provider
        self.ocr = ocr_provider
        self.llm = llm_provider

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
            # Stage 1: OCR Text Extraction
            with log_timing("OCR_Extraction", extra=ocr_metrics) as t_metrics:
                ocr_result = await self.ocr.extract_text(
                    file_path=full_file_path,
                    mime_type=invoice.mime_type,
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
                extracted_data = await self.llm.extract_structured_invoice(
                    raw_ocr_text=ocr_result.raw_text
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

        except Exception as e:
            logger.error(f"Invoice pipeline processing failed for ID '{invoice_id}': {str(e)}")
            self.repo.mark_failed(invoice_id, str(e))
            raise

    async def process_invoice(self, file: UploadFile) -> Invoice:
        """Helper combining upload and immediate extraction into a single call."""
        invoice = await self.upload_invoice(file)
        processed_invoice = await self.extract_invoice(invoice.id)
        return processed_invoice

    def get_invoice(self, invoice_id: str) -> Invoice:
        """Retrieves invoice by ID."""
        return self.repo.get_by_id(invoice_id)

    def list_invoices(
        self, skip: int = 0, limit: int = 50, status: Optional[InvoiceStatus] = None
    ) -> Tuple[List[Invoice], int]:
        """Lists paginated invoices."""
        return self.repo.list_invoices(skip=skip, limit=limit, status=status)
