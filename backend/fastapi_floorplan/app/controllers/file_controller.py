# ------------------------------------------------------------------------------
# FileController
#
# Handles reading and writing DXF files to disk.
# Future-ready for replacing with cloud storage operations.
# ------------------------------------------------------------------------------

from pathlib import Path
from fastapi import UploadFile
import uuid

from app.config import UPLOAD_DIR

class FileController:
    @staticmethod
    async def save_upload(file: UploadFile) -> Path:
        """
        Save an uploaded DXF file with a unique name to the upload directory.

        Args:
            file (UploadFile): The uploaded DXF file.

        Returns:
            Path: The full path to the saved file.
        """
        ext = Path(file.filename).suffix
        safe_name = f"{uuid.uuid4().hex}{ext}"
        temp_path = UPLOAD_DIR / safe_name

        content = await file.read()
        temp_path.write_bytes(content)
        return temp_path

    @staticmethod
    def read_file(file_path: Path) -> bytes:
        """
        Read the content of a file from disk.

        Args:
            file_path (Path): The path to the file.

        Returns:
            bytes: The file content.
        """
        return file_path.read_bytes()

    @staticmethod
    def delete_file(file_path: Path):
        """
        Delete a file from disk if it exists.

        Args:
            file_path (Path): The path to the file.
        """
        if file_path.exists():
            file_path.unlink()
