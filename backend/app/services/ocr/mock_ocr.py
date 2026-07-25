import asyncio
from app.services.ocr.base import BaseOCRProvider
from app.schemas.ocr import OCRResult, OCRPageResult


class MockOCRProvider(BaseOCRProvider):
    """Mock OCR Provider returning realistic sample text for fast testing."""

    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        await asyncio.sleep(0.05)  # Simulate small processing delay

        sample_text = """
        INVOICE # INV-2026-0892
        Date: 2026-07-15
        Due Date: 2026-08-15
        
        Vendor: Acme Cloud Tech Inc.
        Address: 100 Innovation Way, San Francisco, CA 94105
        
        Customer: Global Enterprises LLC
        
        Line Items:
        1. Enterprise Cloud Subscription - Qty: 1 - Price: $1,200.00 - Total: $1,200.00
        2. Premium Support Addon - Qty: 2 - Price: $150.00 - Total: $300.00
        
        Subtotal: $1,500.00
        Tax (8%): $120.00
        Total Amount Due: $1,620.00
        Payment Terms: Net 30
        """

        return OCRResult(
            raw_text=sample_text.strip(),
            pages=1,
            detected_language="en",
            confidence=0.97,
            page_details=[
                OCRPageResult(page_number=1, text=sample_text.strip(), confidence=0.97)
            ],
        )
