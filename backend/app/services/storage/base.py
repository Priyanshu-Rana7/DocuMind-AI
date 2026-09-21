from abc import ABC, abstractmethod
from typing import BinaryIO, Tuple


class BaseStorageProvider(ABC):
    """Abstract Storage Interface for Local, S3, or Cloud Storage."""

    @abstractmethod
    async def save_file(self, file_obj: BinaryIO, filename: str) -> Tuple[str, str, int]:
        """
        Saves uploaded file binary data to storage target.
        Returns tuple of (relative_file_path, full_stored_path, file_size_in_bytes).
        """
        pass

    @abstractmethod
    async def get_file_path(self, relative_path: str) -> str:
        """Returns the local file path or presigned URL for access."""
        pass

    async def release_file_path(self, file_path: str) -> None:
        """Releases any temporary local materialization created for a remote file."""
        return None

    @abstractmethod
    async def delete_file(self, relative_path: str) -> bool:
        """Deletes file from storage target."""
        pass
