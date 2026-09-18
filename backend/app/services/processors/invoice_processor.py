from app.schemas.invoice import ExtractedInvoiceData
from app.services.llm.base import BaseLLMProvider
from app.services.processors.base import BaseDocumentProcessor
from app.validators.invoice_validator import validate_extracted_invoice


class InvoiceDocumentProcessor(BaseDocumentProcessor):
    """Processes recognized invoice text using the configured LLM provider."""

    document_type = "invoice"

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def extract(self, raw_text: str) -> ExtractedInvoiceData:
        extracted_data = await self.llm_provider.extract_structured_invoice(raw_text)
        extracted_data.validation_warnings = validate_extracted_invoice(extracted_data)
        return extracted_data
