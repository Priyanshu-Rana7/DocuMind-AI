import pytest
from io import BytesIO
from fastapi import UploadFile
from app.services.invoice_service import InvoiceService
from app.repositories.invoice_repository import InvoiceRepository
from app.services.storage.local_storage import LocalStorageProvider
from app.services.ocr.mock_ocr import MockOCRProvider
from app.services.llm.mock_llm import MockLLMProvider
from app.models.invoice import InvoiceStatus
from app.schemas.invoice import ExtractedInvoiceData, InvoiceItemSchema
from app.validators.invoice_validator import validate_extracted_invoice
from app.core.exceptions import AIExtractionError, LLMConfigurationError
from app.services.processors.invoice_processor import InvoiceDocumentProcessor


@pytest.fixture
def invoice_service(db_session, tmp_path):
    repo = InvoiceRepository(db_session)
    storage = LocalStorageProvider(upload_dir=str(tmp_path))
    ocr = MockOCRProvider()
    llm = MockLLMProvider()
    return InvoiceService(repository=repo, storage_provider=storage, ocr_provider=ocr, llm_provider=llm)


@pytest.mark.asyncio
async def test_upload_invoice_service(invoice_service: InvoiceService, sample_pdf_bytes: bytes):
    file_obj = BytesIO(sample_pdf_bytes)
    upload_file = UploadFile(filename="test_invoice.pdf", file=file_obj, headers={"content-type": "application/pdf"})

    invoice = await invoice_service.upload_invoice(upload_file)
    assert invoice.id is not None
    assert invoice.status == InvoiceStatus.UPLOADED
    assert invoice.filename == "test_invoice.pdf"


@pytest.mark.asyncio
async def test_extract_invoice_service(invoice_service: InvoiceService, sample_pdf_bytes: bytes):
    file_obj = BytesIO(sample_pdf_bytes)
    upload_file = UploadFile(filename="test_invoice.pdf", file=file_obj, headers={"content-type": "application/pdf"})

    invoice = await invoice_service.upload_invoice(upload_file)
    processed = await invoice_service.extract_invoice(invoice.id)

    assert processed.status == InvoiceStatus.EXTRACTED
    assert processed.raw_ocr_text is not None
    assert "INVOICE #" in processed.raw_ocr_text
    assert processed.extracted_data is not None
    assert processed.extracted_data["vendor_name"] == "Acme Cloud Tech Inc."
    assert processed.overall_confidence > 0.9


def test_extracted_data_validation_reports_amount_mismatches():
    data = ExtractedInvoiceData(
        subtotal=100,
        tax=10,
        discount=0,
        total=125,
        invoice_items=[
            InvoiceItemSchema(
                description="Monitor",
                quantity=2,
                unit_price=40,
                total=75,
            )
        ],
    )

    warnings = validate_extracted_invoice(data)

    assert "Line item 1 total does not match quantity × unit price." in warnings
    assert "Line item totals do not match the extracted subtotal." in warnings
    assert "Subtotal, discount, and tax do not reconcile with the extracted total." in warnings


def test_extracted_data_validation_accepts_tolerance_and_missing_optional_amounts():
    data = ExtractedInvoiceData(
        subtotal=100,
        tax=0,
        discount=0,
        total=100.01,
        invoice_items=[],
        invoice_date=None,
        due_date=None,
    )

    assert validate_extracted_invoice(data) == []


@pytest.mark.asyncio
async def test_invoice_document_processor_extracts_and_validates_with_llm():
    processor = InvoiceDocumentProcessor(MockLLMProvider())

    extracted = await processor.extract("invoice text")

    assert extracted.vendor_name == "Acme Cloud Tech Inc."
    assert extracted.validation_warnings == []


@pytest.mark.asyncio
async def test_extraction_retry_recovers_from_transient_failure(invoice_service, monkeypatch):
    attempts = 0

    async def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise AIExtractionError("temporary provider failure")
        return "recovered"

    monkeypatch.setattr("app.services.invoice_service.settings.EXTRACTION_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(
        "app.services.invoice_service.settings.EXTRACTION_RETRY_BACKOFF_SECONDS", 0
    )

    result = await invoice_service._with_retry(
        operation_name="test extraction",
        operation=flaky_operation,
        retryable_exceptions=(AIExtractionError,),
    )

    assert result == "recovered"
    assert attempts == 3


@pytest.mark.asyncio
async def test_extraction_retry_does_not_retry_configuration_failures(
    invoice_service, monkeypatch
):
    attempts = 0

    async def unavailable_operation():
        nonlocal attempts
        attempts += 1
        raise LLMConfigurationError("missing provider configuration")

    monkeypatch.setattr("app.services.invoice_service.settings.EXTRACTION_MAX_ATTEMPTS", 3)

    with pytest.raises(LLMConfigurationError):
        await invoice_service._with_retry(
            operation_name="test extraction",
            operation=unavailable_operation,
            retryable_exceptions=(AIExtractionError,),
        )

    assert attempts == 1
