from abc import ABC, abstractmethod
from app.schemas.ocr import OCRResult


class BaseOCRProvider(ABC):
    """Abstract OCR Provider Interface (EasyOCR, Tesseract, Cloud Vision)."""

    @abstractmethod
    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        """
        Extracts raw text, detected language, and page metadata from document file.
        """
        pass
