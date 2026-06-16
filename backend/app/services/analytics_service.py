import pandas as pd
import numpy as np
import math
from typing import List, Dict, Any, Tuple

from app.models.dataset import Dataset
from app.models.cleaning_plan import DatasetCleaningPlan
from app.schemas.analytics import (
    AnalyticsFilter, AnalyticsKPI, ChartSpecification,
    Insight, CorrelationResponse, CustomChartRequest, CustomChartResponse
)

from app.services.analytics.roles import AnalyticsRoleService
from app.services.analytics.filter_service import AnalyticsFilterService
from app.services.analytics.chart_service import AnalyticsChartService
from app.services.analytics.correlation_service import AnalyticsCorrelationService
from app.services.analytics.insight_service import AnalyticsInsightService

class AnalyticsService:
    
    @staticmethod
    def _sanitize_for_json(val: Any) -> Any:
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (np.integer, int)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            if math.isnan(val) or math.isinf(val):
                return None
            return float(val)
        if isinstance(val, (np.bool_, bool)):
            return bool(val)
        if isinstance(val, pd.Timestamp):
            return val.isoformat()
        return str(val)

    @classmethod
    def get_analytics_dataframe(
        cls,
        session,
        dataset: Dataset,
        view: str
    ) -> Tuple[pd.DataFrame, bool]:
        from app.utils.working_dataframe import get_mapped_dataframe, get_working_dataframe
        
        if dataset.status != "ready":
            raise ValueError(f"Dataset status is '{dataset.status}', must be 'ready'.")
        
        plan = session.query(DatasetCleaningPlan).filter_by(dataset_id=dataset.id).first()
        has_plan = plan is not None
        
        if view == "working":
            if not has_plan:
                raise ValueError("Cannot request 'working' view when no cleaning plan exists.")
            df = get_working_dataframe(dataset.id, session, plan.configuration)
        else:
            df = get_mapped_dataframe(dataset.id, session)
            
        return df, has_plan

    @classmethod
    def apply_filters(cls, df: pd.DataFrame, filters: List[AnalyticsFilter]) -> pd.DataFrame:
        return AnalyticsFilterService.apply_filters(df, filters)

    @classmethod
    def get_column_roles(cls, session, dataset_id: str) -> Dict[str, Dict[str, Any]]:
        return AnalyticsRoleService.get_column_roles(session, dataset_id)

    @classmethod
    def generate_kpis(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]]) -> List[AnalyticsKPI]:
        kpis = []
        row_count = len(df)
        kpis.append(AnalyticsKPI(
            id="kpi_total_records",
            title="Total Records",
            value=row_count,
            formatted_value=f"{row_count:,}",
            source_column=None,
            aggregation="count",
            description="Total number of rows in the current view."
        ))
        
        measures = [col for col, meta in roles.items() if meta["role"] in ["integer", "float"] and not meta["is_identifier_like"] and col in df.columns]
        categoricals = []
        for c, m in roles.items():
            if c not in df.columns: continue
            if m["is_identifier_like"]: continue
            if m["role"] == "categorical":
                categoricals.append(c)
            elif m["role"] == "text":
                if df[c].nunique(dropna=True) <= 20:
                    name_lower = str(c).lower()
                    if not any(k in name_lower for k in ["note", "comment", "desc", "detail"]):
                        categoricals.append(c)
        
        for m in measures:
            if len(kpis) >= 6: break
            series = pd.to_numeric(df[m], errors='coerce').dropna()
            if len(series) > 0:
                total_val = cls._sanitize_for_json(series.sum())
                if total_val is not None:
                    kpis.append(AnalyticsKPI(
                        id=f"kpi_sum_{m}",
                        title=f"Total {m.replace('_', ' ').title()}",
                        value=total_val,
                        formatted_value=f"{total_val:,.2f}" if isinstance(total_val, float) else f"{total_val:,}",
                        source_column=m,
                        aggregation="sum"
                    ))
        
        if len(kpis) < 4:
            for c in categoricals:
                if len(kpis) >= 6: break
                distinct = int(df[c].nunique(dropna=True))
                kpis.append(AnalyticsKPI(
                    id=f"kpi_distinct_{c}",
                    title=f"Unique {c.replace('_', ' ').title()}",
                    value=distinct,
                    formatted_value=f"{distinct:,}",
                    source_column=c,
                    aggregation="distinct_count"
                ))
                
        return kpis

    @classmethod
    def calculate_correlation(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]]) -> CorrelationResponse:
        return AnalyticsCorrelationService.calculate_correlation(df, roles)

    @classmethod
    def generate_chart_recommendations(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]]) -> List[ChartSpecification]:
        return AnalyticsChartService.generate_chart_recommendations(df, roles)

    @classmethod
    def generate_deterministic_insights(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]], charts: List[ChartSpecification], corr: CorrelationResponse) -> List[Insight]:
        return AnalyticsInsightService.generate_deterministic_insights(df, roles, charts, corr)

    @classmethod
    def generate_custom_chart(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]], req: CustomChartRequest) -> CustomChartResponse:
        return AnalyticsChartService.generate_custom_chart(df, roles, req)
