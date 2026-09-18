import pytest
from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.invoice_repository import InvoiceRepository


def test_invoice_model_creation(db_session):
    inv = Invoice(
        filename="test_inv.pdf",
        file_path="/uploads/test_inv.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=InvoiceStatus.UPLOADED,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)

    assert inv.id is not None
    assert inv.status == InvoiceStatus.UPLOADED


def test_invoice_search_matches_metadata_and_ocr_text(db_session):
    repository = InvoiceRepository(db_session)
    db_session.add_all(
        [
            Invoice(
                filename="samsung.pdf",
                file_path="/uploads/samsung.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=InvoiceStatus.EXTRACTED,
                raw_ocr_text="GST invoice for Demo Electronics",
                extracted_data={
                    "vendor_name": "SAMSUNG INDIA ELECTRONICS PVT LTD",
                    "invoice_number": "335016033053",
                },
            ),
            Invoice(
                filename="other.pdf",
                file_path="/uploads/other.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=InvoiceStatus.EXTRACTED,
                extracted_data={"vendor_name": "Other Vendor"},
            ),
        ]
    )
    db_session.commit()

    items, total = repository.list_invoices(limit=20, search="335016033053")

    assert total == 1
    assert items[0].filename == "samsung.pdf"
