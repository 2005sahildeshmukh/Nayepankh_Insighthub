import pandas as pd
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.dataset import Dataset, DatasetColumn

def _load_raw_df(dataset: Dataset) -> pd.DataFrame:
    try:
        if dataset.file_type == 'csv':
            return pd.read_csv(dataset.file_path)
        elif dataset.file_type == 'xlsx':
            return pd.read_excel(dataset.file_path)
        else:
            raise ValueError(f"Unsupported file format: {dataset.file_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read original dataset: {str(e)}")

def get_original_dataframe(dataset_id: str, db: Session) -> pd.DataFrame:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return _load_raw_df(dataset)

def get_mapped_dataframe(dataset_id: str, db: Session) -> pd.DataFrame:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    df = _load_raw_df(dataset)
    
    # Filter out excluded columns and determine final names
    rename_map = {}
    final_names = []
    
    for col in dataset.columns:
        if col.mapping_status == "exclude":
            continue
            
        original_name = col.original_name
        if original_name not in df.columns:
            continue
            
        if col.mapping_status == "mapped" and col.standard_field:
            final_name = col.standard_field
        elif col.mapping_status == "keep":
            final_name = col.custom_display_name if col.custom_display_name else original_name
        else:
            final_name = original_name
            
        rename_map[original_name] = final_name
        final_names.append(final_name)
        
    # Validate duplicate final names
    if len(final_names) != len(set(final_names)):
        duplicates = [x for i, x in enumerate(final_names) if final_names.count(x) > 1]
        raise HTTPException(
            status_code=400, 
            detail=f"Duplicate final output column names detected: {', '.join(set(duplicates))}. Please correct your column mapping."
        )
        
    # Apply mapping
    df = df[list(rename_map.keys())].copy() # Keep only non-excluded, avoid SettingWithCopyWarning
    df = df.rename(columns=rename_map)
    
    return df

def get_working_dataframe(dataset_id: str, db: Session, optional_configuration: Optional[dict] = None) -> pd.DataFrame:
    """
    Returns the dataframe with both mapping and cleaning applied.
    If optional_configuration is provided, it applies that config (for preview).
    Otherwise, it checks for a saved DatasetCleaningPlan.
    """
    # Start with mapped data
    df = get_mapped_dataframe(dataset_id, db)
    
    config_dict = optional_configuration
    if config_dict is None:
        from app.models.cleaning_plan import DatasetCleaningPlan
        plan = db.query(DatasetCleaningPlan).filter(DatasetCleaningPlan.dataset_id == dataset_id).first()
        if plan:
            config_dict = plan.configuration
    
    if not config_dict:
        return df
        
    # Lazy import to avoid circular dependencies if services use this utility
    from app.services.data_cleaning_service import DataCleaningService
    df = DataCleaningService.apply_cleaning_plan(df, config_dict)
    
    return df
