import os
import asyncio
from typing import List, Optional
from PIL import Image
from app.services.ocr.base import BaseOCRProvider
from app.schemas.ocr import OCRResult, OCRPageResult
from app.core.config import settings
from app.core.exceptions import OCRConfigurationError, OCRExtractionError
from app.core.logging import logger

# EasyOCR reader instance singleton cache
_reader_instance = None


def get_easyocr_reader():
    """Lazy loader for EasyOCR reader instance."""
    global _reader_instance
    if _reader_instance is None:
        try:
            import easyocr
            logger.info(f"Initializing EasyOCR reader (languages={settings.OCR_LANGUAGES}, gpu={settings.OCR_USE_GPU})...")
            reader_options = {
                "gpu": settings.OCR_USE_GPU,
                "verbose": False,
            }
            if settings.OCR_MODEL_DIR:
                reader_options["model_storage_directory"] = settings.OCR_MODEL_DIR
            _reader_instance = easyocr.Reader(settings.OCR_LANGUAGES, **reader_options)
        except ImportError as e:
            logger.error(f"EasyOCR or PyTorch is not installed: {str(e)}")
            return None
    return _reader_instance


class EasyOCRProvider(BaseOCRProvider):
    """EasyOCR Implementation for multi-format text recognition."""

    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        if not os.path.exists(file_path):
            raise OCRExtractionError(f"File not found for OCR processing: '{file_path}'")

        try:
            # Run heavy CPU/GPU bound OCR in threadpool to prevent blocking FastAPI main loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, self._sync_extract, file_path, mime_type
            )
            return result
        except (OCRConfigurationError, OCRExtractionError):
            raise
        except Exception as e:
            logger.error(f"EasyOCR extraction error on file '{file_path}': {str(e)}", exc_info=True)
            raise OCRExtractionError(f"OCR extraction failed: {str(e)}")

    def _sync_extract(self, file_path: str, mime_type: str) -> OCRResult:
        reader = get_easyocr_reader()
        if reader is None:
            raise OCRConfigurationError(
                "EasyOCR is unavailable. Install EasyOCR and PyTorch, "
                "or explicitly configure OCR_PROVIDER=mock for development."
            )
        page_results: List[OCRPageResult] = []
        all_text_blocks: List[str] = []
        confidences: List[float] = []

        if mime_type == "application/pdf" or file_path.lower().endswith(".pdf"):
            # Convert PDF pages to PIL Images
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(
                    file_path,
                    poppler_path=settings.POPPLER_PATH or None,
                    last_page=settings.MAX_DOCUMENT_PAGES + 1,
                )
            except Exception as e:
                raise OCRExtractionError(
                    f"PDF page conversion failed: {str(e)}. "
                    "Install Poppler and add its bin directory to PATH, "
                    "or set POPPLER_PATH in the backend .env file."
                )
            if not images:
                raise OCRExtractionError(
                    f"PDF contains no readable pages: '{file_path}'."
                )
            if len(images) > settings.MAX_DOCUMENT_PAGES:
                for image in images:
                    image.close()
                raise OCRExtractionError(
                    f"PDF exceeds the maximum supported length of "
                    f"{settings.MAX_DOCUMENT_PAGES} pages."
                )

            for page_num, img in enumerate(images, start=1):
                try:
                    page_text, page_conf = self._process_image(reader, img)
                    page_results.append(
                        OCRPageResult(
                            page_number=page_num,
                            text=page_text,
                            confidence=page_conf,
                        )
                    )
                    all_text_blocks.append(page_text)
                    confidences.append(page_conf)
                finally:
                    img.close()
        else:
            # Single image file (PNG, JPG, JPEG)
            with Image.open(file_path) as img:
                page_text, page_conf = self._process_image(reader, img)
            page_results.append(
                OCRPageResult(
                    page_number=1,
                    text=page_text,
                    confidence=page_conf,
                )
            )
            all_text_blocks.append(page_text)
            confidences.append(page_conf)

        combined_text = "\n\n--- Page Break ---\n\n".join(all_text_blocks)
        if not combined_text.strip():
            raise OCRExtractionError(
                f"No readable text was detected in '{file_path}'."
            )
        avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0

        return OCRResult(
            raw_text=combined_text.strip(),
            pages=len(page_results),
            detected_language="en",
            confidence=avg_confidence,
            page_details=page_results,
        )

    def _process_image(self, reader, image: Image.Image) -> tuple[str, float]:
        import numpy as np
        img_np = np.array(image.convert("RGB"))
        ocr_out = reader.readtext(img_np)

        lines: List[str] = []
        conf_scores: List[float] = []

        for bbox, text, prob in ocr_out:
            lines.append(text)
            conf_scores.append(float(prob))

        page_text = "\n".join(lines)
        page_conf = round(sum(conf_scores) / len(conf_scores), 4) if conf_scores else 0.0
        return page_text, page_conf
