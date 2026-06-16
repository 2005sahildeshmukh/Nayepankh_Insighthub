import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List
from fastapi import HTTPException
from app.models.dataset import Dataset

class DataProfilingService:
    @staticmethod
    def _safe_json_value(val: Any) -> Any:
        if pd.isna(val):
            return None
        if isinstance(val, (int, float, bool, str)):
            if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                return None
            return val
        if isinstance(val, (np.integer, np.floating, np.bool_)):
            if isinstance(val, np.floating) and (np.isnan(val) or np.isinf(val)):
                return None
            return val.item()
        return str(val)

    @staticmethod
    def generate_profile(df: pd.DataFrame, dataset: Dataset, view: str) -> Dict[str, Any]:
        """Generates dataset and column profiles."""
        row_count = len(df)
        column_count = len(df.columns)
        total_cells = row_count * column_count
        
        missing_cells = int(df.isna().sum().sum())
        missing_percentage = round((missing_cells / total_cells * 100), 2) if total_cells > 0 else 0
        
        complete_rows = int(df.dropna().shape[0])
        duplicate_rows = int(df.duplicated().sum())
        duplicate_percentage = round((duplicate_rows / row_count * 100), 2) if row_count > 0 else 0
        
        column_profiles = []
        numeric_count = 0
        categorical_count = 0
        datetime_count = 0
        boolean_count = 0

        # Create lookup for mapping status and types from dataset.columns
        col_meta_lookup = {}
        for c in dataset.columns:
            if c.mapping_status != "exclude":
                if c.mapping_status == "mapped" and c.standard_field:
                    final_name = c.standard_field
                elif c.mapping_status == "keep":
                    final_name = c.custom_display_name if c.custom_display_name else c.original_name
                else:
                    final_name = c.original_name
                col_meta_lookup[final_name] = c

        for col in df.columns:
            series = df[col]
            meta = col_meta_lookup.get(col)
            if not meta:
                continue

            prof_type = meta.inferred_type
            
            missing_col = int(series.isna().sum())
            non_null = row_count - missing_col
            unique = int(series.nunique(dropna=True))
            unique_ratio = (unique / non_null) if non_null > 0 else 0

            # Semantic inference refinement
            import re
            if prof_type in ["text", "categorical", "identifier", "integer", "unknown"]:
                is_id_field = meta.standard_field in ['record_id', 'volunteer_id', 'beneficiary_id', 'donor_id', 'campaign_id', 'event_id', 'internship_id']
                
                name_str = (str(meta.original_name) + " " + str(col)).lower()
                has_id_keyword = bool(re.search(r'\b(id|identifier|ref|reference|code)\b', name_str))
                
                is_structured = False
                if prof_type in ["text", "categorical", "identifier"] and non_null > 0:
                    sample_vals = series.dropna().astype(str).head(20)
                    if sample_vals.str.match(r'^[A-Za-z]+[-_]*\d+$').mean() > 0.8:
                        is_structured = True

                if is_id_field:
                    prof_type = "identifier"
                elif has_id_keyword and unique_ratio > 0.5:
                    prof_type = "identifier"
                elif is_structured and unique_ratio > 0.5:
                    prof_type = "identifier"
                elif prof_type == "identifier":
                    if pd.api.types.is_numeric_dtype(series):
                        prof_type = "integer"
                    elif unique_ratio < 0.2 and unique < 50:
                        prof_type = "categorical"
                    else:
                        prof_type = "text"

            if prof_type in ["integer", "float"]:
                numeric_count += 1
            elif prof_type in ["categorical", "text", "identifier"]:
                categorical_count += 1
            elif prof_type == "datetime":
                datetime_count += 1
            elif prof_type == "boolean":
                boolean_count += 1

            profile = {
                "final_name": col,
                "original_name": meta.original_name,
                "mapping_status": meta.mapping_status,
                "standard_field": meta.standard_field,
                "inferred_type": prof_type,
                "dtype": str(series.dtype),
                "row_count": row_count,
                "missing_count": missing_col,
                "missing_percentage": round((missing_col / row_count * 100), 2) if row_count > 0 else 0,
                "non_null_count": non_null,
                "unique_count": unique,
                "unique_percentage": round((unique / non_null * 100), 2) if non_null > 0 else 0,
                "sample_values": [DataProfilingService._safe_json_value(x) for x in series.dropna().head(5).tolist()]
            }

            if prof_type in ["integer", "float"] and pd.api.types.is_numeric_dtype(series):
                desc = series.describe()
                q1 = desc.get("25%")
                q3 = desc.get("75%")
                iqr = q3 - q1 if pd.notnull(q1) and pd.notnull(q3) else 0
                
                zeros = int((series == 0).sum())
                negatives = int((series < 0).sum())
                
                outliers = 0
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outliers = int(((series < lower) | (series > upper)).sum())

                profile.update({
                    "min": DataProfilingService._safe_json_value(desc.get("min")),
                    "max": DataProfilingService._safe_json_value(desc.get("max")),
                    "mean": DataProfilingService._safe_json_value(desc.get("mean")),
                    "median": DataProfilingService._safe_json_value(desc.get("50%")),
                    "std": DataProfilingService._safe_json_value(desc.get("std")),
                    "q1": DataProfilingService._safe_json_value(q1),
                    "q3": DataProfilingService._safe_json_value(q3),
                    "iqr": DataProfilingService._safe_json_value(iqr),
                    "zero_count": zeros,
                    "negative_count": negatives,
                    "outlier_count": outliers,
                    "outlier_percentage": round((outliers / non_null * 100), 2) if non_null > 0 else 0
                })
            elif prof_type in ["categorical", "text", "identifier"]:
                val_counts = series.value_counts(dropna=True).head(5)
                top_values = [{"value": DataProfilingService._safe_json_value(k), "count": int(v)} for k, v in val_counts.items()]
                mode_val = val_counts.index[0] if not val_counts.empty else None
                mode_count = int(val_counts.iloc[0]) if not val_counts.empty else 0
                
                text_len = series.dropna().astype(str).str.len()
                
                profile.update({
                    "top_values": top_values,
                    "most_frequent_value": DataProfilingService._safe_json_value(mode_val),
                    "most_frequent_value_percentage": round((mode_count / non_null * 100), 2) if non_null > 0 else 0,
                    "average_text_length": DataProfilingService._safe_json_value(text_len.mean()) if not text_len.empty else None,
                    "min_text_length": DataProfilingService._safe_json_value(text_len.min()) if not text_len.empty else None,
                    "max_text_length": DataProfilingService._safe_json_value(text_len.max()) if not text_len.empty else None,
                })
                
                if prof_type == "identifier":
                    profile["uniqueness_ratio"] = profile["unique_percentage"] / 100.0
                    profile["duplicate_identifier_count"] = non_null - unique

            elif prof_type == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(series):
                    series = pd.to_datetime(series, errors='coerce')
                min_dt = series.min()
                max_dt = series.max()
                delta = (max_dt - min_dt).days if pd.notnull(min_dt) and pd.notnull(max_dt) else None
                profile.update({
                    "earliest_date": str(min_dt) if pd.notnull(min_dt) else None,
                    "latest_date": str(max_dt) if pd.notnull(max_dt) else None,
                    "date_range_days": delta
                })
            elif prof_type == "boolean":
                profile.update({
                    "true_count": int((series == True).sum()),
                    "false_count": int((series == False).sum())
                })

            column_profiles.append(profile)

        return {
            "dataset": {
                "row_count": row_count,
                "column_count": column_count,
                "total_cells": total_cells,
                "missing_cells": missing_cells,
                "missing_percentage": missing_percentage,
                "complete_rows": complete_rows,
                "complete_rows_percentage": round((complete_rows / row_count * 100), 2) if row_count > 0 else 0,
                "exact_duplicate_rows": duplicate_rows,
                "duplicate_percentage": duplicate_percentage,
                "numeric_columns": numeric_count,
                "categorical_text_columns": categorical_count,
                "datetime_columns": datetime_count,
                "boolean_columns": boolean_count
            },
            "columns": column_profiles
        }

    @staticmethod
    def generate_quality_report(df: pd.DataFrame, dataset: Dataset, view: str) -> Dict[str, Any]:
        """Generates quality issues list deterministically."""
        issues = []
        row_count = len(df)
        
        # 1. Dataset-level issues
        duplicate_rows = int(df.duplicated().sum())
        if duplicate_rows > 0:
            issues.append({
                "code": "EXACT_DUPLICATE_ROWS",
                "severity": "critical",
                "column": None,
                "title": "Exact Duplicate Rows",
                "explanation": f"Found {duplicate_rows} rows that are exact duplicates of other rows.",
                "affected_count": duplicate_rows,
                "affected_percentage": round((duplicate_rows / row_count * 100), 2) if row_count > 0 else 0,
                "suggested_action": "Remove exact duplicates via Cleaning config."
            })
            
        missing_rows = int(df.isna().any(axis=1).sum())
        if missing_rows > 0:
            issues.append({
                "code": "ROWS_WITH_MISSING",
                "severity": "warning",
                "column": None,
                "title": "Rows with Missing Data",
                "explanation": f"Found {missing_rows} rows containing at least one missing value.",
                "affected_count": missing_rows,
                "affected_percentage": round((missing_rows / row_count * 100), 2) if row_count > 0 else 0,
                "suggested_action": "Apply missing-value strategies per column."
            })

        # Create lookup
        col_meta_lookup = {}
        for c in dataset.columns:
            if c.mapping_status != "exclude":
                if c.mapping_status == "mapped" and c.standard_field:
                    final_name = c.standard_field
                elif c.mapping_status == "keep":
                    final_name = c.custom_display_name if c.custom_display_name else c.original_name
                else:
                    final_name = c.original_name
                col_meta_lookup[final_name] = c

        # 2. Column-level issues
        for col in df.columns:
            series = df[col]
            meta = col_meta_lookup.get(col)
            if not meta: continue
            
            missing_count = int(series.isna().sum())
            non_null = row_count - missing_count
            unique = int(series.nunique(dropna=True))
            
            # Missingness
            if missing_count > 0:
                pct = round((missing_count / row_count * 100), 2)
                sev = "critical" if pct > 50 else "warning"
                issues.append({
                    "code": "HIGH_MISSINGNESS" if pct > 50 else "MISSING_VALUES",
                    "severity": sev,
                    "column": col,
                    "title": "High Missingness" if pct > 50 else "Missing Values",
                    "explanation": f"Column '{col}' is missing {pct}% of its data.",
                    "affected_count": missing_count,
                    "affected_percentage": pct,
                    "suggested_action": "Drop column, drop rows, or impute missing values."
                })
                
            if missing_count == row_count and row_count > 0:
                issues.append({
                    "code": "EMPTY_COLUMN",
                    "severity": "critical",
                    "column": col,
                    "title": "Empty Column",
                    "explanation": f"Column '{col}' contains entirely null values.",
                    "affected_count": row_count,
                    "affected_percentage": 100,
                    "suggested_action": "Exclude column or fill with constant."
                })
                continue # Skip other checks if empty

            # Constant column
            if unique == 1 and non_null > 0:
                issues.append({
                    "code": "CONSTANT_COLUMN",
                    "severity": "info",
                    "column": col,
                    "title": "Constant Column",
                    "explanation": f"Column '{col}' has only one unique value: {series.dropna().iloc[0]}.",
                    "affected_count": non_null,
                    "affected_percentage": round((non_null / row_count * 100), 2),
                    "suggested_action": "Consider excluding this column as it provides no variance."
                })

            # Formatting (whitespace)
            if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
                str_series = series.dropna().astype(str)
                ws_count = int(str_series.str.contains(r'^\s+|\s+$', regex=True).sum())
                if ws_count > 0:
                    issues.append({
                        "code": "LEADING_TRAILING_WHITESPACE",
                        "severity": "warning",
                        "column": col,
                        "title": "Whitespace Issues",
                        "explanation": f"Found {ws_count} values with leading or trailing whitespace.",
                        "affected_count": ws_count,
                        "affected_percentage": round((ws_count / row_count * 100), 2),
                        "suggested_action": "Trim whitespace via Global Cleaning Rules."
                    })
                    
                empty_str_count = int((str_series.str.strip() == "").sum())
                if empty_str_count > 0:
                    issues.append({
                        "code": "EMPTY_STRINGS",
                        "severity": "warning",
                        "column": col,
                        "title": "Empty Strings",
                        "explanation": f"Found {empty_str_count} empty or whitespace-only strings.",
                        "affected_count": empty_str_count,
                        "affected_percentage": round((empty_str_count / row_count * 100), 2),
                        "suggested_action": "Convert empty strings to null via Global Cleaning Rules."
                    })
                    
                # Case inconsistencies (heuristic: mixed case where not typical, but let's stick to simple checks)
                if meta.standard_field == "email" or meta.inferred_type == "email":
                    email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
                    invalid_emails = int((~str_series.str.match(email_pattern)).sum())
                    print(f"DEBUG: col={col}, inferred_type={meta.inferred_type}, invalid_emails={invalid_emails}")
                    if invalid_emails > 0:
                        issues.append({
                            "code": "INVALID_EMAILS",
                            "severity": "warning",
                            "column": col,
                            "title": "Invalid Emails",
                            "explanation": f"Found {invalid_emails} poorly formatted email addresses.",
                            "affected_count": invalid_emails,
                            "affected_percentage": round((invalid_emails / row_count * 100), 2),
                            "suggested_action": "Review data source."
                        })

            # Numeric issues
            if pd.api.types.is_numeric_dtype(series) and meta.inferred_type in ["integer", "float"]:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1 if pd.notnull(q1) and pd.notnull(q3) else 0
                if iqr > 0:
                    outliers = int(((series < (q1 - 1.5 * iqr)) | (series > (q3 + 1.5 * iqr))).sum())
                    if outliers > 0:
                        issues.append({
                            "code": "IQR_OUTLIERS",
                            "severity": "info",
                            "column": col,
                            "title": "Numeric Outliers",
                            "explanation": f"Found {outliers} values falling outside the 1.5 IQR bounds.",
                            "affected_count": outliers,
                            "affected_percentage": round((outliers / row_count * 100), 2),
                            "suggested_action": "Cap or remove outliers."
                        })

            # Identifier duplicates
            if meta.inferred_type == "identifier":
                dups = non_null - unique
                if dups > 0:
                    issues.append({
                        "code": "DUPLICATE_IDENTIFIERS",
                        "severity": "critical",
                        "column": col,
                        "title": "Duplicate Identifiers",
                        "explanation": f"Column '{col}' is an identifier but contains duplicate values.",
                        "affected_count": dups, # Rough estimate of affected instances
                        "affected_percentage": round((dups / row_count * 100), 2) if row_count > 0 else 0,
                        "suggested_action": "Remove exact duplicates or drop column."
                    })

        critical = sum(1 for i in issues if i["severity"] == "critical")
        warning = sum(1 for i in issues if i["severity"] == "warning")
        info = sum(1 for i in issues if i["severity"] == "info")
        
        missing_cells = int(df.isna().sum().sum())
        column_count = len(dataset.columns)
        total_cells = row_count * column_count if column_count else 0
        return {
            "summary": {
                "completeness_percentage": 100 - (missing_cells / total_cells * 100 if total_cells > 0 else 0),
                "total_issues": len(issues),
                "critical_issues": critical,
                "warning_issues": warning,
                "info_issues": info,
                "duplicate_rows": duplicate_rows
            },
            "issues": issues
        }
