import asyncio
import os
from typing import List

from PIL import Image

from app.core.config import settings
from app.core.exceptions import OCRConfigurationError, OCRExtractionError
from app.schemas.ocr import OCRPageResult, OCRResult
from app.services.ocr.base import BaseOCRProvider


class TesseractOCRProvider(BaseOCRProvider):
    """Lightweight local OCR provider for constrained deployment environments."""

    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        if not os.path.exists(file_path):
            raise OCRExtractionError(f"OCR file does not exist: '{file_path}'")

        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, self._sync_extract, file_path, mime_type
            )
        except (OCRConfigurationError, OCRExtractionError):
            raise
        except Exception as exc:
            raise OCRExtractionError(f"OCR extraction failed: {exc}") from exc

    def _sync_extract(self, file_path: str, mime_type: str) -> OCRResult:
        try:
            import pytesseract
        except ImportError as exc:
            raise OCRConfigurationError(
                "Tesseract OCR is unavailable. Install pytesseract and the "
                "tesseract-ocr system package."
            ) from exc

        images: List[Image.Image] = []
        if mime_type == "application/pdf" or file_path.lower().endswith(".pdf"):
            try:
                from pdf2image import convert_from_path

                images = convert_from_path(
                    file_path,
                    poppler_path=settings.POPPLER_PATH or None,
                    last_page=settings.MAX_DOCUMENT_PAGES + 1,
                )
            except Exception as exc:
                raise OCRExtractionError(
                    f"PDF page conversion failed: {exc}. "
                    "Install Poppler or set POPPLER_PATH."
                ) from exc
        else:
            try:
                images = [Image.open(file_path)]
            except Exception as exc:
                raise OCRExtractionError(
                    f"Image could not be opened for OCR: {exc}"
                ) from exc

        if not images:
            raise OCRExtractionError("Document contains no readable pages.")
        if len(images) > settings.MAX_DOCUMENT_PAGES:
            for image in images:
                image.close()
            raise OCRExtractionError(
                f"Document exceeds the maximum supported length of "
                f"{settings.MAX_DOCUMENT_PAGES} pages."
            )

        page_results: List[OCRPageResult] = []
        text_blocks: List[str] = []
        confidences: List[float] = []
        try:
            for page_number, image in enumerate(images, start=1):
                data = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT,
                    config="--psm 6",
                )
                words = []
                word_confidences = []
                for text, confidence in zip(data["text"], data["conf"]):
                    text = text.strip()
                    try:
                        confidence_value = float(confidence)
                    except (TypeError, ValueError):
                        confidence_value = -1
                    if text and confidence_value >= 0:
                        words.append(text)
                        word_confidences.append(confidence_value / 100)

                page_text = " ".join(words).strip()
                page_confidence = (
                    round(sum(word_confidences) / len(word_confidences), 4)
                    if word_confidences
                    else 0.0
                )
                page_results.append(
                    OCRPageResult(
                        page_number=page_number,
                        text=page_text,
                        confidence=page_confidence,
                    )
                )
                text_blocks.append(page_text)
                confidences.append(page_confidence)
        finally:
            for image in images:
                image.close()

        combined_text = "\n\n--- Page Break ---\n\n".join(text_blocks).strip()
        if not combined_text:
            raise OCRExtractionError("No readable text was detected in the document.")

        return OCRResult(
            raw_text=combined_text,
            pages=len(page_results),
            detected_language="en",
            confidence=round(sum(confidences) / len(confidences), 4),
            page_details=page_results,
        )
