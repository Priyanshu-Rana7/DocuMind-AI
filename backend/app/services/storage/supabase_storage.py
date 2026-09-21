import os
import tempfile
import mimetypes
from typing import BinaryIO, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.services.storage.base import BaseStorageProvider


class SupabaseStorageProvider(BaseStorageProvider):
    """Private Supabase Storage implementation for persistent invoice files."""

    def __init__(self) -> None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required "
                "when STORAGE_PROVIDER=supabase."
            )

        from supabase import create_client

        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        self.bucket = client.storage.from_(settings.SUPABASE_STORAGE_BUCKET)

    async def save_file(
        self, file_obj: BinaryIO, filename: str
    ) -> Tuple[str, str, int]:
        content = file_obj.read()
        object_path = filename
        self.bucket.upload(
            object_path,
            content,
            file_options={
                "content-type": mimetypes.guess_type(filename)[0]
                or "application/octet-stream",
                "upsert": "false",
            },
        )
        logger.info(
            "Saved file to Supabase Storage",
            extra={"extra_fields": {"object_path": object_path, "file_size": len(content)}},
        )
        return object_path, object_path, len(content)

    async def get_file_path(self, relative_path: str) -> str:
        content = self.bucket.download(relative_path)
        suffix = os.path.splitext(relative_path)[1].lower()
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix="documind-", suffix=suffix, delete=False
        ) as temporary_file:
            temporary_file.write(content)
            return temporary_file.name

    async def release_file_path(self, file_path: str) -> None:
        if os.path.isfile(file_path):
            os.remove(file_path)

    async def delete_file(self, relative_path: str) -> bool:
        self.bucket.remove([relative_path])
        logger.info(
            "Deleted file from Supabase Storage",
            extra={"extra_fields": {"object_path": relative_path}},
        )
        return True
