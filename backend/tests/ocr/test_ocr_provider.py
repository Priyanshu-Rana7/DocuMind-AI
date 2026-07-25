import pytest
from app.schemas.ocr import OCRResult


def test_ocr_result_schema_validation():
    res = OCRResult(
        raw_text="INVOICE #001 VENDOR ACME",
        pages=1,
        detected_language="en",
        confidence=0.98,
    )
    assert res.raw_text == "INVOICE #001 VENDOR ACME"
    assert res.confidence == 0.98
