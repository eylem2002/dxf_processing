# ----------------------------------------------------------------------------
# FileController
#
# Responsible for local disk operations on DXF files, with methods for:
#   • Saving uploaded DXF files with unique names
#   • Reading DXF file contents
#   • Deleting DXF files when no longer needed
#
# Designed for easy extension or replacement with cloud storage backends
# (e.g. S3, Azure Blob) by swapping out implementations here.
# ----------------------------------------------------------------------------

from pathlib import Path
import uuid
from fastapi import UploadFile

from app.config import UPLOAD_DIR


class FileController:
    """
    Abstracts file persistence so that storage backend can be swapped
    without changing business logic. Currently writes to local disk.
    """

    @staticmethod
    async def save_upload(file: UploadFile) -> Path:
        """
        Persist an incoming DXF upload to the configured upload directory.

        Args:
            file (UploadFile): Incoming file from a FastAPI request.

        Returns:
            Path: Absolute path on local disk where the file is stored.

        Note:
            Filename is randomized via UUID to avoid collisions and
            to prevent exposing original filenames in storage.
        """
        ext = Path(file.filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_path = UPLOAD_DIR / unique_name

        content = await file.read()
        target_path.write_bytes(content)
        return target_path

    @staticmethod
    def read_file(path: Path) -> bytes:
        """
        Read raw bytes from a DXF file on disk.

        Args:
            path (Path): Full path to the file to read.

        Returns:
            bytes: The binary content of the file.
        """
        return path.read_bytes()

    @staticmethod
    def delete_file(path: Path) -> None:
        """
        Remove a file from local storage if it exists.

        Args:
            path (Path): Full path to the file to delete.
        """
        if path.exists():
            path.unlink()

    @staticmethod
    def save_bytes(data: bytes, filename: str) -> Path:
        """
        Save raw bytes (e.g., generated DXF) to disk under a given name.

        Args:
            data (bytes): Binary content to write.
            filename (str): Desired filename (including extension).

        Returns:
            Path: Path to the newly written file.

        Example:
            FileController.save_bytes(dxf_data, "new_plan.dxf")
        """
        target_path = UPLOAD_DIR / filename
        target_path.write_bytes(data)
        return target_path
