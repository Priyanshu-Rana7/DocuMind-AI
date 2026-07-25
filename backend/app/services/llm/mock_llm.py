import asyncio
import re
from app.services.llm.base import BaseLLMProvider
from app.schemas.invoice import ExtractedInvoiceData, InvoiceItemSchema


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider returning parsed invoice JSON structure for offline testing."""

    async def extract_structured_invoice(self, raw_ocr_text: str) -> ExtractedInvoiceData:
        await asyncio.sleep(0.05)  # Simulate small API delay

        # Basic text parsing logic for realistic mock values if present in text
        inv_num_match = re.search(r"INVOICE\s*#?\s*([A-Za-z0-9\-]+)", raw_ocr_text, re.IGNORECASE)
        inv_num = inv_num_match.group(1) if inv_num_match else "INV-2026-0892"

        return ExtractedInvoiceData(
            invoice_number=inv_num,
            vendor_name="Acme Cloud Tech Inc.",
            vendor_address="100 Innovation Way, San Francisco, CA 94105",
            customer_name="Global Enterprises LLC",
            invoice_date="2026-07-15",
            due_date="2026-08-15",
            currency="USD",
            subtotal=1500.00,
            tax=120.00,
            discount=0.0,
            total=1620.00,
            payment_terms="Net 30",
            invoice_items=[
                InvoiceItemSchema(
                    description="Enterprise Cloud Subscription",
                    quantity=1.0,
                    unit_price=1200.00,
                    total=1200.00,
                ),
                InvoiceItemSchema(
                    description="Premium Support Addon",
                    quantity=2.0,
                    unit_price=150.00,
                    total=300.00,
                ),
            ],
            confidence_score=0.96,
        )
