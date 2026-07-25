from typing import List, Optional
from pydantic import BaseModel, Field


class OCRPageResult(BaseModel):
    page_number: int
    text: str
    confidence: float


class OCRResult(BaseModel):
    raw_text: str = Field(description="Combined text from all pages")
    pages: int = Field(default=1, description="Total pages processed")
    detected_language: str = Field(default="en", description="Primary detected language code")
    confidence: float = Field(description="Average OCR confidence score between 0.0 and 1.0")
    page_details: List[OCRPageResult] = Field(default_factory=list)
