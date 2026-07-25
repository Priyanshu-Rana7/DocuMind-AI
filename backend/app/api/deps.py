from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.repositories.invoice_repository import InvoiceRepository
from app.services.storage.base import BaseStorageProvider
from app.services.ocr.base import BaseOCRProvider
from app.services.llm.base import BaseLLMProvider
from app.services.invoice_service import InvoiceService


def get_storage_provider() -> BaseStorageProvider:
    """Factory dependency injecting configured Storage Provider."""
    if settings.STORAGE_PROVIDER == "local":
        from app.services.storage.local_storage import LocalStorageProvider
        return LocalStorageProvider()
    else:
        raise NotImplementedError(f"Storage provider '{settings.STORAGE_PROVIDER}' is not implemented.")


def get_ocr_provider() -> BaseOCRProvider:
    """Factory dependency injecting configured OCR Provider."""
    if settings.OCR_PROVIDER == "easyocr":
        try:
            from app.services.ocr.easy_ocr import EasyOCRProvider
            return EasyOCRProvider()
        except (ImportError, Exception) as e:
            from app.services.ocr.mock_ocr import MockOCRProvider
            from app.core.logging import logger
            logger.warning(
                f"EasyOCR import/init failed ({str(e)}). Using MockOCRProvider fallback."
            )
            return MockOCRProvider()
    elif settings.OCR_PROVIDER == "mock":
        from app.services.ocr.mock_ocr import MockOCRProvider
        return MockOCRProvider()
    else:
        raise NotImplementedError(f"OCR provider '{settings.OCR_PROVIDER}' is not implemented.")


def get_llm_provider() -> BaseLLMProvider:
    """Factory dependency injecting configured LLM Provider."""
    if settings.LLM_PROVIDER in ["openrouter", "openai"]:
        from app.services.llm.openrouter import OpenRouterLLMProvider
        return OpenRouterLLMProvider()
    elif settings.LLM_PROVIDER == "mock":
        from app.services.llm.mock_llm import MockLLMProvider
        return MockLLMProvider()
    else:
        raise NotImplementedError(f"LLM provider '{settings.LLM_PROVIDER}' is not implemented.")


def get_invoice_repository(db: Session = Depends(get_db)) -> InvoiceRepository:
    """Injects InvoiceRepository with DB session."""
    return InvoiceRepository(db)


def get_invoice_service(
    repo: InvoiceRepository = Depends(get_invoice_repository),
    storage: BaseStorageProvider = Depends(get_storage_provider),
    ocr: BaseOCRProvider = Depends(get_ocr_provider),
    llm: BaseLLMProvider = Depends(get_llm_provider),
) -> InvoiceService:
    """Injects InvoiceService with all dependencies."""
    return InvoiceService(
        repository=repo,
        storage_provider=storage,
        ocr_provider=ocr,
        llm_provider=llm,
    )
