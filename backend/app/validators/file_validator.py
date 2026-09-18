import os
import re
import uuid
from typing import Optional, Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import InvalidFileTypeError, FileTooLargeError
from app.core.logging import logger

# Header / Magic bytes for supported invoice formats
MAGIC_BYTES = {
    "pdf": b"%PDF",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
}


class FileValidator:
    """Validates uploaded invoice files for type, size, header magic bytes, and corruption."""

    @staticmethod
    def validate_file_size(file_size: int) -> None:
        if file_size == 0:
            raise InvalidFileTypeError("Uploaded file is empty (0 bytes).")
        
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise FileTooLargeError(settings.MAX_UPLOAD_SIZE_MB)

    @staticmethod
    def validate_extension_and_mime(filename: str, content_type: Optional[str]) -> str:
        ext = os.path.splitext(filename.lower())[1]
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(
                f"File extension '{ext}' is not allowed. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        if content_type and content_type.lower() not in settings.ALLOWED_MIME_TYPES:
            raise InvalidFileTypeError(
                f"MIME type '{content_type}' is not allowed. Supported: {', '.join(settings.ALLOWED_MIME_TYPES)}"
            )

        return ext

    @staticmethod
    def validate_magic_header(file_content: bytes, ext: str) -> None:
        """Inspect file header magic bytes to prevent corrupted or disguised files."""
        if ext == ".pdf":
            if not file_content.startswith(MAGIC_BYTES["pdf"]):
                raise InvalidFileTypeError("File has a .pdf extension but invalid/corrupted PDF header magic bytes.")
        elif ext == ".png":
            if not file_content.startswith(MAGIC_BYTES["png"]):
                raise InvalidFileTypeError("File has a .png extension but invalid/corrupted PNG header magic bytes.")
        elif ext in [".jpg", ".jpeg"]:
            if not file_content.startswith(MAGIC_BYTES["jpeg"]):
                raise InvalidFileTypeError("File has a JPEG extension but invalid/corrupted JPEG header magic bytes.")

    @classmethod
    async def validate_upload(cls, upload_file: UploadFile) -> Tuple[bytes, str, str]:
        """
        Full validation pipeline for UploadFile object.
        Returns tuple of (file_bytes, safe_filename, file_extension).
        """
        filename = upload_file.filename or "uploaded_invoice"
        ext = cls.validate_extension_and_mime(filename, upload_file.content_type)

        # Read file contents into memory
        file_bytes = await upload_file.read()
        await upload_file.seek(0)

        cls.validate_file_size(len(file_bytes))
        cls.validate_magic_header(file_bytes, ext)

        safe_filename = cls.generate_safe_filename(filename)
        logger.info(f"File validation passed for '{safe_filename}' ({len(file_bytes)} bytes)")
        
        return file_bytes, safe_filename, ext

    @staticmethod
    def generate_safe_filename(original_filename: str) -> str:
        """Sanitizes filename and prepends unique UUID token to prevent path traversal & collisions."""
        name, ext = os.path.splitext(original_filename)
        # Sanitize name to keep alphanumeric, hyphens, and underscores
        clean_name = re.sub(r"[^\w\-]", "_", name).strip("_")
        if not clean_name:
            clean_name = "invoice"
        
        unique_prefix = str(uuid.uuid4())[:8]
        return f"{unique_prefix}_{clean_name}{ext.lower()}"
