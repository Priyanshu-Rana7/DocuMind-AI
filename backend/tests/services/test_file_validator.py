import pytest
from io import BytesIO
from fastapi import UploadFile
from app.validators.file_validator import FileValidator
from app.core.exceptions import InvalidFileTypeError, FileTooLargeError


@pytest.mark.asyncio
async def test_file_validator_valid_pdf(sample_pdf_bytes: bytes):
    file_obj = BytesIO(sample_pdf_bytes)
    upload_file = UploadFile(filename="invoice.pdf", file=file_obj, headers={"content-type": "application/pdf"})
    
    file_bytes, safe_filename, ext = await FileValidator.validate_upload(upload_file)
    assert ext == ".pdf"
    assert "invoice.pdf" in safe_filename or "invoice" in safe_filename
    assert file_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_file_validator_invalid_extension():
    file_obj = BytesIO(b"some content")
    upload_file = UploadFile(filename="invoice.exe", file=file_obj, headers={"content-type": "application/octet-stream"})
    
    with pytest.raises(InvalidFileTypeError) as exc:
        await FileValidator.validate_upload(upload_file)
    assert "extension '.exe' is not allowed" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_file_validator_empty_file():
    file_obj = BytesIO(b"")
    upload_file = UploadFile(filename="empty.pdf", file=file_obj, headers={"content-type": "application/pdf"})
    
    with pytest.raises(InvalidFileTypeError) as exc:
        await FileValidator.validate_upload(upload_file)
    assert "empty" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_file_validator_corrupted_header():
    # File named .pdf but contains random non-PDF binary header
    file_obj = BytesIO(b"NOT_A_PDF_HEADER_DATA_STREAM")
    upload_file = UploadFile(filename="corrupted.pdf", file=file_obj, headers={"content-type": "application/pdf"})
    
    with pytest.raises(InvalidFileTypeError) as exc:
        await FileValidator.validate_upload(upload_file)
    assert "invalid/corrupted PDF header" in str(exc.value.detail)
