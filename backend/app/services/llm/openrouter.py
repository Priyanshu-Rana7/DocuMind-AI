import json
import re
from openai import AsyncOpenAI
from pydantic import ValidationError
from app.services.llm.base import BaseLLMProvider
from app.schemas.invoice import ExtractedInvoiceData
from app.core.config import settings
from app.core.prompt_manager import prompt_manager
from app.core.exceptions import (
    AIExtractionError,
    AIResponseError,
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.core.logging import logger


class OpenRouterLLMProvider(BaseLLMProvider):
    """OpenRouter / OpenAI LLM Provider for structured invoice extraction."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model_name = settings.OPENROUTER_MODEL
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        else:
            self.client = None
            logger.warning(
                "OPENROUTER_API_KEY is not configured. OpenRouterLLMProvider is unavailable."
            )

    async def extract_structured_invoice(self, raw_ocr_text: str) -> ExtractedInvoiceData:
        if not self.client:
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY is not configured. "
                "Set a valid API key or use LLM_PROVIDER=mock explicitly for test data."
            )

        prompt = prompt_manager.format_prompt(raw_ocr_text)

        try:
            logger.info(f"Sending prompt to OpenRouter model '{self.model_name}'...")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise Document AI system that extracts structured invoice data and outputs strictly valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            raw_response_content = response.choices[0].message.content or "{}"
            logger.debug(f"Raw OpenRouter LLM Response: {raw_response_content[:300]}...")

            cleaned_json_str = self._clean_json_markdown(raw_response_content)
            parsed_dict = json.loads(cleaned_json_str)
            parsed_dict = self._normalize_nullable_amounts(parsed_dict)

            # Validate against Pydantic schema
            extracted_data = ExtractedInvoiceData(**parsed_dict)
            return extracted_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise AIResponseError(f"LLM returned invalid JSON output: {str(e)}")
        except ValidationError as e:
            logger.error(f"LLM response failed schema validation: {str(e)}")
            raise AIResponseError(f"LLM response failed schema validation: {str(e)}")
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {str(e)}", exc_info=True)
            exception_name = type(e).__name__
            status_code = getattr(e, "status_code", None)
            if exception_name == "APITimeoutError" or isinstance(e, TimeoutError):
                raise LLMTimeoutError(
                    "The AI provider request timed out. Please retry the invoice."
                )
            if exception_name == "RateLimitError" or status_code == 429:
                raise LLMRateLimitError(
                    "The AI provider rate limit was reached. Please wait and retry."
                )
            if status_code is not None and status_code >= 400:
                raise LLMProviderError(
                    f"The AI provider returned HTTP {status_code}. "
                    "Check the configured model and provider settings."
                )
            raise AIExtractionError(f"AI Extraction failed: {str(e)}")

    @staticmethod
    def _normalize_nullable_amounts(payload: dict) -> dict:
        """Convert unreadable numeric fields to explicit zero values with warnings."""
        normalized = dict(payload)
        warnings = list(normalized.get("validation_warnings") or [])

        for field in ("subtotal", "tax", "discount", "total"):
            if normalized.get(field) is None:
                normalized[field] = 0.0
                warnings.append(
                    f"{field.capitalize()} was not provided by the AI response."
                )

        items = normalized.get("invoice_items")
        if isinstance(items, list):
            normalized_items = []
            for item in items:
                if not isinstance(item, dict):
                    normalized_items.append(item)
                    continue
                normalized_item = dict(item)
                for field in ("quantity", "unit_price", "total"):
                    if normalized_item.get(field) is None:
                        normalized_item[field] = 0.0
                        warnings.append(
                            f"Line item {field.replace('_', ' ')} was not provided "
                            "by the AI response."
                        )
                normalized_items.append(normalized_item)
            normalized["invoice_items"] = normalized_items

        if warnings:
            normalized["validation_warnings"] = warnings
        return normalized

    @staticmethod
    def _clean_json_markdown(content: str) -> str:
        """Strips ```json ... ``` markdown block wrappers if present."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()
