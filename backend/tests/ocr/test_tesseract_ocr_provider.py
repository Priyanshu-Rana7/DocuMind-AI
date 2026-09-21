from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from app.core.exceptions import OCRExtractionError
from app.services.ocr.tesseract_ocr import TesseractOCRProvider


def test_tesseract_extracts_text_and_confidence(monkeypatch, tmp_path: Path):
    source = tmp_path / "invoice.png"
    Image.new("RGB", (20, 20), "white").save(source)

    fake_tesseract = SimpleNamespace(
        Output=SimpleNamespace(DICT=dict),
        image_to_data=lambda image, output_type, config: {
            "text": ["Invoice", "", "100"],
            "conf": ["90", "-1", "80"],
        },
    )
    monkeypatch.setitem(__import__("sys").modules, "pytesseract", fake_tesseract)

    result = TesseractOCRProvider()._sync_extract(str(source), "image/png")

    assert result.raw_text == "Invoice 100"
    assert result.pages == 1
    assert result.confidence == 0.85


@pytest.mark.asyncio
async def test_tesseract_rejects_missing_file(tmp_path: Path):
    provider = TesseractOCRProvider()

    with pytest.raises(OCRExtractionError, match="does not exist"):
        await provider.extract_text(str(tmp_path / "missing.png"), "image/png")
