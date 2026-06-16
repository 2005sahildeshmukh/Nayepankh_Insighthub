from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.models.dataset import Dataset
from app.utils.working_dataframe import get_mapped_dataframe, get_working_dataframe
from app.services.data_profiling_service import DataProfilingService
from app.models.workspace import utc_now

router = APIRouter(prefix="/workspaces/{workspace_id}/datasets/{dataset_id}")

def _verify_dataset_readiness(dataset_id: str, workspace_id: str, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Dataset not found in this workspace")
    if dataset.status != "ready":
        raise HTTPException(status_code=409, detail="Dataset mapping is not complete. Please complete mapping first.")
    return dataset

@router.get("/profile")
def get_profile(
    workspace_id: str, 
    dataset_id: str, 
    view: str = Query("mapped", pattern="^(mapped|working)$"),
    db: Session = Depends(get_session)
):
    dataset = _verify_dataset_readiness(dataset_id, workspace_id, db)
    
    if view == "mapped":
        df = get_mapped_dataframe(dataset_id, db)
    else:
        df = get_working_dataframe(dataset_id, db)
        
    profile_data = DataProfilingService.generate_profile(df, dataset, view)
    
    return {
        "generated_at": utc_now().isoformat(),
        "view": view,
        "has_cleaning_plan": dataset.cleaning_plan is not None,
        "dataset": profile_data["dataset"],
        "columns": profile_data["columns"]
    }

@router.get("/quality")
def get_quality_report(
    workspace_id: str, 
    dataset_id: str, 
    view: str = Query("mapped", pattern="^(mapped|working)$"),
    db: Session = Depends(get_session)
):
    dataset = _verify_dataset_readiness(dataset_id, workspace_id, db)
    
    if view == "mapped":
        df = get_mapped_dataframe(dataset_id, db)
    else:
        df = get_working_dataframe(dataset_id, db)
        
    quality_data = DataProfilingService.generate_quality_report(df, dataset, view)
    
    return {
        "generated_at": utc_now().isoformat(),
        "view": view,
        "has_cleaning_plan": dataset.cleaning_plan is not None,
        "summary": quality_data["summary"],
        "issues": quality_data["issues"]
    }
