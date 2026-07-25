import pytest
from io import BytesIO
from fastapi import UploadFile
from app.services.invoice_service import InvoiceService
from app.repositories.invoice_repository import InvoiceRepository
from app.services.storage.local_storage import LocalStorageProvider
from app.services.ocr.mock_ocr import MockOCRProvider
from app.services.llm.mock_llm import MockLLMProvider
from app.models.invoice import InvoiceStatus


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
