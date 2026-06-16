from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.database import get_session
from app.schemas.ml import (
    MLMetadataResponse, MLValidateRequest, MLValidateResponse, 
    MLTrainRequest, MLExperimentResponse, MLPredictRequest,
    MLExperimentSummary
)
from app.services.ml.ml_service import MLService

router = APIRouter()

@router.get("/workspaces/{workspace_id}/datasets/{dataset_id}/ml/metadata", response_model=MLMetadataResponse)
def get_ml_metadata(workspace_id: str, dataset_id: str, view: str = "mapped", db: Session = Depends(get_session)):
    if view == "original":
        raise HTTPException(status_code=422, detail="Original data cannot be used for Machine Learning.")
    try:
        return MLService.get_dataset_metadata(db, workspace_id, dataset_id, view)
    except ValueError as e:
        if "Dataset not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/workspaces/{workspace_id}/datasets/{dataset_id}/ml/validate", response_model=MLValidateResponse)
def validate_ml_config(workspace_id: str, dataset_id: str, req: MLValidateRequest, db: Session = Depends(get_session)):
    if req.view == "original":
        raise HTTPException(status_code=422, detail="Original data cannot be used for Machine Learning.")
    try:
        return MLService.validate_configuration(db, workspace_id, dataset_id, req)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/workspaces/{workspace_id}/datasets/{dataset_id}/ml/train", response_model=MLExperimentResponse)
def train_ml_experiment(workspace_id: str, dataset_id: str, req: MLTrainRequest, db: Session = Depends(get_session)):
    if req.view == "original":
        raise HTTPException(status_code=422, detail="Original data cannot be used for Machine Learning.")
    try:
        return MLService.train_experiment(db, workspace_id, dataset_id, req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/workspaces/{workspace_id}/ml/experiments", response_model=list[MLExperimentSummary])
def list_ml_experiments(workspace_id: str, dataset_id: str = None, task_type: str = None, status: str = None, db: Session = Depends(get_session)):
    try:
        return MLService.list_experiments(db, workspace_id, dataset_id, task_type, status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/workspaces/{workspace_id}/ml/experiments/{experiment_id}", response_model=MLExperimentResponse)
def get_ml_experiment(workspace_id: str, experiment_id: str, db: Session = Depends(get_session)):
    try:
        return MLService.get_experiment(db, workspace_id, experiment_id, include_details=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/workspaces/{workspace_id}/ml/experiments/{experiment_id}")
def delete_ml_experiment(workspace_id: str, experiment_id: str, db: Session = Depends(get_session)):
    try:
        MLService.delete_experiment(db, workspace_id, experiment_id)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/workspaces/{workspace_id}/ml/experiments/{experiment_id}/predict")
def predict_ml(workspace_id: str, experiment_id: str, req: MLPredictRequest, db: Session = Depends(get_session)):
    try:
        res = MLService.predict(db, workspace_id, experiment_id, req.features)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
