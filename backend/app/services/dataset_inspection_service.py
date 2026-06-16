import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple
from fastapi import HTTPException
import json

class DatasetInspectionService:
    @staticmethod
    def inspect_file(file_path: str, file_type: str) -> Tuple[int, int, list[Dict[str, Any]]]:
        """Reads file, returns (row_count, column_count, columns_metadata)"""
        try:
            if file_type == 'csv':
                df = pd.read_csv(file_path, nrows=1000) # Read up to 1000 rows for inspection
            elif file_type == 'xlsx':
                df = pd.read_excel(file_path, nrows=1000)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

        row_count = len(df)
        column_count = len(df.columns)
        columns_metadata = []

        for col_name in df.columns:
            col_series = df[col_name]
            
            # Counts
            missing_count = int(col_series.isna().sum())
            unique_count = int(col_series.nunique(dropna=True))
            
            # Sample values (up to 5 non-null)
            sample_values = col_series.dropna().head(5).tolist()
            # Serialize samples to strings or standard json types safely
            safe_samples = []
            for val in sample_values:
                if pd.isna(val): continue
                if isinstance(val, (int, float, bool, str)):
                    safe_samples.append(val)
                else:
                    safe_samples.append(str(val))

            # Infer type
            inferred_type = DatasetInspectionService._infer_type(col_series)
            
            columns_metadata.append({
                "original_name": str(col_name),
                "inferred_type": inferred_type,
                "nullable": missing_count > 0,
                "unique_count": unique_count,
                "missing_count": missing_count,
                "sample_values": safe_samples
            })
            
        return row_count, column_count, columns_metadata

    @staticmethod
    def _infer_type(series: pd.Series) -> str:
        if len(series.dropna()) == 0:
            return "unknown"
            
        # Boolean
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
            
        # Integer
        if pd.api.types.is_integer_dtype(series):
            return "integer"
            
        # Float
        if pd.api.types.is_float_dtype(series):
            return "float"
            
        # Object / String
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            # Check for boolean-like strings
            val_lower = series.dropna().astype(str).str.lower()
            if set(val_lower).issubset({"true", "false", "yes", "no", "1", "0", "t", "f"}):
                return "boolean"
            
            # Check datetime
            try:
                # Don't parse plain integers as dates
                if not series.astype(str).str.isnumeric().all():
                    parsed_dates = pd.to_datetime(series.dropna(), errors='coerce', format='mixed')
                    if parsed_dates.notna().mean() > 0.8: # If > 80% parseable as dates
                        return "datetime"
            except:
                pass
                
            # Categorical vs Text vs Identifier
            unique_ratio = series.nunique() / len(series.dropna())
            if unique_ratio < 0.2 and series.nunique() < 50:
                return "categorical"
            else:
                return "text"
                
        # Datetime fallback
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
            
        return "unknown"

    @staticmethod
    def get_preview(file_path: str, file_type: str, limit: int = 20) -> list[Dict[str, Any]]:
        try:
            if file_type == 'csv':
                df = pd.read_csv(file_path, nrows=limit)
            elif file_type == 'xlsx':
                df = pd.read_excel(file_path, nrows=limit)
            else:
                return []
            
            # Convert NaNs to None for JSON serialization
            df = df.where(pd.notnull(df), None)
            return df.to_dict(orient="records")
        except:
            return []
