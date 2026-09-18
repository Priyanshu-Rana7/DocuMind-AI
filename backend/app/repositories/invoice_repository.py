from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, cast, String
from app.models.invoice import Invoice, InvoiceStatus
from app.core.exceptions import InvoiceNotFoundError
from app.core.logging import logger


class InvoiceRepository:
    """Repository handling all database persistence operations for Invoice entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        status: InvoiceStatus = InvoiceStatus.UPLOADED,
    ) -> Invoice:
        """Creates and persists a new Invoice record."""
        invoice = Invoice(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            status=status,
        )
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        logger.debug(f"Created invoice record ID: {invoice.id}")
        return invoice

    def get_by_id(self, invoice_id: str) -> Invoice:
        """Fetches invoice record by ID or raises InvoiceNotFoundError."""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise InvoiceNotFoundError(invoice_id)
        return invoice

    def list_invoices(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[InvoiceStatus] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Invoice], int]:
        """Returns paginated list of invoices and total count."""
        query = self.db.query(Invoice)
        if status:
            query = query.filter(Invoice.status == status)
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Invoice.filename.ilike(term),
                    Invoice.raw_ocr_text.ilike(term),
                    cast(Invoice.extracted_data, String).ilike(term),
                )
            )

        total = query.count()
        items = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_ocr_data(
        self,
        invoice_id: str,
        raw_ocr_text: str,
        ocr_metadata: Dict[str, Any],
        status: InvoiceStatus = InvoiceStatus.OCR_COMPLETED,
    ) -> Invoice:
        """Updates invoice record with OCR raw text and metadata."""
        invoice = self.get_by_id(invoice_id)
        invoice.raw_ocr_text = raw_ocr_text
        invoice.ocr_metadata = ocr_metadata
        invoice.status = status
        self.db.commit()
        self.db.refresh(invoice)
        logger.debug(f"Updated OCR data for invoice ID: {invoice.id}")
        return invoice

    def update_extracted_data(
        self,
        invoice_id: str,
        extracted_data: Dict[str, Any],
        overall_confidence: float,
        status: InvoiceStatus = InvoiceStatus.EXTRACTED,
    ) -> Invoice:
        """Updates invoice record with structured AI extracted JSON data."""
        invoice = self.get_by_id(invoice_id)
        invoice.extracted_data = extracted_data
        invoice.overall_confidence = overall_confidence
        invoice.status = status
        self.db.commit()
        self.db.refresh(invoice)
        logger.debug(f"Updated extracted data for invoice ID: {invoice.id}")
        return invoice

    def update_corrected_data(
        self,
        invoice_id: str,
        extracted_data: Dict[str, Any],
    ) -> Invoice:
        """Persists user-corrected structured invoice data."""
        invoice = self.get_by_id(invoice_id)
        invoice.extracted_data = extracted_data
        self.db.commit()
        self.db.refresh(invoice)
        logger.debug(f"Updated corrected data for invoice ID: {invoice.id}")
        return invoice

    def mark_failed(self, invoice_id: str, error_message: str) -> Invoice:
        """Marks invoice status as FAILED with descriptive error message."""
        invoice = self.get_by_id(invoice_id)
        invoice.status = InvoiceStatus.FAILED
        invoice.error_message = error_message
        self.db.commit()
        self.db.refresh(invoice)
        logger.warning(f"Marked invoice ID {invoice_id} as FAILED: {error_message}")
        return invoice

    def delete(self, invoice_id: str) -> None:
        """Deletes an invoice record after its stored file has been removed."""
        invoice = self.get_by_id(invoice_id)
        self.db.delete(invoice)
        self.db.commit()
        logger.info(f"Deleted invoice record ID: {invoice_id}")
