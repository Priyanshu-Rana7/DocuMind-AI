import os
import asyncio
from typing import List, Optional
from PIL import Image
from app.services.ocr.base import BaseOCRProvider
from app.schemas.ocr import OCRResult, OCRPageResult
from app.core.config import settings
from app.core.exceptions import OCRExtractionError
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
            _reader_instance = easyocr.Reader(
                settings.OCR_LANGUAGES,
                gpu=settings.OCR_USE_GPU,
                verbose=False,
            )
        except ImportError as e:
            logger.warning(f"EasyOCR or PyTorch is not installed ({str(e)}). EasyOCRProvider will operate in fallback mode.")
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
        except OCRExtractionError:
            raise
        except Exception as e:
            logger.error(f"EasyOCR extraction error on file '{file_path}': {str(e)}", exc_info=True)
            raise OCRExtractionError(f"OCR extraction failed: {str(e)}")

    def _sync_extract(self, file_path: str, mime_type: str) -> OCRResult:
        reader = get_easyocr_reader()
        if reader is None:
            from app.services.ocr.mock_ocr import MockOCRProvider
            import asyncio
            mock_ocr = MockOCRProvider()
            return asyncio.run(mock_ocr.extract_text(file_path, mime_type))
        page_results: List[OCRPageResult] = []
        all_text_blocks: List[str] = []
        confidences: List[float] = []

        if mime_type == "application/pdf" or file_path.lower().endswith(".pdf"):
            # Convert PDF pages to PIL Images
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(file_path)
            except Exception as e:
                logger.warning(f"pdf2image conversion failed for '{file_path}' (poppler missing?): {str(e)}. Falling back to mock text.")
                raise OCRExtractionError(f"PDF page conversion failed: {str(e)}. Ensure poppler is installed.")
            
            for page_num, img in enumerate(images, start=1):
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
        else:
            # Single image file (PNG, JPG, JPEG)
            img = Image.open(file_path)
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
