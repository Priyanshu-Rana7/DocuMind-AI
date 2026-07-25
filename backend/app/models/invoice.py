import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, Enum
from app.db.session import Base


class InvoiceStatus(str, PyEnum):
    PENDING = "PENDING"
    UPLOADED = "UPLOADED"
    OCR_COMPLETED = "OCR_COMPLETED"
    EXTRACTED = "EXTRACTED"
    FAILED = "FAILED"


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.UPLOADED, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # OCR output
    raw_ocr_text = Column(Text, nullable=True)
    ocr_metadata = Column(JSON, nullable=True)  # {pages, detected_language, confidence}
    
    # Structured AI output
    extracted_data = Column(JSON, nullable=True)
    overall_confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status.value if isinstance(self.status, InvoiceStatus) else self.status,
            "error_message": self.error_message,
            "raw_ocr_text": self.raw_ocr_text,
            "ocr_metadata": self.ocr_metadata,
            "extracted_data": self.extracted_data,
            "overall_confidence": self.overall_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
