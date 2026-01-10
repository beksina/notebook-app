"""File storage service with abstract interface for easy swapping."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import uuid
import os

import aiofiles
from fastapi import UploadFile

from app.core.config import settings


class StorageBackend(ABC):
    """Abstract storage interface for easy swapping to S3 later."""

    @abstractmethod
    async def save(self, file: UploadFile, user_id: str, notebook_id: str) -> str:
        """Save file and return the storage path."""
        pass

    @abstractmethod
    async def get(self, path: str) -> bytes:
        """Retrieve file contents by path."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file by path."""
        pass

    @abstractmethod
    def get_full_path(self, relative_path: str) -> Path:
        """Get full filesystem path for a relative path."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage implementation."""

    def __init__(self, base_dir: Path = settings.UPLOAD_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _generate_path(self, user_id: str, notebook_id: str, filename: str) -> Path:
        """Generate organized storage path: uploads/{user_id}/{notebook_id}/{uuid}_{filename}"""
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        return Path(user_id) / notebook_id / unique_name

    async def save(self, file: UploadFile, user_id: str, notebook_id: str) -> str:
        """Save uploaded file to local filesystem."""
        relative_path = self._generate_path(user_id, notebook_id, file.filename)
        full_path = self.base_dir / relative_path

        # Create directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        content = await file.read()
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        return str(relative_path)

    async def get(self, path: str) -> bytes:
        """Read file contents from local filesystem."""
        full_path = self.base_dir / path
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        """Delete file from local filesystem."""
        full_path = self.base_dir / path
        if full_path.exists():
            os.remove(full_path)
            return True
        return False

    def get_full_path(self, relative_path: str) -> Path:
        """Get absolute path for file."""
        return self.base_dir / relative_path


# Singleton instance - can be swapped for S3Backend later
storage = LocalStorageBackend()
