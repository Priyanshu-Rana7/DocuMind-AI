import os
import aiofiles
from typing import BinaryIO, Tuple
from app.services.storage.base import BaseStorageProvider
from app.core.config import settings
from app.core.logging import logger


class LocalStorageProvider(BaseStorageProvider):
    """Local file system implementation of storage provider interface."""

    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_file(self, file_obj: BinaryIO, filename: str) -> Tuple[str, str, int]:
        """
        Saves file binary stream to local disk upload directory.
        Returns tuple of (relative_file_path, absolute_file_path, file_size_in_bytes).
        """
        full_path = os.path.join(self.upload_dir, filename)
        
        # Read content and write to target path
        content = file_obj.read()
        file_size = len(content)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        relative_path = os.path.relpath(full_path, start=os.path.dirname(self.upload_dir))
        logger.info(f"Saved file to local storage: '{full_path}' ({file_size} bytes)")
        
        return relative_path, full_path, file_size

    async def get_file_path(self, relative_path: str) -> str:
        """Resolves absolute path for relative storage path."""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.abspath(os.path.join(os.path.dirname(self.upload_dir), relative_path))

    async def delete_file(self, relative_path: str) -> bool:
        """Deletes file from local storage."""
        path = await self.get_file_path(relative_path)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted file from local storage: '{path}'")
            return True
        return False
