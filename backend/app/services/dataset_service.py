import os
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models.dataset import Dataset, DatasetColumn
from app.services.file_storage_service import FileStorageService
from app.services.dataset_inspection_service import DatasetInspectionService
from app.services.column_mapping_service import ColumnMappingService

class DatasetService:
    @staticmethod
    async def upload_dataset(db: Session, workspace_id: str, file: UploadFile) -> Dataset:
        # Validate extension
        filename = file.filename or ""
        ext = filename.split('.')[-1].lower() if '.' in filename else ""
        if ext not in ["csv", "xlsx"]:
            raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported.")
            
        # Create dataset record
        dataset = Dataset(
            workspace_id=workspace_id,
            name=filename,
            original_filename=filename,
            stored_filename="", # will be updated
            file_path="", # will be updated
            file_type=ext,
            file_size_bytes=0,
            row_count=0,
            column_count=0,
            status="uploaded"
        )
        db.add(dataset)
        db.flush() # get ID
        
        try:
            # Save file via storage service
            file_path_str = await FileStorageService.save_upload_file(workspace_id, dataset.id, file)
            
            # Inspect file
            row_count, col_count, cols_meta = DatasetInspectionService.inspect_file(file_path_str, ext)
            
            # Update dataset
            dataset.stored_filename = os.path.basename(file_path_str)
            dataset.file_path = file_path_str
            dataset.file_size_bytes = os.path.getsize(file_path_str)
            dataset.row_count = row_count
            dataset.column_count = col_count
            dataset.status = "mapping_pending"
            
            # Create columns
            position = 0
            for col_meta in cols_meta:
                suggested_status, suggested_field = ColumnMappingService.suggest_mapping(col_meta["original_name"])
                
                db_col = DatasetColumn(
                    dataset_id=dataset.id,
                    original_name=col_meta["original_name"],
                    normalized_name=ColumnMappingService.normalize_column_name(col_meta["original_name"]),
                    position=position,
                    inferred_type=col_meta["inferred_type"],
                    nullable=col_meta["nullable"],
                    unique_count=col_meta["unique_count"],
                    missing_count=col_meta["missing_count"],
                    sample_values=col_meta["sample_values"],
                    mapping_status=suggested_status,
                    standard_field=suggested_field,
                    custom_display_name=col_meta["original_name"] if suggested_status == "keep" else None
                )
                db.add(db_col)
                position += 1
                
            db.commit()
            db.refresh(dataset)
            return dataset
            
        except HTTPException as he:
            db.rollback()
            # Try to save the failed state if we have a dataset ID
            db_err = Session(db.get_bind())
            ds = db_err.query(Dataset).filter(Dataset.id == dataset.id).first()
            if ds:
                ds.status = "failed"
                ds.upload_error = str(he.detail)
                db_err.commit()
            raise he
        except Exception as e:
            db.rollback()
            db_err = Session(db.get_bind())
            ds = db_err.query(Dataset).filter(Dataset.id == dataset.id).first()
            if ds:
                ds.status = "failed"
                ds.upload_error = str(e)
                db_err.commit()
            raise HTTPException(status_code=500, detail=f"Dataset processing failed: {str(e)}")

    @staticmethod
    def get_dataset(db: Session, workspace_id: str, dataset_id: str) -> Dataset:
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id, 
            Dataset.workspace_id == workspace_id
        ).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset

    @staticmethod
    def delete_dataset(db: Session, workspace_id: str, dataset_id: str):
        dataset = DatasetService.get_dataset(db, workspace_id, dataset_id)
        
        # Delete ML artifacts explicitly
        from app.services.ml.ml_service import MLService
        MLService.delete_dataset_models(db, workspace_id, dataset_id)
        
        # Delete files
        FileStorageService.delete_dataset_directory(workspace_id, dataset_id)
        
        # Delete DB records (cascades to columns)
        db.delete(dataset)
        db.commit()
