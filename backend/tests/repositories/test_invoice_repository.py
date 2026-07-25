import pytest
from app.models.invoice import Invoice, InvoiceStatus


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
