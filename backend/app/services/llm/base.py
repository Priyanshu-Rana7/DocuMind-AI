from abc import ABC, abstractmethod
from app.schemas.invoice import ExtractedInvoiceData


class BaseLLMProvider(ABC):
    """Abstract LLM Provider Interface for invoice text parsing."""

    @abstractmethod
    async def extract_structured_invoice(self, raw_ocr_text: str) -> ExtractedInvoiceData:
        """
        Parses OCR raw text using LLM into validated structured invoice data.
        """
        pass
