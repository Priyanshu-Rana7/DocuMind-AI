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


class OCRExtractionError(BaseAppException):
    def __init__(self, detail: str = "Failed to extract text using OCR."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="OCR_EXTRACTION_FAILED",
        )


class AIExtractionError(BaseAppException):
    def __init__(self, detail: str = "Failed to process invoice with AI/LLM."):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="AI_EXTRACTION_FAILED",
        )
