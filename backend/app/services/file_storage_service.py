import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
MAX_FILE_SIZE = 25 * 1024 * 1024 # 25 MB

class FileStorageService:
    @staticmethod
    def get_workspace_dir(workspace_id: str) -> Path:
        # Prevent path traversal
        clean_id = os.path.basename(workspace_id)
        return UPLOAD_DIR / clean_id

    @staticmethod
    def get_dataset_dir(workspace_id: str, dataset_id: str) -> Path:
        clean_wid = os.path.basename(workspace_id)
        clean_did = os.path.basename(dataset_id)
        return UPLOAD_DIR / clean_wid / clean_did

    @staticmethod
    async def save_upload_file(workspace_id: str, dataset_id: str, file: UploadFile) -> str:
        dataset_dir = FileStorageService.get_dataset_dir(workspace_id, dataset_id)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize original filename
        safe_filename = os.path.basename(file.filename)
        if not safe_filename:
            safe_filename = "unnamed_file"
            
        file_path = dataset_dir / safe_filename
        
        # Stream read to enforce limit
        bytes_read = 0
        try:
            with open(file_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024): # 1MB chunks
                    bytes_read += len(chunk)
                    if bytes_read > MAX_FILE_SIZE:
                        buffer.close()
                        os.remove(file_path)
                        raise HTTPException(status_code=413, detail="File size exceeds the 25MB limit.")
                    buffer.write(chunk)
        except Exception as e:
            if file_path.exists():
                os.remove(file_path)
            raise e
            
        return str(file_path.absolute())

    @staticmethod
    def delete_dataset_directory(workspace_id: str, dataset_id: str):
        dataset_dir = FileStorageService.get_dataset_dir(workspace_id, dataset_id)
        if dataset_dir.exists() and dataset_dir.is_dir():
            shutil.rmtree(dataset_dir)
