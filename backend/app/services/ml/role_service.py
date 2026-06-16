import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List, Tuple, Optional
from app.schemas.ml import MLTaskRecommendation, MLFeatureRole, MLTargetStats, MLTargetCandidate

class MLRoleService:
    # ---------------------------------------------------------
    # DOMAIN-AGNOSTIC SEMANTIC TOKENS
    # ---------------------------------------------------------
    CLASS_TOKENS = {
        "status", "state", "class", "label", "category", "type", "outcome",
        "result", "segment", "tier", "band", "grade", "priority", "severity",
        "risk", "approved", "accepted", "rejected", "active", "inactive",
        "completed", "converted", "churned", "retained", "defaulted",
        "fraud", "success", "failure", "response", "decision"
    }

    REGRESSION_TOKENS = {
        "amount", "price", "cost", "revenue", "income", "sales", "spend",
        "balance", "profit", "loss", "hours", "duration", "quantity",
        "volume", "distance", "weight", "height", "temperature", "percentage",
        "percent", "rate", "score", "value", "total", "average", "count"
    }

    IDENTIFIER_TOKENS = {
        "id", "uuid", "guid", "identifier", "key", "reference", "ref",
        "serial", "sequence", "code", "account", "transaction", "invoice",
        "order", "customer", "employee", "volunteer"
    }
    
    CONTACT_TOKENS = {
        "email", "mail", "phone", "mobile", "telephone", "whatsapp", "fax"
    }

    NAME_TOKENS = {
        "name", "first", "last", "person"
    }

    FREE_TEXT_TOKENS = {
        "note", "notes", "comment", "comments", "description", "remarks",
        "feedback", "feedback_text", "message", "narrative", "details", "summary", "observation",
        "reason", "review", "text"
    }


    DATETIME_TOKENS = {
        "date", "time", "joined", "created", "updated", "timestamp", "year", "month", "day"
    }

    @staticmethod
    def _is_datetime_heuristic(series: pd.Series, tokens: set, inferred_type: str) -> bool:
        if pd.api.types.is_datetime64_any_dtype(series.dtype) or inferred_type == "datetime":
            return True
        if tokens.intersection(MLRoleService.DATETIME_TOKENS):
            sample = series.dropna().head(10).astype(str)
            if len(sample) == 0:
                return False
            try:
                parsed = pd.to_datetime(sample, errors='coerce')
                if parsed.notna().sum() >= len(sample) * 0.8:
                    return True
            except:
                pass
        return False

    @staticmethod
    def _normalize_tokens(name: str) -> set:
        """Splits camelCase, snake_case, hyphens, and whitespace into lowercased tokens."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        s3 = re.sub(r'[-_]', ' ', s2)
        s4 = re.sub(r'[^\w\s]', ' ', s3)
        return {t.lower() for t in s4.split() if t.strip()}

    @staticmethod
    def get_target_candidates(df: pd.DataFrame, inferred_types: Dict[str, str]) -> List[MLTargetCandidate]:
        """
        Evaluates every column to determine if it is eligible for classification or regression.
        """
        candidates = []
        row_count = len(df)
        
        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            unique_count = int(series.nunique(dropna=True))
            
            candidate = MLTargetCandidate(
                name=col,
                display_name=col,
                non_null_count=row_count - missing_count,
                missing_count=missing_count,
                unique_count=unique_count,
                is_eligible=True
            )
            
            inferred = inferred_types.get(col, "unknown")
            tokens = MLRoleService._normalize_tokens(col)
            
            valid_series = series.dropna()
            if len(valid_series) == 0:
                candidate.is_eligible = False
                candidate.exclusion_reason = "Target column is entirely empty."
                candidates.append(candidate)
                continue
                
            dtype = valid_series.dtype
            is_numeric = pd.api.types.is_numeric_dtype(dtype)
            is_bool = pd.api.types.is_bool_dtype(dtype)
            is_string = pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype)
            
            avg_length = 0
            if is_string:
                avg_length = valid_series.astype(str).str.len().mean()
                
            # 1. Reject explicit mapped role
            if inferred in ["identifier", "contact"]:
                candidate.is_eligible = False
                candidate.exclusion_reason = f"Explicitly mapped as {inferred}."
                candidates.append(candidate)
                continue
                
            # 2. Reject Datetimes
            is_datetime = MLRoleService._is_datetime_heuristic(valid_series, tokens, inferred)
            if is_datetime:
                candidate.is_eligible = False
                candidate.exclusion_reason = "Raw datetimes are not supported as targets."
                candidates.append(candidate)
                continue
                
            # 3. Reject Constants
            if unique_count <= 1:
                candidate.is_eligible = False
                candidate.exclusion_reason = "Constant column (only 1 unique value)."
                candidates.append(candidate)
                continue
                
            # 4. Reject Free-Text (heuristic)
            if is_string and tokens.intersection(MLRoleService.FREE_TEXT_TOKENS):
                candidate.is_eligible = False
                candidate.exclusion_reason = "Free-text fields are not supported as supervised targets in Phase 4."
                candidates.append(candidate)
                continue

            # 5. Reject Identifiers (heuristic)
            if unique_count == len(valid_series) and len(valid_series) >= 5:
                if tokens.intersection(MLRoleService.IDENTIFIER_TOKENS):
                    candidate.is_eligible = False
                    candidate.exclusion_reason = "Detected as identifier (IDs, codes)."
                    candidates.append(candidate)
                    continue
                
            # 6. Reject Contact / Names
            if tokens.intersection(MLRoleService.CONTACT_TOKENS):
                candidate.is_eligible = False
                candidate.exclusion_reason = "Detected as contact field (email, phone)."
                candidates.append(candidate)
                continue
                
            if is_string and "name" in tokens and unique_count > len(valid_series) * 0.8:
                candidate.is_eligible = False
                candidate.exclusion_reason = "Detected as near-unique name identifier."
                candidates.append(candidate)
                continue

            # Task Inference Logic
            # CLASSIFICATION HEURISTICS
            is_categorical = False
            if is_bool:
                is_categorical = True
            elif is_string:
                if len(valid_series) < 15:
                    is_categorical = True
                else:
                    is_categorical = unique_count <= min(50, len(valid_series) * 0.2)
            elif is_numeric:
                # A numeric target may be classification ONLY when its values genuinely represent a small discrete class set.
                if len(valid_series) >= 30 and unique_count <= min(10, len(valid_series) * 0.1):
                    is_categorical = True
                elif len(valid_series) < 30 and unique_count <= 3:
                    is_categorical = True
            
            # If it has classification tokens and value count supports it, enforce classification even for some numerics
            if tokens.intersection(MLRoleService.CLASS_TOKENS) and unique_count <= 20:
                is_categorical = True
                
            if is_categorical:
                candidate.recommended_task = "classification"
                candidate.reason = "Categorical or low-cardinality discrete field."
                candidates.append(candidate)
                continue
                
            # REGRESSION HEURISTICS
            if is_numeric:
                variance = valid_series.var()
                if variance == 0 or pd.isna(variance):
                    candidate.is_eligible = False
                    candidate.exclusion_reason = "Numeric target has zero variance."
                    candidates.append(candidate)
                    continue
                    
                candidate.recommended_task = "regression"
                candidate.reason = "Numeric field with continuous or high-cardinality values."
                # Allow alternative task if cardinality is somewhat low
                if unique_count <= 50:
                    candidate.alternative_task = "classification"
                candidates.append(candidate)
                continue
                
            # Fallback for high-cardinality strings that aren't text
            if is_string:
                candidate.is_eligible = False
                candidate.exclusion_reason = "Too many unique values to classify safely."
                candidates.append(candidate)
                continue
                
            candidate.is_eligible = False
            candidate.exclusion_reason = "Target type is not supported or cannot be determined."
            candidates.append(candidate)

        return candidates

    @staticmethod
    def get_feature_recommendations(df: pd.DataFrame, target_column: str, inferred_types: Dict[str, str]) -> List[MLFeatureRole]:
        """
        Evaluates input features relative to the selected target.
        Categorizes features into recommended, optional, or excluded.
        """
        features = []
        
        for col in df.columns:
            if col == target_column:
                features.append(MLFeatureRole(
                    name=col,
                    display_name=col,
                    role="target",
                    type=str(df[col].dtype),
                    feature_status="excluded",
                    selected_by_default=False,
                    reason="This is the selected target column and cannot be used as a feature."
                ))
                continue
                
            series = df[col]
            missing_ratio = series.isna().sum() / len(df)
            unique_count = series.nunique(dropna=True)
            dtype = series.dtype
            inferred = inferred_types.get(col, "unknown")
            tokens = MLRoleService._normalize_tokens(col)
            
            valid_series = series.dropna()
            is_numeric = pd.api.types.is_numeric_dtype(dtype)
            is_string = pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype)
            avg_length = valid_series.astype(str).str.len().mean() if is_string else 0

            status = "optional"
            role = "feature"
            reason = "Usable feature."
            selected_by_default = False
            warning = None
            
            is_datetime = MLRoleService._is_datetime_heuristic(valid_series, tokens, inferred)

            # --- EXCLUSION RULES ---
            if is_datetime:
                pass # Skip to recommendation rules so datetime is processed correctly!
            elif inferred in ["identifier", "contact"]:
                status = "excluded"
                reason = f"Explicitly mapped as {inferred}."
            elif missing_ratio > 0.9:
                status = "excluded"
                reason = "Excluded due to >90% missing values."
            elif unique_count <= 1:
                status = "excluded"
                reason = "Excluded due to constant value (zero variance)."
            elif is_string and tokens.intersection(MLRoleService.FREE_TEXT_TOKENS):
                status = "excluded"
                role = "free_text"
                reason = "Free-text fields are not supported as model features in Phase 4."
            elif unique_count == len(valid_series) and len(valid_series) >= 5 and tokens.intersection(MLRoleService.IDENTIFIER_TOKENS):
                status = "excluded"
                reason = "Detected as identifier (IDs, codes)."
            elif tokens.intersection(MLRoleService.CONTACT_TOKENS):
                status = "excluded"
                reason = "Detected as contact field (email, phone)."
            elif is_string and "name" in tokens and unique_count > len(valid_series) * 0.8 and len(valid_series) >= 5:
                status = "excluded"
                reason = "Detected as near-unique name identifier."
            elif is_string and unique_count > min(100, len(valid_series) * 0.9) and len(valid_series) >= 15:
                status = "excluded"
                reason = "Excluded due to high cardinality categorical."
            
            # --- RECOMMENDATION RULES ---
            if status != "excluded":
                if is_datetime:
                    role = "datetime_feature"
                    status = "recommended"
                    selected_by_default = True
                    reason = "Supported datetime feature transformed into calendar components."
                elif is_numeric:
                    status = "recommended"
                    selected_by_default = True
                    reason = "Supported numeric feature."
                elif is_string:
                    if len(valid_series) < 15 or unique_count <= 20:
                        status = "recommended"
                        selected_by_default = True
                        reason = "Low-cardinality categorical feature."
                    else:
                        status = "optional"
                        selected_by_default = False
                        reason = "Moderate-cardinality categorical feature."
                        warning = "May increase encoded feature count."

            features.append(MLFeatureRole(
                name=col,
                display_name=col,
                role=role,
                type=str(dtype),
                feature_status=status,
                selected_by_default=selected_by_default,
                reason=reason,
                warning=warning
            ))
            
        return features

    @staticmethod
    def detect_leakage(df: pd.DataFrame, target_column: str, selected_features: List[str]) -> List[Dict[str, Any]]:
        """
        Scans for data leakage (features that are deterministically identical to or perfectly separate the target).
        """
        leakage_warnings = []
        if target_column not in df.columns:
            return leakage_warnings
            
        target_series = df[target_column]
        is_numeric_target = pd.api.types.is_numeric_dtype(target_series.dtype)
        
        for feature in selected_features:
            if feature not in df.columns:
                continue
            
            feature_series = df[feature]
            
            # Exact match check
            if feature_series.equals(target_series):
                leakage_warnings.append({
                    "feature": feature,
                    "severity": "confirmed",
                    "evidence": "Feature is an exact copy of the target.",
                    "action_taken": "blocked",
                    "explanation": "Using the exact target as a feature guarantees perfect predictions but ruins the model's ability to generalize."
                })
                continue
                
            # Name overlap
            if target_column.lower() in feature.lower() or feature.lower() in target_column.lower():
                leakage_warnings.append({
                    "feature": feature,
                    "severity": "suspected",
                    "evidence": "Feature name strongly overlaps with target name.",
                    "action_taken": "warn",
                    "explanation": "Features with similar names often contain the same underlying information as the target."
                })
                
            # Correlation check for numerics
            if is_numeric_target and pd.api.types.is_numeric_dtype(feature_series.dtype):
                try:
                    corr = target_series.corr(feature_series)
                    if not pd.isna(corr) and abs(corr) > 0.98:
                        leakage_warnings.append({
                            "feature": feature,
                            "severity": "suspected",
                            "evidence": f"Near-perfect linear correlation ({corr:.2f}) with target.",
                            "action_taken": "warn",
                            "explanation": "Extremely high correlation suggests this feature is derived directly from the target."
                        })
                except Exception:
                    pass
                    
        return leakage_warnings

    @staticmethod
    def calculate_target_stats(df: pd.DataFrame, target_column: str) -> MLTargetStats:
        if target_column not in df.columns:
            # Fallback when invalid column is passed
            return MLTargetStats(row_count=len(df), missing_count=0, unique_count=0)
            
        series = df[target_column]
        row_count = len(df)
        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))
        
        stats = MLTargetStats(
            row_count=row_count,
            missing_count=missing_count,
            unique_count=unique_count
        )
        
        valid_series = series.dropna()
        if not valid_series.empty:
            if pd.api.types.is_numeric_dtype(valid_series.dtype):
                stats.min = float(valid_series.min())
                stats.max = float(valid_series.max())
                stats.mean = float(valid_series.mean())
                
            # Class distribution for potential classification tasks
            if unique_count <= 20 or not pd.api.types.is_numeric_dtype(valid_series.dtype):
                dist = valid_series.value_counts()
                stats.class_distribution = {str(k): int(v) for k, v in dist.items()}
                stats.num_classes = len(dist)
                if stats.num_classes > 0:
                    smallest = dist.nsmallest(1)
                    stats.smallest_class_label = str(smallest.index[0])
                    stats.smallest_class_count = int(smallest.iloc[0])

        return stats
