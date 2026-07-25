import os
from typing import Dict
from app.core.config import settings
from app.core.logging import logger


class PromptNotFoundError(Exception):
    """Raised when requested prompt version template file is not found."""
    pass


class PromptManager:
    """Dynamically loads and manages versioned LLM prompt templates."""

    def __init__(self, prompts_dir: str = settings.PROMPTS_DIR):
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, str] = {}

    def get_prompt_template(self, version: str = settings.PROMPT_VERSION) -> str:
        """
        Retrieves template text for requested prompt version.
        Uses in-memory caching to avoid repeated disk reads.
        """
        if version in self._cache and not settings.DEBUG:
            return self._cache[version]

        filename = f"{version}.txt"
        filepath = os.path.join(self.prompts_dir, filename)

        if not os.path.exists(filepath):
            logger.error(f"Prompt template file not found at '{filepath}'")
            raise PromptNotFoundError(
                f"Prompt version template '{version}' not found at path '{filepath}'"
            )

        with open(filepath, "r", encoding="utf-8") as f:
            template_content = f.read()

        self._cache[version] = template_content
        logger.debug(f"Loaded prompt template version '{version}'")
        return template_content

    def format_prompt(
        self, raw_ocr_text: str, version: str = settings.PROMPT_VERSION
    ) -> str:
        """
        Formats raw OCR text into prompt template.
        """
        template = self.get_prompt_template(version)
        return template.replace("{raw_ocr_text}", raw_ocr_text)


# Default singleton instance
prompt_manager = PromptManager()
