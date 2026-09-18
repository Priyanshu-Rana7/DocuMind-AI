from abc import ABC, abstractmethod
from typing import Generic, TypeVar


TDocument = TypeVar("TDocument")


class BaseDocumentProcessor(ABC, Generic[TDocument]):
    """Interface for converting recognized document text into domain data."""

    document_type: str

    @abstractmethod
    async def extract(self, raw_text: str) -> TDocument:
        """Extract structured domain data from OCR text."""
        raise NotImplementedError
