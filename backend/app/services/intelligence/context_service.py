
import logging
import math
import re
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models.cleaning_plan import DatasetCleaningPlan
from app.models.dataset import Dataset
from app.models.ml_experiment import MLExperiment
from app.services.analytics_service import AnalyticsService
from app.services.data_profiling_service import DataProfilingService


logger = logging.getLogger(__name__)


class IntelligenceContextBuilder:
    """
    Builds a compact, sanitized intelligence context for Copilot,
    Decision Intelligence and Reports.

    The context contains aggregated information only. It does not include
    complete dataframe rows, raw notes, personal identifiers or artifact paths.
    """

    # These tokens indicate that a dataset column may contain personal or
    # identifier information. Domain words such as "donor" and "volunteer"
    # are intentionally NOT sensitive by themselves.
    SENSITIVE_COLUMN_TOKENS = {
        "id",
        "name",
        "email",
        "phone",
        "mobile",
        "contact",
        "address",
        "note",
        "notes",
        "comment",
        "comments",
    }

    # Structural keys used by the intelligence context. These must not be
    # redacted merely because they contain words such as "name".
    SAFE_STRUCTURAL_KEYS = {
        "workspace_name",
        "dataset",
        "name",
        "title",
        "description",
        "feature",
        "feature1",
        "feature2",
        "target",
        "model",
        "view",
        "code",
        "severity",
        "column",
        "explanation",
        "message",
        "summary",
        "insight",
        "text",
        "content",
        "value",
        "metrics",
        "feature_importance",
        "category_distributions",
    }

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    PHONE_PATTERN = re.compile(
        r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"
    )

    @staticmethod
    def _normalize_tokens(text: str) -> set[str]:
        """
        Convert snake_case, kebab-case and normal text into lowercase tokens.
        """
        normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(text))
        normalized = re.sub(r"[^A-Za-z0-9]+", "_", normalized).lower()
        return {token for token in normalized.split("_") if token}

    @classmethod
    def is_sensitive_column(cls, column_name: Optional[str]) -> bool:
        """
        Detect whether a column name represents an identifier or personal field.

        Examples:
        - donor_id -> sensitive
        - donor_email -> sensitive
        - donor_notes -> sensitive
        - donor_segment -> not sensitive
        - volunteer_events_attended -> not sensitive
        """
        if not column_name:
            return False

        tokens = cls._normalize_tokens(column_name)
        return bool(tokens & cls.SENSITIVE_COLUMN_TOKENS)

    @classmethod
    def is_sensitive(cls, text: Optional[str]) -> bool:
        """
        Backward-compatible alias used by existing tests/callers.
        """
        return cls.is_sensitive_column(text)

    @classmethod
    def _should_redact_key(cls, key: str) -> bool:
        normalized_key = str(key).strip().lower()

        if normalized_key in cls.SAFE_STRUCTURAL_KEYS:
            return False

        return cls.is_sensitive_column(normalized_key)

    @classmethod
    def _sanitize_string(cls, value: str) -> str:
        """
        Redact direct email/phone values and standalone sensitive column names.

        Normal analytical sentences containing terms such as donor or volunteer
        are preserved.
        """
        if cls.EMAIL_PATTERN.search(value):
            return "[REDACTED]"

        if cls.PHONE_PATTERN.search(value):
            return "[REDACTED]"

        # Redact values such as "donor_id" or "customer_email", but do not
        # redact full analytical sentences.
        if " " not in value.strip() and cls.is_sensitive_column(value):
            return "[REDACTED]"

        return value

    @classmethod
    def sanitize_dict_keys_and_values(cls, data: Any) -> Any:
        """
        Recursively sanitize a JSON-like structure.

        This function intentionally preserves domain language and aggregated
        analytics while removing direct personal identifiers.
        """
        if isinstance(data, dict):
            sanitized: Dict[str, Any] = {}

            for key, value in data.items():
                key_string = str(key)

                if cls._should_redact_key(key_string):
                    sanitized[key_string] = "[REDACTED]"
                else:
                    sanitized[key_string] = cls.sanitize_dict_keys_and_values(
                        value
                    )

            return sanitized

        if isinstance(data, list):
            return [
                cls.sanitize_dict_keys_and_values(item)
                for item in data
            ]

        if isinstance(data, tuple):
            return [
                cls.sanitize_dict_keys_and_values(item)
                for item in data
            ]

        if isinstance(data, str):
            return cls._sanitize_string(data)

        return cls._json_safe(data)

    @staticmethod
    def _to_dict(value: Any) -> Dict[str, Any]:
        """
        Convert Pydantic models, dictionaries and simple objects into a dict.
        """
        if value is None:
            return {}

        if isinstance(value, dict):
            return value

        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            return dumped if isinstance(dumped, dict) else {}

        if hasattr(value, "dict"):
            dumped = value.dict()
            return dumped if isinstance(dumped, dict) else {}

        if hasattr(value, "__dict__"):
            return {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }

        return {}

    @staticmethod
    def _json_safe(value: Any) -> Any:
        """
        Convert pandas/NumPy values into JSON-safe Python values.
        """
        if value is None:
            return None

        if isinstance(value, pd.Timestamp):
            return value.isoformat()

        if hasattr(value, "item"):
            try:
                value = value.item()
            except (ValueError, TypeError):
                pass

        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None

        return value

    @classmethod
    def get_insight_text(cls, insight: Any) -> Optional[str]:
        """
        Extract readable text from different Insight schema versions.

        This prevents failures when an Insight model uses fields such as
        description, message, summary or title instead of text.
        """
        if insight is None:
            return None

        if isinstance(insight, str):
            cleaned = insight.strip()
            return cleaned or None

        data = cls._to_dict(insight)
        title = data.get("title")
        if isinstance(title, str):
            title = title.strip()
        else:
            title = None

        # Find the first valid detail field
        detail = None
        for field_name in (
            "statement",
            "description",
            "explanation",
            "message",
            "summary",
            "content",
            "text",
            "insight",
            "detail",
        ):
            val = data.get(field_name)
            if isinstance(val, str) and val.strip():
                detail = val.strip()
                break

        if title and detail:
            if title != detail:
                return f"{title}: {detail}"
            return title
        elif detail:
            return detail
        elif title:
            return title

        # Last-resort readable representation for an unexpected schema.
        if data:
            for value in data.values():
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return None

    @classmethod
    def _serialize_kpi(cls, kpi: Any) -> Optional[Dict[str, Any]]:
        data = cls._to_dict(kpi)

        kpi_id = data.get("id")
        title = data.get("title") or data.get("label")
        value = data.get("value")

        if not title:
            return None

        return {
            "id": cls._json_safe(kpi_id),
            "title": str(title),
            "value": cls._json_safe(value),
        }

    @classmethod
    def _serialize_correlation(
        cls,
        correlation: Any,
    ) -> Optional[Dict[str, Any]]:
        data = cls._to_dict(correlation)

        feature1 = data.get("feature1") or data.get("column1")
        feature2 = data.get("feature2") or data.get("column2")
        coefficient = data.get("coefficient")

        if coefficient is None:
            coefficient = data.get("correlation")

        if not feature1 or not feature2 or coefficient is None:
            return None

        if (
            cls.is_sensitive_column(str(feature1))
            or cls.is_sensitive_column(str(feature2))
        ):
            return None

        return {
            "feature1": str(feature1),
            "feature2": str(feature2),
            "coefficient": cls._json_safe(coefficient),
        }

    @classmethod
    def build_context(
        cls,
        db: Session,
        workspace_id: str,
        dataset_id: str,
        view: str,
    ) -> Dict[str, Any]:
        dataset = (
            db.query(Dataset)
            .filter(
                Dataset.id == dataset_id,
                Dataset.workspace_id == workspace_id,
            )
            .first()
        )

        if not dataset:
            raise ValueError("Dataset not found")

        if dataset.status != "ready":
            raise ValueError(
                f"Dataset status is '{dataset.status}', must be 'ready'."
            )

        normalized_view = view.strip().lower()

        if normalized_view not in {"mapped", "working"}:
            raise ValueError(
                "Unsupported view. Only 'mapped' and 'working' views are allowed."
            )

        # Load the selected dataframe once.
        df, has_cleaning_plan = AnalyticsService.get_analytics_dataframe(
            db,
            dataset,
            normalized_view,
        )

        roles = AnalyticsService.get_column_roles(db, dataset.id)

        row_count = int(len(df))
        column_count = int(len(df.columns))

        # --------------------------------------------------------------
        # Quality summary
        # --------------------------------------------------------------
        try:
            quality_report = DataProfilingService.generate_quality_report(
                df,
                dataset,
                normalized_view,
            )
        except Exception:
            logger.exception(
                "Unable to generate the complete intelligence quality report."
            )
            quality_report = {
                "summary": {},
                "issues": [],
            }

        summary = quality_report.get("summary", {}) or {}
        all_issues = quality_report.get("issues", []) or []

        def issue_priority(issue: Any) -> int:
            issue_data = cls._to_dict(issue)
            severity = str(issue_data.get("severity", "")).lower()

            if severity == "critical":
                return 0

            if severity == "warning":
                return 1

            return 2

        sorted_issues = sorted(all_issues, key=issue_priority)
        limited_issues = sorted_issues[:8]

        sanitized_issues = []

        for issue in limited_issues:
            issue_data = cls._to_dict(issue)
            column_name = issue_data.get("column")

            sanitized_issues.append(
                {
                    "code": issue_data.get("code"),
                    "severity": issue_data.get("severity"),
                    "column": (
                        "[REDACTED]"
                        if cls.is_sensitive_column(column_name)
                        else column_name
                    ),
                    "title": issue_data.get("title"),
                    "explanation": (
                        issue_data.get("explanation")
                        or issue_data.get("message")
                        or issue_data.get("description")
                    ),
                    "affected_count": cls._json_safe(
                        issue_data.get("affected_count")
                    ),
                    "affected_percentage": cls._json_safe(
                        issue_data.get("affected_percentage")
                    ),
                }
            )

        total_cells = row_count * column_count
        missing_cells = int(df.isna().sum().sum())

        calculated_completeness = (
            round(((total_cells - missing_cells) / total_cells) * 100, 2)
            if total_cells > 0
            else 100.0
        )

        completeness_percent = summary.get(
            "completeness_percentage",
            calculated_completeness,
        )

        quality = {
            "completeness_percent": cls._json_safe(
                completeness_percent
            ),
            "missing_cells": missing_cells,
            "complete_rows": int(df.dropna().shape[0]),
            "issues": sanitized_issues,
        }

        # --------------------------------------------------------------
        # Cleaning plan
        # --------------------------------------------------------------
        plan = (
            db.query(DatasetCleaningPlan)
            .filter_by(dataset_id=dataset.id)
            .first()
        )

        cleaning_actions: list[str] = []

        if plan:
            config = plan.configuration or {}

            if config.get("trim_whitespace"):
                cleaning_actions.append(
                    "Trim leading and trailing whitespace."
                )

            if config.get("convert_empty_strings_to_null"):
                cleaning_actions.append(
                    "Convert empty strings to null values."
                )

            for rule in config.get("case_rules", []) or []:
                column_name = rule.get("column")
                strategy = rule.get("strategy")

                if (
                    strategy
                    and strategy != "none"
                    and not cls.is_sensitive_column(column_name)
                ):
                    cleaning_actions.append(
                        f"Convert case of '{column_name}' using "
                        f"the '{strategy}' strategy."
                    )

            for rule in config.get("missing_value_rules", []) or []:
                column_name = rule.get("column")
                strategy = rule.get("strategy")

                if (
                    column_name
                    and strategy
                    and not cls.is_sensitive_column(column_name)
                ):
                    cleaning_actions.append(
                        f"Impute missing values in '{column_name}' "
                        f"using the '{strategy}' strategy."
                    )

        cleaning = {
            "has_saved_plan": bool(plan or has_cleaning_plan),
            "actions": cleaning_actions[:20],
        }

        # --------------------------------------------------------------
        # Analytics
        # --------------------------------------------------------------
        try:
            raw_kpis = AnalyticsService.generate_kpis(df, roles)[:6]
        except Exception:
            logger.exception("Unable to generate intelligence KPIs.")
            raw_kpis = []

        kpis = []

        for kpi in raw_kpis:
            serialized_kpi = cls._serialize_kpi(kpi)

            if serialized_kpi:
                kpis.append(serialized_kpi)

        try:
            correlation_result = AnalyticsService.calculate_correlation(
                df,
                roles,
            )
        except Exception:
            logger.exception(
                "Unable to generate intelligence correlations."
            )
            correlation_result = None

        raw_correlations = []

        if correlation_result is not None:
            raw_correlations = getattr(
                correlation_result,
                "correlations",
                [],
            ) or []

            if isinstance(correlation_result, dict):
                raw_correlations = correlation_result.get(
                    "correlations",
                    raw_correlations,
                ) or []

        correlations = []

        for correlation in raw_correlations[:5]:
            serialized_correlation = cls._serialize_correlation(
                correlation
            )

            if serialized_correlation:
                correlations.append(serialized_correlation)

        try:
            charts = AnalyticsService.generate_chart_recommendations(
                df,
                roles,
            )
        except Exception:
            logger.exception(
                "Unable to generate chart recommendations for intelligence."
            )
            charts = []

        try:
            raw_insights = (
                AnalyticsService.generate_deterministic_insights(
                    df,
                    roles,
                    charts,
                    correlation_result,
                )[:6]
            )
        except Exception:
            logger.exception(
                "Unable to generate deterministic intelligence insights."
            )
            raw_insights = []

        insights = []

        for insight in raw_insights:
            insight_text = cls.get_insight_text(insight)

            if insight_text:
                insights.append(insight_text)

        category_distributions: Dict[str, Dict[str, int]] = {}

        categorical_columns = [
            column
            for column, metadata in roles.items()
            if metadata.get("role") == "categorical"
        ][:5]

        for column in categorical_columns:
            if column not in df.columns:
                continue

            if cls.is_sensitive_column(column):
                continue

            counts = (
                df[column]
                .dropna()
                .astype(str)
                .value_counts()
                .head(5)
                .to_dict()
            )

            safe_counts: Dict[str, int] = {}

            for category, count in counts.items():
                sanitized_category = cls._sanitize_string(str(category))

                if sanitized_category == "[REDACTED]":
                    continue

                safe_counts[sanitized_category] = int(count)

            category_distributions[column] = safe_counts

        analytics = {
            "kpis": kpis[:6],
            "insights": insights[:6],
            "correlations": correlations[:5],
            "category_distributions": category_distributions,
        }

        # --------------------------------------------------------------
        # Latest completed ML experiment
        # --------------------------------------------------------------
        latest_experiment = (
            db.query(MLExperiment)
            .filter_by(
                workspace_id=workspace_id,
                dataset_id=dataset_id,
                dataset_view=normalized_view,
                status="completed",
            )
            .order_by(MLExperiment.created_at.desc())
            .first()
        )

        ml: Dict[str, Any] = {
            "available": False,
        }

        if latest_experiment:
            raw_feature_importance = (
                latest_experiment.feature_importance_json or []
            )

            sanitized_feature_importance = []

            for item in raw_feature_importance[:10]:
                item_data = cls._to_dict(item)
                feature_name = str(item_data.get("feature", ""))

                sanitized_feature_importance.append(
                    {
                        "feature": (
                            "[REDACTED]"
                            if cls.is_sensitive_column(feature_name)
                            else feature_name
                        ),
                        "importance": cls._json_safe(
                            item_data.get("importance", 0.0)
                        ),
                    }
                )

            target_column = latest_experiment.target_column

            metrics_raw = latest_experiment.metrics_json or {}
            baseline_raw = metrics_raw.get("baseline") or {}
            
            compact_metrics = {}
            for key in ["mae", "mse", "rmse", "r2", "explained_variance", "median_absolute_error", "mape"]:
                if key in metrics_raw:
                    compact_metrics[key] = metrics_raw[key]
            for key in ["mae", "rmse", "r2"]:
                if key in baseline_raw:
                    compact_metrics[f"baseline_{key}"] = baseline_raw[key]

            ml = {
                "available": True,
                "task_type": latest_experiment.task_type,
                "target": (
                    "[REDACTED]"
                    if cls.is_sensitive_column(target_column)
                    else target_column
                ),
                "model": latest_experiment.best_model_name,
                "metrics": cls.sanitize_dict_keys_and_values(compact_metrics),
                "feature_importance": sanitized_feature_importance,
            }

        workspace_name = "InsightHub Workspace"

        if getattr(dataset, "workspace", None):
            workspace_name = (
                getattr(dataset.workspace, "name", None)
                or workspace_name
            )

        context = {
            "workspace_name": workspace_name,
            "dataset": {
                "name": dataset.name,
                "view": normalized_view,
                "row_count": row_count,
                "column_count": column_count,
            },
            "quality": quality,
            "cleaning": cleaning,
            "analytics": analytics,
            "ml": ml,
        }

        return cls.sanitize_dict_keys_and_values(context)
