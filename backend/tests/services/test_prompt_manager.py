import pytest
from app.core.prompt_manager import PromptManager, PromptNotFoundError


def test_prompt_manager_loads_template():
    pm = PromptManager()
    template = pm.get_prompt_template("invoice_extraction_v1")
    assert "{raw_ocr_text}" in template
    assert "DOCUMENT OCR TEXT" in template


def test_prompt_manager_format_prompt():
    pm = PromptManager()
    formatted = pm.format_prompt(raw_ocr_text="Invoice #12345 Vendor Acme Corp Total $500", version="invoice_extraction_v1")
    assert "Invoice #12345 Vendor Acme Corp Total $500" in formatted


def test_prompt_manager_non_existent_version():
    pm = PromptManager()
    with pytest.raises(PromptNotFoundError):
        pm.get_prompt_template("non_existent_version_v99")
