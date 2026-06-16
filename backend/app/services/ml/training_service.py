import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.model_selection import train_test_split, StratifiedKFold, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, RandomForestRegressor, ExtraTreesRegressor
from sklearn.metrics import get_scorer
from app.schemas.ml import MLModelCandidateResult

class MLTrainingService:
    @staticmethod
    def split_data(df: pd.DataFrame, target_column: str, task_type: str, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Safely splits data using stratify for classification.
        """
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        if task_type == "classification":
            try:
                # Need at least 2 instances per class in the dataset to stratify, and min class > 1.
                # Actually, role_service guarantees min class count >= 5.
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
            except Exception:
                # Fallback
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        else:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
            
        return X_train, X_test, y_train, y_test

    @staticmethod
    def get_candidate_models(task_type: str, random_state: int = 42) -> Dict[str, Dict[str, Any]]:
        """
        Returns bounded baseline and candidate models.
        """
        if task_type == "classification":
            return {
                "dummy": {
                    "display_name": "Baseline (Dummy)",
                    "estimator": DummyClassifier(strategy="prior"),
                    "is_baseline": True,
                    "requires_scaling": False
                },
                "logreg": {
                    "display_name": "Logistic Regression",
                    "estimator": LogisticRegression(max_iter=1000, random_state=random_state, class_weight="balanced"),
                    "is_baseline": False,
                    "requires_scaling": True
                },
                "rf": {
                    "display_name": "Random Forest",
                    "estimator": RandomForestClassifier(n_estimators=50, max_depth=10, random_state=random_state, class_weight="balanced"),
                    "is_baseline": False,
                    "requires_scaling": False
                },
                "et": {
                    "display_name": "Extra Trees",
                    "estimator": ExtraTreesClassifier(n_estimators=50, max_depth=10, random_state=random_state, class_weight="balanced"),
                    "is_baseline": False,
                    "requires_scaling": False
                }
            }
        else:
            return {
                "dummy": {
                    "display_name": "Baseline (Dummy)",
                    "estimator": DummyRegressor(strategy="mean"),
                    "is_baseline": True,
                    "requires_scaling": False
                },
                "ridge": {
                    "display_name": "Ridge Regression",
                    "estimator": Ridge(random_state=random_state, solver='sparse_cg'),
                    "is_baseline": False,
                    "requires_scaling": True
                },
                "rf": {
                    "display_name": "Random Forest",
                    "estimator": RandomForestRegressor(n_estimators=50, max_depth=10, random_state=random_state),
                    "is_baseline": False,
                    "requires_scaling": False
                },
                "et": {
                    "display_name": "Extra Trees",
                    "estimator": ExtraTreesRegressor(n_estimators=50, max_depth=10, random_state=random_state),
                    "is_baseline": False,
                    "requires_scaling": False
                }
            }

    @staticmethod
    def train_candidates(X_train: pd.DataFrame, y_train: pd.Series, task_type: str, selected_features: List[str], random_state: int = 42) -> Any:
        """
        Runs CV for candidate models, selects the best non-baseline, and fits it on the entire training set.
        Returns MLTrainingResult.
        """
        from app.services.ml.preprocessing_service import MLPreprocessingService
        from app.services.ml.feature_roles import MLFeatureRoleResolver, MLTrainingResult
        
        models = MLTrainingService.get_candidate_models(task_type, random_state=random_state)
        
        if task_type == "classification":
            cv = StratifiedKFold(n_splits=min(5, y_train.value_counts().min()), shuffle=True, random_state=random_state)
            scoring = "f1_weighted"
            primary_metric_name = "F1 Weighted"
            metric_direction = "higher_is_better"
        else:
            cv = KFold(n_splits=5, shuffle=True, random_state=random_state)
            from app.services.ml.evaluation_service import calculate_rmse
            from sklearn.metrics import make_scorer
            scoring = make_scorer(calculate_rmse, greater_is_better=False)
            primary_metric_name = "RMSE"
            metric_direction = "lower_is_better"
            
        results = []
        best_score = -np.inf if metric_direction == "higher_is_better" else np.inf
        best_model_id = None
        
        # Resolve feature roles
        resolved_features = MLFeatureRoleResolver.resolve_roles(X_train, selected_features)
        
        # Build Preprocessing Manifest
        manifest = {
            "numeric_features": [f.name for f in resolved_features if f.role == "numeric"],
            "categorical_features": [f.name for f in resolved_features if f.role == "categorical"],
            "boolean_features": [f.name for f in resolved_features if f.role == "boolean"],
            "datetime_features": [f.name for f in resolved_features if f.role == "datetime"],
            "excluded_features": [f.name for f in resolved_features if f.role == "excluded"]
        }
        
        for model_id, model_info in models.items():
            start_time = time.time()
            estimator = model_info["estimator"]
            is_baseline = model_info["is_baseline"]
            display_name = model_info["display_name"]
            requires_scaling = model_info["requires_scaling"]
            
            # Construct model-specific preprocessor and pipeline
            preprocessor = MLPreprocessingService.build_preprocessor(resolved_features, scale=requires_scaling)
            pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('estimator', estimator)
            ])
            
            try:
                # Run cross-validation strictly on training set using the full pipeline
                scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1, error_score="raise")
                
                # Handle direction logic
                if metric_direction == "lower_is_better":
                    # Convert neg metric to positive metric
                    scores = -scores
                    cv_mean = float(np.mean(scores))
                    cv_std = float(np.std(scores))
                    cv_min = float(np.min(scores))
                    cv_max = float(np.max(scores))
                    
                    if not is_baseline:
                        if cv_mean < best_score:
                            best_score = cv_mean
                            best_model_id = model_id
                else:
                    cv_mean = float(np.mean(scores))
                    cv_std = float(np.std(scores))
                    cv_min = float(np.min(scores))
                    cv_max = float(np.max(scores))
                    
                    if not is_baseline:
                        if cv_mean > best_score:
                            best_score = cv_mean
                            best_model_id = model_id
                    
                results.append(MLModelCandidateResult(
                    model_id=model_id,
                    display_name=display_name,
                    is_baseline=is_baseline,
                    status="completed",
                    cv_mean=cv_mean,
                    cv_std=cv_std,
                    cv_min=cv_min,
                    cv_max=cv_max,
                    cv_fold_scores=[float(x) for x in scores],
                    primary_metric_name=primary_metric_name,
                    metric_direction=metric_direction,
                    training_duration_seconds=round(time.time() - start_time, 2)
                ))
            except Exception as e:
                results.append(MLModelCandidateResult(
                    model_id=model_id,
                    display_name=display_name,
                    is_baseline=is_baseline,
                    status="failed",
                    primary_metric_name=primary_metric_name,
                    metric_direction=metric_direction,
                    training_duration_seconds=round(time.time() - start_time, 2),
                    failure_reason=str(e)
                ))
        
        if best_model_id is None:
            raise ValueError("All non-baseline candidate models failed during cross-validation.")
            
        # Build and fit the final selected pipeline
        best_info = models[best_model_id]
        best_preprocessor = MLPreprocessingService.build_preprocessor(resolved_features, scale=best_info["requires_scaling"])
        final_pipeline = Pipeline(steps=[
            ('preprocessor', best_preprocessor),
            ('estimator', best_info["estimator"])
        ])
        final_pipeline.fit(X_train, y_train)
        
        # Build and fit the baseline pipeline (wait, where is it returned? the schema didn't include baseline pipeline. We need to evaluate baseline though in ml_service).
        # Let's keep returning the baseline_pipeline or add it to MLTrainingResult. Let's add it.
        baseline_info = models["dummy"]
        baseline_preprocessor = MLPreprocessingService.build_preprocessor(resolved_features, scale=baseline_info["requires_scaling"])
        baseline_pipeline = Pipeline(steps=[
            ('preprocessor', baseline_preprocessor),
            ('estimator', baseline_info["estimator"])
        ])
        baseline_pipeline.fit(X_train, y_train)
        
        return MLTrainingResult(
            winner_pipeline=final_pipeline,
            winner_name=best_info["display_name"],
            candidate_results=results,
            resolved_features=resolved_features,
            preprocessing_manifest=manifest,
            metric_direction=metric_direction
        ), baseline_pipeline
