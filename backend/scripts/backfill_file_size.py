import os
import sys
from pathlib import Path

# Add backend directory to sys.path to allow imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal
from app.models.dataset import Dataset
from app.services.file_storage_service import FileStorageService

def run_backfill():
    print("Starting backfill for dataset file_size_bytes...")
    db = SessionLocal()
    try:
        datasets = db.query(Dataset).all()
        updated_count = 0
        missing_count = 0
        
        for dataset in datasets:
            if not dataset.file_path:
                print(f"Dataset {dataset.id} ({dataset.name}): No file path recorded.")
                missing_count += 1
                continue
                
            path = Path(dataset.file_path)
            
            # Use FileStorageService to resolve path in case it changed
            if not path.is_absolute():
                # Fallback to reconstructing it
                path = FileStorageService.get_dataset_dir(dataset.workspace_id, dataset.id) / dataset.stored_filename
                
            if path.exists() and path.is_file():
                actual_size = os.path.getsize(path)
                if dataset.file_size_bytes != actual_size:
                    print(f"Dataset {dataset.id} ({dataset.name}): Updating size from {dataset.file_size_bytes} to {actual_size} bytes.")
                    dataset.file_size_bytes = actual_size
                    updated_count += 1
            else:
                print(f"Dataset {dataset.id} ({dataset.name}): File not found at {path}")
                missing_count += 1
                
        db.commit()
        print(f"Backfill complete! Updated {updated_count} datasets. {missing_count} datasets missing files.")
    finally:
        db.close()

if __name__ == "__main__":
    run_backfill()
