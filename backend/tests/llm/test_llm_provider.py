import pytest
from app.schemas.invoice import ExtractedInvoiceData, InvoiceItemSchema
from app.services.llm.openrouter import OpenRouterLLMProvider
from app.core.exceptions import (
    AIResponseError,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMTimeoutError,
)


def test_extracted_invoice_schema_validation():
    data = ExtractedInvoiceData(
        invoice_number="INV-2026-001",
        vendor_name="Acme Cloud Solutions",
        customer_address="10 Main Street, London",
        total=1250.00,
        currency="USD",
        invoice_items=[
          InvoiceItemSchema(description="Cloud Hosting", quantity=1, unit_price=1250.00, total=1250.00)
        ],
        confidence_score=0.96,
    )
    assert data.invoice_number == "INV-2026-001"
    assert len(data.invoice_items) == 1
    assert data.total == 1250.00
    assert data.customer_address == "10 Main Street, London"


def test_openrouter_normalizes_missing_amounts_with_warnings():
    normalized = OpenRouterLLMProvider._normalize_nullable_amounts(
        {
            "total": None,
            "invoice_items": [
                {"description": "Service", "quantity": 1, "unit_price": None, "total": None}
            ],
        }
    )

    data = ExtractedInvoiceData(**normalized)

    assert data.total == 0.0
    assert data.invoice_items[0].unit_price == 0.0
    assert data.invoice_items[0].total == 0.0
    assert "Total was not provided by the AI response." in data.validation_warnings


@pytest.mark.asyncio
async def test_openrouter_does_not_fallback_to_mock_without_api_key(monkeypatch):
    monkeypatch.setattr("app.services.llm.openrouter.settings.OPENROUTER_API_KEY", "")
    provider = OpenRouterLLMProvider()

    with pytest.raises(LLMConfigurationError, match="OPENROUTER_API_KEY"):
        await provider.extract_structured_invoice("Invoice total: 100")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception_name", "expected"),
    [
        ("RateLimitError", LLMRateLimitError),
        ("APITimeoutError", LLMTimeoutError),
    ],
)
async def test_openrouter_classifies_provider_failures(monkeypatch, exception_name, expected):
    provider = OpenRouterLLMProvider.__new__(OpenRouterLLMProvider)
    provider.client = type(
        "Client",
        (),
        {
            "chat": type(
                "Chat",
                (),
                {
                    "completions": type(
                        "Completions",
                        (),
                        {
                            "create": staticmethod(
                                lambda **kwargs: (_ for _ in ()).throw(
                                    type(exception_name, (Exception,), {})()
                                )
                            )
                        },
                    )()
                },
            )()
        },
    )()
    provider.model_name = "test-model"

    with pytest.raises(expected):
        await provider.extract_structured_invoice("Invoice total: 100")
