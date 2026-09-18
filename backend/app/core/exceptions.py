from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    """Base exception for AI Invoice Reader application."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "INTERNAL_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}


class InvoiceNotFoundError(BaseAppException):
    def __init__(self, invoice_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' was not found.",
            error_code="INVOICE_NOT_FOUND",
        )


class InvalidFileTypeError(BaseAppException):
    def __init__(self, detail: str = "Invalid file type uploaded."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_FILE_TYPE",
        )


class FileTooLargeError(BaseAppException):
    def __init__(self, max_size_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_size_mb} MB.",
            error_code="FILE_TOO_LARGE",
        )


class InvoiceExportError(BaseAppException):
    def __init__(self, detail: str = "Invoice data is not available for export."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="INVOICE_EXPORT_UNAVAILABLE",
        )


class InvoiceCorrectionError(BaseAppException):
    def __init__(self, detail: str = "Invoice extraction cannot be corrected in its current state."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="INVOICE_CORRECTION_UNAVAILABLE",
        )


class OCRExtractionError(BaseAppException):
    def __init__(self, detail: str = "Failed to extract text using OCR."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="OCR_EXTRACTION_FAILED",
        )


class OCRConfigurationError(BaseAppException):
    def __init__(self, detail: str = "The configured OCR provider is not ready."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="OCR_CONFIGURATION_ERROR",
        )


class AIExtractionError(BaseAppException):
    def __init__(self, detail: str = "Failed to process invoice with AI/LLM."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="AI_EXTRACTION_FAILED",
        )


class AIResponseError(AIExtractionError):
    def __init__(self, detail: str = "The AI provider returned an invalid response."):
        super().__init__(detail=detail)
        self.error_code = "AI_RESPONSE_INVALID"
        self.status_code = status.HTTP_502_BAD_GATEWAY


class LLMRateLimitError(AIExtractionError):
    def __init__(self, detail: str = "The AI provider rate limit was reached."):
        super().__init__(detail=detail)
        self.error_code = "LLM_RATE_LIMITED"
        self.status_code = status.HTTP_429_TOO_MANY_REQUESTS


class LLMTimeoutError(AIExtractionError):
    def __init__(self, detail: str = "The AI provider request timed out."):
        super().__init__(detail=detail)
        self.error_code = "LLM_TIMEOUT"
        self.status_code = status.HTTP_504_GATEWAY_TIMEOUT


class LLMProviderError(AIExtractionError):
    def __init__(self, detail: str = "The AI provider returned an error."):
        super().__init__(detail=detail)
        self.error_code = "LLM_PROVIDER_ERROR"
        self.status_code = status.HTTP_502_BAD_GATEWAY


class LLMConfigurationError(BaseAppException):
    def __init__(self, detail: str = "The configured LLM provider is not ready."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="LLM_CONFIGURATION_ERROR",
        )


class RateLimitExceededError(BaseAppException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before trying again.",
            error_code="RATE_LIMIT_EXCEEDED",
            extra={"retry_after_seconds": retry_after},
        )
