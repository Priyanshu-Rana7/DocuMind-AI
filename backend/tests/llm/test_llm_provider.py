import pytest
from app.schemas.invoice import ExtractedInvoiceData, InvoiceItemSchema


def test_extracted_invoice_schema_validation():
    data = ExtractedInvoiceData(
        invoice_number="INV-2026-001",
        vendor_name="Acme Cloud Solutions",
        total=1250.00,
        currency="USD",
        invoice_items=[
          InvoiceItemSchema(description="Cloud Hosting", quantity=1, unit_price=1250.00, total=1250.00)
        ],
        confidence_score=0.96,
    )
    assert data.invoice_number == "INV-2026-001"
    assert len(data.invoice_items) == 1
    assert data.total == 1250.00
