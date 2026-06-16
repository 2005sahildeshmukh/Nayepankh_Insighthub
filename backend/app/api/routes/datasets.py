from typing import List, Any, Dict
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.schemas.dataset import DatasetResponse, DatasetDetailResponse, BulkMappingUpdate
from app.services.dataset_service import DatasetService
from app.services.dataset_inspection_service import DatasetInspectionService
from app.models.dataset import Dataset, DatasetColumn

router = APIRouter(prefix="/workspaces/{workspace_id}/datasets", tags=["Datasets"])

@router.get("", response_model=List[DatasetResponse])
def list_datasets(workspace_id: str, db: Session = Depends(get_session)):
    datasets = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).all()
    return datasets

@router.post("", response_model=DatasetResponse)
async def upload_dataset(workspace_id: str, file: UploadFile = File(...), db: Session = Depends(get_session)):
    return await DatasetService.upload_dataset(db, workspace_id, file)

@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(workspace_id: str, dataset_id: str, db: Session = Depends(get_session)):
    dataset = DatasetService.get_dataset(db, workspace_id, dataset_id)
    return dataset

@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(workspace_id: str, dataset_id: str, db: Session = Depends(get_session)):
    DatasetService.delete_dataset(db, workspace_id, dataset_id)

@router.get("/{dataset_id}/preview", response_model=List[Dict[str, Any]])
def preview_dataset(workspace_id: str, dataset_id: str, limit: int = 20, db: Session = Depends(get_session)):
    dataset = DatasetService.get_dataset(db, workspace_id, dataset_id)
    limit = min(limit, 100) # Cap at 100
    if not dataset.file_path:
        return []
    return DatasetInspectionService.get_preview(dataset.file_path, dataset.file_type, limit)

@router.get("/{dataset_id}/mapping", response_model=DatasetDetailResponse)
def get_mapping(workspace_id: str, dataset_id: str, db: Session = Depends(get_session)):
    # Same as get_dataset but could be extended if needed
    return DatasetService.get_dataset(db, workspace_id, dataset_id)

@router.put("/{dataset_id}/mapping", response_model=DatasetDetailResponse)
def update_mapping(workspace_id: str, dataset_id: str, update_data: BulkMappingUpdate, db: Session = Depends(get_session)):
    dataset = DatasetService.get_dataset(db, workspace_id, dataset_id)
    
    # Create lookup map
    updates = {u.id: u for u in update_data.columns}
    
    final_names = []
    
    for col in dataset.columns:
        if col.id in updates:
            u = updates[col.id]
            col.mapping_status = u.mapping_status
            if u.mapping_status == "mapped":
                col.standard_field = u.standard_field
                col.custom_display_name = None
                if u.standard_field:
                    final_names.append(u.standard_field)
            elif u.mapping_status == "keep":
                col.standard_field = None
                col.custom_display_name = u.custom_display_name
                name = u.custom_display_name if u.custom_display_name else col.original_name
                final_names.append(name)
            else: # exclude
                col.standard_field = None
                col.custom_display_name = None

    # Validate duplicates
    if len(final_names) != len(set(final_names)):
        duplicates = [x for i, x in enumerate(final_names) if final_names.count(x) > 1]
        raise HTTPException(status_code=400, detail=f"Duplicate final output column names detected: {', '.join(set(duplicates))}")

    dataset.status = "ready"
    db.commit()
    db.refresh(dataset)
    return dataset
