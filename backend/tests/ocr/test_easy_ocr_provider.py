from pathlib import Path

import pytest

from app.core.exceptions import OCRConfigurationError, OCRExtractionError
from app.services.ocr import easy_ocr
from app.services.ocr.easy_ocr import EasyOCRProvider


@pytest.mark.asyncio
async def test_missing_easyocr_does_not_fall_back_to_mock(monkeypatch, tmp_path: Path):
    source = tmp_path / "invoice.png"
    source.write_bytes(b"not an image")
    monkeypatch.setattr(easy_ocr, "get_easyocr_reader", lambda: None)

    with pytest.raises(OCRConfigurationError, match="OCR_PROVIDER=mock"):
        await EasyOCRProvider().extract_text(str(source), "image/png")


def test_empty_pdf_is_rejected(monkeypatch, tmp_path: Path):
    source = tmp_path / "invoice.pdf"
    source.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(easy_ocr, "get_easyocr_reader", lambda: object())
    monkeypatch.setattr(
        "pdf2image.convert_from_path",
        lambda *args, **kwargs: [],
    )

    with pytest.raises(OCRExtractionError, match="no readable pages"):
        EasyOCRProvider()._sync_extract(str(source), "application/pdf")
