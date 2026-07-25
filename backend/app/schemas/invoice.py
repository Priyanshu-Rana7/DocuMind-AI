from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.invoice import InvoiceStatus
from app.schemas.ocr import OCRResult


class InvoiceItemSchema(BaseModel):
    description: str = Field(..., description="Line item description")
    quantity: float = Field(default=1.0, description="Quantity purchased")
    unit_price: float = Field(default=0.0, description="Unit price per item")
    total: float = Field(default=0.0, description="Total amount for this line item")


class ExtractedInvoiceData(BaseModel):
    invoice_number: Optional[str] = Field(default=None, description="Invoice or reference number")
    vendor_name: Optional[str] = Field(default=None, description="Seller or Vendor Company Name")
    vendor_address: Optional[str] = Field(default=None, description="Vendor mailing or business address")
    customer_name: Optional[str] = Field(default=None, description="Buyer or Client Name")
    invoice_date: Optional[str] = Field(default=None, description="Date invoice was issued (YYYY-MM-DD format if possible)")
    due_date: Optional[str] = Field(default=None, description="Invoice payment due date")
    currency: str = Field(default="USD", description="Currency symbol or 3-letter code e.g. USD, EUR, INR")
    subtotal: float = Field(default=0.0, description="Subtotal amount before tax/discount")
    tax: float = Field(default=0.0, description="Tax amount e.g. VAT, GST, Sales Tax")
    discount: float = Field(default=0.0, description="Discount amount")
    total: float = Field(default=0.0, description="Grand total payable amount")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms e.g. Net 30, Due on receipt")
    invoice_items: List[InvoiceItemSchema] = Field(default_factory=list, description="Array of line items")
    confidence_score: float = Field(default=0.9, description="LLM confidence rating from 0.0 to 1.0")


class UploadResponseSchema(BaseModel):
    id: str
    filename: str
    file_size: int
    mime_type: str
    status: InvoiceStatus
    message: str = "File uploaded successfully."


class ExtractRequestSchema(BaseModel):
    invoice_id: str


class InvoiceResponseSchema(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: InvoiceStatus
    error_message: Optional[str] = None
    raw_ocr_text: Optional[str] = None
    ocr_metadata: Optional[Dict[str, Any]] = None
    extracted_data: Optional[ExtractedInvoiceData] = None
    overall_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponseSchema(BaseModel):
    total: int
    items: List[InvoiceResponseSchema]
