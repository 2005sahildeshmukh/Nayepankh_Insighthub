from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
import pandas as pd

from app.core.database import get_session
from app.models.workspace import Workspace
from app.models.dataset import Dataset
from app.schemas.analytics import (
    AnalyticsMetadataResponse, AnalyticsDashboardResponse, CustomChartRequest,
    CustomChartResponse, CorrelationResponse, AnalyticsBaseRequest, AnalyticsOverview
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()

def get_verified_dataset(workspace_id: str, dataset_id: str, db: Session) -> Dataset:
    workspace = db.query(Workspace).filter_by(id=workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    dataset = db.query(Dataset).filter_by(id=dataset_id, workspace_id=workspace_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in this workspace")
        
    if dataset.status != "ready":
        raise HTTPException(status_code=409, detail=f"Dataset is not ready for analytics. Status: {dataset.status}")
        
    return dataset

@router.get("/workspaces/{workspace_id}/datasets/{dataset_id}/analytics/metadata", response_model=AnalyticsMetadataResponse)
def get_analytics_metadata(
    workspace_id: str,
    dataset_id: str,
    view: str = Query("mapped", description="View type: 'mapped' or 'working'"),
    db: Session = Depends(get_session)
):
    dataset = get_verified_dataset(workspace_id, dataset_id, db)
    
    try:
        # Just fetching roles to get metadata
        roles = AnalyticsService.get_column_roles(db, dataset.id)
        columns = []
        for col, meta in roles.items():
            columns.append({
                "name": col,
                "role": meta["role"],
                "inferred_type": meta["inferred_type"],
                "is_identifier_like": meta["is_identifier_like"]
            })
            
        _, has_plan = AnalyticsService.get_analytics_dataframe(db, dataset, "mapped") # we just need to know if it has a plan
        
        return AnalyticsMetadataResponse(columns=columns, has_cleaning_plan=has_plan)
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/workspaces/{workspace_id}/datasets/{dataset_id}/analytics/dashboard", response_model=AnalyticsDashboardResponse)
def get_analytics_dashboard(
    workspace_id: str,
    dataset_id: str,
    request: AnalyticsBaseRequest,
    db: Session = Depends(get_session)
):
    dataset = get_verified_dataset(workspace_id, dataset_id, db)
    
    try:
        df, has_plan = AnalyticsService.get_analytics_dataframe(db, dataset, request.view)
        original_row_count = len(df)
        
        # Apply filters
        try:
            filtered_df = AnalyticsService.apply_filters(df, request.filters)
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=str(ve))
            
        filtered_row_count = len(filtered_df)
        
        roles = AnalyticsService.get_column_roles(db, dataset.id)
        
        # Determine base stats
        num_count = sum(1 for c, m in roles.items() if m["role"] in ["integer", "float"])
        cat_count = sum(1 for c, m in roles.items() if m["role"] in ["categorical", "text"])
        dt_count = sum(1 for c, m in roles.items() if m["role"] == "datetime")
        bool_count = sum(1 for c, m in roles.items() if m["role"] == "boolean")
        missing_cells = int(filtered_df.isna().sum().sum())
        
        date_range = None
        dt_cols = [c for c, m in roles.items() if m["role"] == "datetime" and c in df.columns]
        if dt_cols:
            dt_series = pd.to_datetime(filtered_df[dt_cols[0]], errors='coerce').dropna()
            if not dt_series.empty:
                date_range = {
                    "start": dt_series.min().isoformat(),
                    "end": dt_series.max().isoformat()
                }
        
        overview = AnalyticsOverview(
            dataset_name=dataset.name,
            view=request.view,
            row_count=original_row_count,
            column_count=len(roles),
            numeric_count=num_count,
            text_categorical_count=cat_count,
            datetime_count=dt_count,
            boolean_count=bool_count,
            missing_cells=missing_cells,
            date_range=date_range,
            has_cleaning_plan=has_plan
        )
        
        kpis = AnalyticsService.generate_kpis(filtered_df, roles)
        charts = AnalyticsService.generate_chart_recommendations(filtered_df, roles)
        corr_res = AnalyticsService.calculate_correlation(filtered_df, roles)
        insights = AnalyticsService.generate_deterministic_insights(filtered_df, roles, charts, corr_res)
        
        return AnalyticsDashboardResponse(
            overview=overview,
            filtered_row_count=filtered_row_count,
            kpis=kpis,
            recommended_charts=charts,
            insights=insights,
            correlation_summary=corr_res,
            warnings=[]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/workspaces/{workspace_id}/datasets/{dataset_id}/analytics/custom-chart", response_model=CustomChartResponse)
def get_custom_chart(
    workspace_id: str,
    dataset_id: str,
    request: CustomChartRequest,
    db: Session = Depends(get_session)
):
    dataset = get_verified_dataset(workspace_id, dataset_id, db)
    
    try:
        df, _ = AnalyticsService.get_analytics_dataframe(db, dataset, request.view)
        
        try:
            filtered_df = AnalyticsService.apply_filters(df, request.filters)
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=str(ve))
            
        roles = AnalyticsService.get_column_roles(db, dataset.id)
        chart_res = AnalyticsService.generate_custom_chart(filtered_df, roles, request)
        return chart_res
        
    except ValueError as e:
        # Distinguish between 422 mapping validation and 409 state logic
        if "not found in dataframe" in str(e).lower() or "required" in str(e).lower():
            raise HTTPException(status_code=422, detail=str(e))
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/workspaces/{workspace_id}/datasets/{dataset_id}/analytics/correlation", response_model=CorrelationResponse)
def get_correlation(
    workspace_id: str,
    dataset_id: str,
    request: AnalyticsBaseRequest,
    db: Session = Depends(get_session)
):
    dataset = get_verified_dataset(workspace_id, dataset_id, db)
    
    try:
        df, _ = AnalyticsService.get_analytics_dataframe(db, dataset, request.view)
        
        try:
            filtered_df = AnalyticsService.apply_filters(df, request.filters)
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=str(ve))
            
        roles = AnalyticsService.get_column_roles(db, dataset.id)
        corr_res = AnalyticsService.calculate_correlation(filtered_df, roles)
        return corr_res
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
