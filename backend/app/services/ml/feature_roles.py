from dataclasses import dataclass
from typing import Literal, List, Dict, Any
import pandas as pd
import re

ResolvedFeatureRole = Literal[
    "numeric",
    "categorical",
    "boolean",
    "datetime",
    "excluded",
]

@dataclass(frozen=True)
class MLResolvedFeature:
    name: str
    role: ResolvedFeatureRole
    inferred_type: str
    reason: str
    parse_success_ratio: float | None = None

@dataclass(frozen=True)
class MLTrainingResult:
    winner_pipeline: Any
    winner_name: str
    candidate_results: List[Any]
    resolved_features: List[MLResolvedFeature]
    preprocessing_manifest: Dict[str, List[str]]
    metric_direction: str


class MLFeatureRoleResolver:
    DATETIME_TOKENS = {
        "date", "time", "joined", "created", "updated", "timestamp", "year", "month", "day"
    }

    @staticmethod
    def _normalize_tokens(name: str) -> set:
        """Splits camelCase, snake_case, hyphens, and whitespace into lowercased tokens."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        s3 = re.sub(r'[-_]', ' ', s2)
        s4 = re.sub(r'[^\w\s]', ' ', s3)
        return {t.lower() for t in s4.split() if t.strip()}

    @staticmethod
    def resolve_roles(df: pd.DataFrame, selected_features: List[str], explicit_roles: Dict[str, str] = None, inferred_types: Dict[str, str] = None) -> List[MLResolvedFeature]:
        """
        Resolves the roles of features strictly using the provided dataframe (expected to be X_train).
        """
        if explicit_roles is None:
            explicit_roles = {}
        if inferred_types is None:
            inferred_types = {}
            
        resolved = []
        for col in selected_features:
            if col not in df.columns:
                resolved.append(MLResolvedFeature(col, "excluded", "unknown", "Column not found in dataset."))
                continue
                
            series = df[col]
            valid_series = series.dropna()
            dtype = series.dtype
            
            explicit_role = explicit_roles.get(col)
            inferred_type = inferred_types.get(col, "unknown")
            tokens = MLFeatureRoleResolver._normalize_tokens(col)
            
            # Evidence 1: Explicitly mapped as datetime
            if explicit_role in ["datetime", "date"]:
                resolved.append(MLResolvedFeature(col, "datetime", inferred_type, "Explicit semantic mapping.", 1.0))
                continue
                
            # Evidence 2 & 3: Parse ratio and tokens
            parse_ratio = None
            is_datetime = False
            
            if pd.api.types.is_datetime64_any_dtype(dtype):
                is_datetime = True
                parse_ratio = 1.0
            else:
                if len(valid_series) > 0:
                    if inferred_type == "datetime" or tokens.intersection(MLFeatureRoleResolver.DATETIME_TOKENS):
                        sample = valid_series.head(100).astype(str)
                        try:
                            parsed = pd.to_datetime(sample, errors='coerce')
                            parse_ratio = parsed.notna().sum() / len(sample)
                            if parse_ratio >= 0.8:
                                is_datetime = True
                        except Exception:
                            parse_ratio = 0.0

            if is_datetime:
                resolved.append(MLResolvedFeature(col, "datetime", inferred_type, "Parsed successfully as datetime (>80%).", parse_ratio))
                continue
                
            # Remaining logic for Boolean, Numeric, Categorical
            if pd.api.types.is_bool_dtype(dtype):
                resolved.append(MLResolvedFeature(col, "boolean", inferred_type, "Pandas boolean dtype."))
                continue
                
            if pd.api.types.is_numeric_dtype(dtype):
                resolved.append(MLResolvedFeature(col, "numeric", inferred_type, "Pandas numeric dtype."))
                continue
                
            # Fallback to categorical
            resolved.append(MLResolvedFeature(col, "categorical", inferred_type, "Fallback string/object dtype."))
            
        return resolved
