import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi import UploadFile

from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.invoice import ExtractedInvoiceData
from app.schemas.ocr import OCRPageResult, OCRResult
from app.services.invoice_service import InvoiceService
from app.services.llm.base import BaseLLMProvider
from app.services.ocr.base import BaseOCRProvider
from app.services.storage.local_storage import LocalStorageProvider


FIXTURES_DIR = Path(__file__).parents[1] / "fixtures" / "invoices"


class ReplayOCRProvider(BaseOCRProvider):
    """Replays OCR captured from a sanitized invoice sample."""

    def __init__(self, fixture: Dict[str, Any]):
        self.fixture = fixture

    async def extract_text(self, file_path: str, mime_type: str) -> OCRResult:
        text = self.fixture["ocr_text"]
        return OCRResult(
            raw_text=text,
            pages=1,
            detected_language="en",
            confidence=0.97,
            page_details=[OCRPageResult(page_number=1, text=text, confidence=0.97)],
        )


class ReplayLLMProvider(BaseLLMProvider):
    """Replays the recorded structured extraction for a fixture."""

    def __init__(self, fixture: Dict[str, Any]):
        self.fixture = fixture

    async def extract_structured_invoice(self, raw_ocr_text: str) -> ExtractedInvoiceData:
        assert raw_ocr_text == self.fixture["ocr_text"]
        return ExtractedInvoiceData.model_validate(self.fixture["expected"])


def load_invoice_fixtures() -> list[Dict[str, Any]]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURES_DIR.glob("*.json"))
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fixture",
    load_invoice_fixtures(),
    ids=lambda fixture: fixture["filename"],
)
async def test_real_invoice_regression_fixture_preserves_extraction(
    db_session, tmp_path, sample_pdf_bytes: bytes, fixture: Dict[str, Any]
):
    service = InvoiceService(
        repository=InvoiceRepository(db_session),
        storage_provider=LocalStorageProvider(upload_dir=str(tmp_path)),
        ocr_provider=ReplayOCRProvider(fixture),
        llm_provider=ReplayLLMProvider(fixture),
    )

    upload = UploadFile(
        filename=fixture["filename"],
        file=BytesIO(sample_pdf_bytes),
        headers={"content-type": "application/pdf"},
    )
    processed = await service.process_invoice(upload)
    expected_data = ExtractedInvoiceData.model_validate(fixture["expected"])

    assert processed.status.value == "EXTRACTED"
    assert processed.raw_ocr_text == fixture["ocr_text"]
    assert processed.extracted_data == {
        **expected_data.model_dump(),
        "validation_warnings": [],
    }
    assert processed.overall_confidence == fixture["expected"]["confidence_score"]
