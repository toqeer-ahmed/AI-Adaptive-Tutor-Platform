import os
import uuid
from backend.config import settings

class StorageService:
    @staticmethod
    def get_storage_path(organization_id: uuid.UUID, document_id: uuid.UUID, file_name: str) -> str:
        """
        Generates tenant-isolated object key path.
        """
        clean_name = os.path.basename(file_name)
        return f"{organization_id}/{document_id}/{clean_name}"

    @staticmethod
    async def save_file(storage_path: str, content: bytes) -> str:
        """
        Saves file content to local storage directory / S3.
        """
        base_dir = os.path.abspath("storage_data")
        full_dest = os.path.join(base_dir, storage_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)

        with open(full_dest, "wb") as f:
            f.write(content)

        return full_dest

    @staticmethod
    async def read_file(storage_path: str) -> bytes:
        base_dir = os.path.abspath("storage_data")
        full_dest = os.path.join(base_dir, storage_path.replace("/", os.sep))
        if not os.path.exists(full_dest):
            raise FileNotFoundError(f"Stored document file not found at path: {storage_path}")

        with open(full_dest, "rb") as f:
            return f.read()
