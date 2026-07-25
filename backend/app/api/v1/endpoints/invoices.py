from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Query, status
from app.schemas.invoice import (
    InvoiceResponseSchema,
    InvoiceListResponseSchema,
    UploadResponseSchema,
)
from app.models.invoice import InvoiceStatus
from app.services.invoice_service import InvoiceService
from app.api.deps import get_invoice_service

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Invoice File",
    description="Validates and uploads an invoice document (PDF, PNG, JPG, JPEG) to storage.",
)
async def upload_invoice(
    file: UploadFile = File(...),
    service: InvoiceService = Depends(get_invoice_service),
):
    invoice = await service.upload_invoice(file)
    return UploadResponseSchema(
        id=invoice.id,
        filename=invoice.filename,
        file_size=invoice.file_size,
        mime_type=invoice.mime_type,
        status=invoice.status,
        message="Invoice uploaded successfully. Call /extract to process.",
    )


@router.post(
    "/{invoice_id}/extract",
    response_model=InvoiceResponseSchema,
    summary="Extract OCR & AI Data",
    description="Processes uploaded invoice through OCR text recognition and LLM structured extraction.",
)
async def extract_invoice(
    invoice_id: str,
    service: InvoiceService = Depends(get_invoice_service),
):
    invoice = await service.extract_invoice(invoice_id)
    return invoice


@router.post(
    "/process",
    response_model=InvoiceResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Extract Invoice",
    description="One-step upload, OCR text recognition, and AI structured data extraction.",
)
async def process_invoice(
    file: UploadFile = File(...),
    service: InvoiceService = Depends(get_invoice_service),
):
    invoice = await service.process_invoice(file)
    return invoice


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponseSchema,
    summary="Get Invoice Details",
    description="Fetches stored invoice metadata, raw OCR output, and structured extracted JSON data.",
)
def get_invoice(
    invoice_id: str,
    service: InvoiceService = Depends(get_invoice_service),
):
    invoice = service.get_invoice(invoice_id)
    return invoice


@router.get(
    "",
    response_model=InvoiceListResponseSchema,
    summary="List Invoices",
    description="Retrieves a paginated list of processed and pending invoices.",
)
def list_invoices(
    skip: int = Query(0, ge=0, description="Offset pagination index"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items per page"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by invoice status"),
    service: InvoiceService = Depends(get_invoice_service),
):
    items, total = service.list_invoices(skip=skip, limit=limit, status=status)
    return InvoiceListResponseSchema(
        total=total,
        items=[InvoiceResponseSchema.model_validate(item) for item in items],
    )
