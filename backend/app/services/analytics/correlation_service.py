import pandas as pd
from typing import Dict, Any
from app.schemas.analytics import CorrelationResponse

class AnalyticsCorrelationService:
    @staticmethod
    def _sanitize_for_json(val: Any) -> Any:
        import numpy as np
        import math
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (np.floating, float)):
            if math.isnan(val) or math.isinf(val):
                return None
            return float(val)
        return val

    @classmethod
    def calculate_correlation(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]]) -> CorrelationResponse:
        measures = [c for c, m in roles.items() if m["role"] in ["integer", "float"] and not m["is_identifier_like"] and c in df.columns]
        
        excluded = {}
        valid_measures = []
        
        for m in measures:
            series = pd.to_numeric(df[m], errors='coerce').dropna()
            if len(series) < 2:
                excluded[m] = "Insufficient valid numbers"
            elif series.nunique() <= 1:
                excluded[m] = "Constant value"
            else:
                valid_measures.append(m)
                
        if len(valid_measures) < 2:
            return CorrelationResponse(
                included_columns=[],
                labels=[],
                values=[],
                excluded_columns=excluded,
                limitation_note="At least two numeric measures are required for correlation."
            )
            
        corr_df = df[valid_measures].corr(method='pearson')
        
        matrix_vals = []
        strongest_pos = None
        strongest_neg = None
        max_pos_val = -1.0
        min_neg_val = 1.0
        
        for i, col1 in enumerate(valid_measures):
            row = []
            for j, col2 in enumerate(valid_measures):
                val = corr_df.loc[col1, col2]
                sanitized = cls._sanitize_for_json(val)
                row.append(sanitized)
                
                if i < j and sanitized is not None:
                    if sanitized > max_pos_val:
                        max_pos_val = sanitized
                        strongest_pos = {"cols": [col1, col2], "value": sanitized}
                    if sanitized < min_neg_val:
                        min_neg_val = sanitized
                        strongest_neg = {"cols": [col1, col2], "value": sanitized}
            matrix_vals.append(row)
            
        return CorrelationResponse(
            included_columns=valid_measures,
            labels=valid_measures,
            values=matrix_vals,
            strongest_positive=strongest_pos,
            strongest_negative=strongest_neg,
            excluded_columns=excluded,
            limitation_note="Correlation describes association, not causation."
        )
