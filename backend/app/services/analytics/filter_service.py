import pandas as pd
from typing import List
from app.schemas.analytics import AnalyticsFilter

class AnalyticsFilterService:
    @staticmethod
    def apply_filters(df: pd.DataFrame, filters: List[AnalyticsFilter]) -> pd.DataFrame:
        filtered_df = df.copy()
        
        for f in filters:
            if f.column not in filtered_df.columns:
                raise ValueError(f"Column '{f.column}' not found in dataframe.")
            
            col_series = filtered_df[f.column]
            op = f.operator
            val = f.value
            
            try:
                if op == "is_missing":
                    filtered_df = filtered_df[col_series.isna()]
                elif op == "is_not_missing":
                    filtered_df = filtered_df[col_series.notna()]
                elif op == "equals":
                    filtered_df = filtered_df[col_series == val]
                elif op == "not_equals":
                    filtered_df = filtered_df[col_series != val]
                elif op == "in":
                    filtered_df = filtered_df[col_series.isin(val)]
                elif op == "gt":
                    filtered_df = filtered_df[pd.to_numeric(col_series, errors='coerce') > float(val)]
                elif op == "gte":
                    filtered_df = filtered_df[pd.to_numeric(col_series, errors='coerce') >= float(val)]
                elif op == "lt":
                    filtered_df = filtered_df[pd.to_numeric(col_series, errors='coerce') < float(val)]
                elif op == "lte":
                    filtered_df = filtered_df[pd.to_numeric(col_series, errors='coerce') <= float(val)]
                elif op == "between":
                    s_num = pd.to_numeric(col_series, errors='coerce')
                    filtered_df = filtered_df[(s_num >= float(val[0])) & (s_num <= float(val[1]))]
                elif op == "on_or_after":
                    s_date = pd.to_datetime(col_series, errors='coerce')
                    filtered_df = filtered_df[s_date >= pd.to_datetime(val)]
                elif op == "on_or_before":
                    s_date = pd.to_datetime(col_series, errors='coerce')
                    filtered_df = filtered_df[s_date <= pd.to_datetime(val)]
                elif op == "contains":
                    filtered_df = filtered_df[col_series.astype(str).str.contains(str(val), case=False, na=False)]
                elif op == "not_contains":
                    filtered_df = filtered_df[~col_series.astype(str).str.contains(str(val), case=False, na=False)]
            except Exception as e:
                raise ValueError(f"Error applying filter {op} on {f.column}: {str(e)}")
                
        return filtered_df
