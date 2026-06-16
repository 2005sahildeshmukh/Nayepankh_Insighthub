from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.models.dataset import Dataset
from app.models.cleaning_plan import DatasetCleaningPlan
from app.schemas.cleaning import CleaningPreviewRequest, CleaningPreviewResponse, CleaningSaveResponse, CleaningPlanResponse, CleaningConfiguration
from app.utils.working_dataframe import get_mapped_dataframe, get_working_dataframe
from app.services.data_cleaning_service import DataCleaningService
from app.models.workspace import utc_now
import pandas as pd

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

@router.get("/cleaning")
def get_cleaning_plan(workspace_id: str, dataset_id: str, db: Session = Depends(get_session)):
    dataset = _verify_dataset_readiness(dataset_id, workspace_id, db)
    
    plan = dataset.cleaning_plan
    if plan:
        return {
            "has_plan": True,
            "plan": CleaningPlanResponse.model_validate(plan)
        }
    else:
        return {
            "has_plan": False,
            "plan": {
                "configuration": CleaningConfiguration().model_dump()
            }
        }

@router.post("/cleaning/preview", response_model=CleaningPreviewResponse)
def preview_cleaning_plan(
    workspace_id: str, 
    dataset_id: str, 
    request: CleaningPreviewRequest,
    db: Session = Depends(get_session)
):
    dataset = _verify_dataset_readiness(dataset_id, workspace_id, db)
    mapped_df = get_mapped_dataframe(dataset_id, db)
    
    # 1. Validate
    warnings = DataCleaningService.validate_plan(mapped_df, request.configuration)
    
    rows_before = len(mapped_df)
    missing_cells_before = int(mapped_df.isna().sum().sum())
    
    # 2. Apply (in memory only)
    cleaned_df = DataCleaningService.apply_cleaning_plan(mapped_df, request.configuration.model_dump())
    
    rows_after = len(cleaned_df)
    missing_cells_after = int(cleaned_df.isna().sum().sum())
    
    duplicates_removed = 0
    if request.configuration.remove_exact_duplicates:
        duplicates_removed = int(mapped_df.duplicated().sum())
        
    # Estimate outliers affected by comparing IQR caps, rough proxy for now.
    outliers_affected = 0
    for rule in request.configuration.outlier_rules:
        col = rule.column
        if rule.strategy != "keep" and col in mapped_df.columns and pd.api.types.is_numeric_dtype(mapped_df[col]):
            series = mapped_df[col].dropna()
            if len(series) > 1:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - rule.iqr_multiplier * iqr
                    upper = q3 + rule.iqr_multiplier * iqr
                    outliers_affected += int(((series < lower) | (series > upper)).sum())

    # Safely convert to list of dicts for JSON
    preview_df = cleaned_df.head(20).copy()
    import numpy as np
    preview_df = preview_df.replace({np.nan: None, np.inf: None, -np.inf: None})
    
    return CleaningPreviewResponse(
        rows_before=rows_before,
        rows_after=rows_after,
        missing_cells_before=missing_cells_before,
        missing_cells_after=missing_cells_after,
        duplicates_removed=duplicates_removed,
        outliers_affected=outliers_affected,
        warnings=warnings,
        preview_data=preview_df.to_dict(orient="records"),
        columns=list(cleaned_df.columns)
    )

@router.put("/cleaning", response_model=CleaningSaveResponse)
def save_cleaning_plan(
    workspace_id: str, 
    dataset_id: str, 
    request: CleaningPreviewRequest,
    db: Session = Depends(get_session)
):
    dataset = _verify_dataset_readiness(dataset_id, workspace_id, db)
    mapped_df = get_mapped_dataframe(dataset_id, db)
    
    # Validate and apply safely
    DataCleaningService.validate_plan(mapped_df, request.configuration)
    cleaned_df = DataCleaningService.apply_cleaning_plan(mapped_df, request.configuration.model_dump())
    
    rows_after = len(cleaned_df)
    if rows_after == 0:
        raise HTTPException(status_code=400, detail="This cleaning configuration removes all rows. It cannot be saved.")
        
    missing_cells_after = int(cleaned_df.isna().sum().sum())
    
    plan = dataset.cleaning_plan
    if plan:
        plan.configuration = request.configuration.model_dump()
        plan.updated_at = utc_now()
    else:
        plan = DatasetCleaningPlan(
            dataset_id=dataset_id,
            configuration=request.configuration.model_dump()
        )
        db.add(plan)
        
    db.commit()
    db.refresh(plan)
    
    return CleaningSaveResponse(
        plan=CleaningPlanResponse.model_validate(plan),
        rows=rows_after,
        columns=len(cleaned_df.columns),
        missing_cells=missing_cells_after
    )

@router.delete("/cleaning")
def reset_cleaning_plan(workspace_id: str, dataset_id: str, db: Session = Depends(get_session)):
    dataset = _verify_dataset_readiness(dataset_id, workspace_id, db)
    
    if dataset.cleaning_plan:
        db.delete(dataset.cleaning_plan)
        db.commit()
        
    return {"message": "Cleaning plan reset successfully"}

@router.get("/working-preview")
def get_working_preview(
    workspace_id: str, 
    dataset_id: str, 
    offset: int = 0,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_session)
):
    _verify_dataset_readiness(dataset_id, workspace_id, db)
    
    df = get_working_dataframe(dataset_id, db)
    
    page = df.iloc[offset:offset+limit].copy()
    import numpy as np
    page = page.replace({np.nan: None})
    
    return {
        "offset": offset,
        "limit": limit,
        "total_rows": len(df),
        "data": page.to_dict(orient="records"),
        "columns": list(df.columns)
    }
