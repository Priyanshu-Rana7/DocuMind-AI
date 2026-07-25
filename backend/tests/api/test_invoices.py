import pytest
from io import BytesIO
from app.main import app
from app.api.deps import get_ocr_provider, get_llm_provider
from app.services.ocr.mock_ocr import MockOCRProvider
from app.services.llm.mock_llm import MockLLMProvider

# Override OCR and LLM dependencies for fast, deterministic API tests
app.dependency_overrides[get_ocr_provider] = lambda: MockOCRProvider()
app.dependency_overrides[get_llm_provider] = lambda: MockLLMProvider()


def test_upload_invoice_endpoint(client, sample_pdf_bytes: bytes):
    files = {"file": ("sample.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/invoices/upload", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample.pdf"
    assert data["status"] == "UPLOADED"


def test_extract_invoice_endpoint(client, sample_pdf_bytes: bytes):
    # 1. Upload
    files = {"file": ("sample.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    upload_res = client.post("/api/v1/invoices/upload", files=files)
    invoice_id = upload_res.json()["id"]

    # 2. Extract
    extract_res = client.post(f"/api/v1/invoices/{invoice_id}/extract")
    assert extract_res.status_code == 200
    data = extract_res.json()
    assert data["id"] == invoice_id
    assert data["status"] == "EXTRACTED"
    assert data["extracted_data"]["vendor_name"] == "Acme Cloud Tech Inc."


def test_process_invoice_one_step_endpoint(client, sample_pdf_bytes: bytes):
    files = {"file": ("invoice_direct.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/invoices/process", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "EXTRACTED"
    assert data["extracted_data"]["invoice_number"] is not None


def test_get_invoice_and_list_endpoints(client, sample_pdf_bytes: bytes):
    # Process one invoice
    files = {"file": ("invoice_list.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    proc_res = client.post("/api/v1/invoices/process", files=files)
    inv_id = proc_res.json()["id"]

    # Get single invoice
    get_res = client.get(f"/api/v1/invoices/{inv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == inv_id

    # List invoices
    list_res = client.get("/api/v1/invoices")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert len(list_data["items"]) >= 1
