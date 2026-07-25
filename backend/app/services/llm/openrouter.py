import json
import re
from openai import AsyncOpenAI
from app.services.llm.base import BaseLLMProvider
from app.services.llm.mock_llm import MockLLMProvider
from app.schemas.invoice import ExtractedInvoiceData
from app.core.config import settings
from app.core.prompt_manager import prompt_manager
from app.core.exceptions import AIExtractionError
from app.core.logging import logger


class OpenRouterLLMProvider(BaseLLMProvider):
    """OpenRouter / OpenAI LLM Provider for structured invoice extraction."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model_name = settings.OPENROUTER_MODEL
        self.fallback_mock = MockLLMProvider()

        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        else:
            self.client = None
            logger.warning(
                "OPENROUTER_API_KEY is not configured. OpenRouterLLMProvider will use MockLLMProvider fallback."
            )

    async def extract_structured_invoice(self, raw_ocr_text: str) -> ExtractedInvoiceData:
        if not self.client:
            logger.info("Using MockLLMProvider fallback due to missing API key.")
            return await self.fallback_mock.extract_structured_invoice(raw_ocr_text)

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

            # Validate against Pydantic schema
            extracted_data = ExtractedInvoiceData(**parsed_dict)
            return extracted_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise AIExtractionError(f"LLM returned invalid JSON output: {str(e)}")
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {str(e)}", exc_info=True)
            raise AIExtractionError(f"AI Extraction failed: {str(e)}")

    @staticmethod
    def _clean_json_markdown(content: str) -> str:
        """Strips ```json ... ``` markdown block wrappers if present."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()
