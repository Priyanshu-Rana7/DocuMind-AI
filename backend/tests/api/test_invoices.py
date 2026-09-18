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


def test_retry_invoice_endpoint_reprocesses_existing_invoice(client, sample_pdf_bytes: bytes):
    files = {"file": ("sample.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    upload_res = client.post("/api/v1/invoices/upload", files=files)
    invoice_id = upload_res.json()["id"]

    retry_res = client.post(f"/api/v1/invoices/{invoice_id}/retry")

    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "EXTRACTED"


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


def test_list_invoice_endpoint_searches_across_matching_records(client, sample_pdf_bytes: bytes):
    files = {"file": ("samsung.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    process_res = client.post("/api/v1/invoices/process", files=files)
    assert process_res.status_code == 201

    response = client.get("/api/v1/invoices", params={"search": "Acme Cloud Tech"})

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["filename"] == "samsung.pdf"


def test_export_invoice_rejects_unprocessed_invoice(client, sample_pdf_bytes: bytes):
    files = {"file": ("invoice with spaces.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    upload_res = client.post("/api/v1/invoices/upload", files=files)
    invoice_id = upload_res.json()["id"]

    response = client.get(f"/api/v1/invoices/{invoice_id}/export?format=csv")

    assert response.status_code == 409
    assert response.json()["error_code"] == "INVOICE_EXPORT_UNAVAILABLE"


def test_correct_extracted_invoice_data(client, sample_pdf_bytes: bytes):
    files = {"file": ("invoice.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    invoice_id = client.post("/api/v1/invoices/process", files=files).json()["id"]
    invoice = client.get(f"/api/v1/invoices/{invoice_id}").json()
    corrected = invoice["extracted_data"] | {
        "vendor_name": "Corrected Vendor",
        "total": 1620.0,
    }

    response = client.put(
        f"/api/v1/invoices/{invoice_id}/extracted-data",
        json=corrected,
    )

    assert response.status_code == 200
    assert response.json()["extracted_data"]["vendor_name"] == "Corrected Vendor"
    assert response.json()["extracted_data"]["total"] == 1620.0
    assert response.json()["overall_confidence"] == invoice["overall_confidence"]


def test_delete_invoice_removes_record(client, sample_pdf_bytes: bytes):
    files = {"file": ("invoice-to-delete.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
    invoice_id = client.post("/api/v1/invoices/upload", files=files).json()["id"]

    response = client.delete(f"/api/v1/invoices/{invoice_id}")

    assert response.status_code == 204
    assert client.get(f"/api/v1/invoices/{invoice_id}").status_code == 404
