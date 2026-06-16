import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from app.schemas.cleaning import CleaningConfiguration

class DataCleaningService:
    @staticmethod
    def apply_cleaning_plan(df: pd.DataFrame, config_dict: dict) -> pd.DataFrame:
        """Applies cleaning configuration deterministically to the dataframe."""
        try:
            config = CleaningConfiguration(**config_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid cleaning configuration: {str(e)}")
            
        # Keep a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # 2. Trim whitespace
        if config.trim_whitespace:
            for col in df.columns:
                if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                    try:
                        df[col] = df[col].astype(str).str.strip()
                    except:
                        pass
                        
        # 3. Convert empty strings to null
        if config.convert_empty_strings_to_null:
            df = df.replace(r'^\s*$', np.nan, regex=True)
            
        # 4. Apply text case rules
        for rule in config.case_rules:
            col = rule.column
            if col in df.columns and rule.strategy != "none":
                # Ensure it's text-like before applying string methods
                if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                    if rule.strategy == "lower":
                        df[col] = df[col].str.lower()
                    elif rule.strategy == "upper":
                        df[col] = df[col].str.upper()
                    elif rule.strategy == "title":
                        df[col] = df[col].str.title()
                        
        # 5. Apply missing-value rules
        for rule in config.missing_value_rules:
            col = rule.column
            if col not in df.columns:
                continue
                
            strat = rule.strategy
            if strat == "keep":
                continue
            elif strat == "drop":
                df = df.dropna(subset=[col])
            elif strat == "mean":
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
            elif strat == "median":
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
            elif strat == "zero":
                df[col] = df[col].fillna(0)
            elif strat == "mode":
                modes = df[col].mode()
                if not modes.empty:
                    df[col] = df[col].fillna(modes.iloc[0])
            elif strat == "custom":
                df[col] = df[col].fillna(rule.value)
            elif strat == "unknown_label":
                df[col] = df[col].fillna("Unknown")
            elif strat == "true":
                df[col] = df[col].fillna(True)
            elif strat == "false":
                df[col] = df[col].fillna(False)
            elif strat == "earliest":
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].min())
            elif strat == "latest":
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].max())

        # 6. Remove exact duplicate rows
        if config.remove_exact_duplicates:
            df = df.drop_duplicates()
            
        # 7. Apply outlier rules
        for rule in config.outlier_rules:
            col = rule.column
            if col not in df.columns or rule.strategy == "keep":
                continue
                
            if pd.api.types.is_numeric_dtype(df[col]):
                # Handle outlier math carefully
                # Drop NAs for calculation
                series = df[col].dropna()
                if len(series) < 2:
                    continue # Cannot calculate reliable IQR
                    
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                
                if iqr <= 0:
                    continue # Zero IQR handled safely, no outlier treatment applied
                    
                multiplier = rule.iqr_multiplier
                lower_bound = q1 - (multiplier * iqr)
                upper_bound = q3 + (multiplier * iqr)
                
                if rule.strategy == "cap_iqr":
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                elif rule.strategy == "remove":
                    # Keep NA, keep values within bounds
                    mask = df[col].isna() | ((df[col] >= lower_bound) & (df[col] <= upper_bound))
                    df = df[mask]
                    
        # 8. Reset index
        df = df.reset_index(drop=True)
        
        return df

    @staticmethod
    def validate_plan(df: pd.DataFrame, config: CleaningConfiguration) -> list[str]:
        """Validates configuration against the mapped dataframe, returns warnings."""
        warnings = []
        columns = set(df.columns)
        
        # Check rule column existence
        for rule in config.case_rules:
            if rule.column not in columns:
                raise HTTPException(status_code=400, detail=f"Case rule refers to unknown column: {rule.column}")
            if not (pd.api.types.is_object_dtype(df[rule.column]) or pd.api.types.is_string_dtype(df[rule.column])):
                raise HTTPException(status_code=400, detail=f"Case normalization requested on non-text column: {rule.column}")
                
        for rule in config.outlier_rules:
            if rule.column not in columns:
                raise HTTPException(status_code=400, detail=f"Outlier rule refers to unknown column: {rule.column}")
            if rule.strategy != "keep" and not pd.api.types.is_numeric_dtype(df[rule.column]):
                raise HTTPException(status_code=400, detail=f"Outlier treatment requested on non-numeric column: {rule.column}")
            if rule.iqr_multiplier < 0:
                raise HTTPException(status_code=400, detail=f"Invalid IQR multiplier: {rule.iqr_multiplier}")

        for rule in config.missing_value_rules:
            if rule.column not in columns:
                raise HTTPException(status_code=400, detail=f"Missing value rule refers to unknown column: {rule.column}")
            if rule.strategy in ["mean", "median"] and not pd.api.types.is_numeric_dtype(df[rule.column]):
                raise HTTPException(status_code=400, detail=f"Numeric strategy {rule.strategy} on non-numeric column: {rule.column}")
            if rule.strategy in ["earliest", "latest"] and not pd.api.types.is_datetime64_any_dtype(df[rule.column]):
                raise HTTPException(status_code=400, detail=f"Datetime strategy {rule.strategy} on non-datetime column: {rule.column}")
                
        # Check for duplicate rules
        seen_case = set()
        for r in config.case_rules:
            if r.column in seen_case:
                raise HTTPException(status_code=400, detail=f"Duplicate case rule for column: {r.column}")
            seen_case.add(r.column)
            
        seen_outlier = set()
        for r in config.outlier_rules:
            if r.column in seen_outlier:
                raise HTTPException(status_code=400, detail=f"Duplicate outlier rule for column: {r.column}")
            seen_outlier.add(r.column)
            
        seen_missing = set()
        for r in config.missing_value_rules:
            if r.column in seen_missing:
                raise HTTPException(status_code=400, detail=f"Duplicate missing-value rule for column: {r.column}")
            seen_missing.add(r.column)

        return warnings
