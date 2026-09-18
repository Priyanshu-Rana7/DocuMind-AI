from io import BytesIO
from zipfile import ZipFile

from app.models.invoice import Invoice, InvoiceStatus
from app.services.export_service import ExportService


def _invoice() -> Invoice:
    return Invoice(
        id="invoice-1",
        filename="Samsung India / August.pdf",
        status=InvoiceStatus.EXTRACTED,
        created_at=None,
        extracted_data={
            "invoice_number": "INV-1",
            "vendor_name": "Samsung",
            "currency": "INR",
            "subtotal": 100,
            "tax": 18,
            "discount": 0,
            "total": 118,
            "invoice_items": [
                {"description": "Display", "quantity": 1, "unit_price": 100, "total": 100}
            ],
        },
        overall_confidence=0.95,
    )


def test_csv_export_is_excel_compatible_and_has_line_items():
    filename, content = ExportService.generate_csv(_invoice())

    assert filename == "Samsung_India_August_export.csv"
    assert content.startswith(b"\xef\xbb\xbf")
    assert b"Line Items" in content
    assert b"Display" in content


def test_excel_export_is_a_valid_workbook():
    filename, content = ExportService.generate_excel(_invoice())

    assert filename == "Samsung_India_August_export.xlsx"
    with ZipFile(BytesIO(content)) as workbook:
        assert "[Content_Types].xml" in workbook.namelist()
        assert "xl/worksheets/sheet1.xml" in workbook.namelist()
