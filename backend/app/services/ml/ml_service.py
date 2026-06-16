import json
import traceback
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.ml_experiment import MLExperiment
from app.models.workspace import utc_now
from app.schemas.ml import (
    MLMetadataResponse, MLTargetCandidate, MLFeatureRole, MLTaskRecommendation,
    MLValidateRequest, MLValidateResponse, MLValidationIssue, MLTrainRequest,
    MLExperimentResponse
)
from app.utils.working_dataframe import get_mapped_dataframe, get_working_dataframe
import pandas as pd

def get_dataset_dataframe(db: Session, dataset: Dataset, view: str) -> pd.DataFrame:
    if view == "working":
        if not dataset.cleaning_plan:
             raise ValueError("Dataset does not have a cleaning plan for working view.")
        return get_working_dataframe(dataset.id, db)
    elif view == "mapped":
        return get_mapped_dataframe(dataset.id, db)
    elif view == "original":
        if dataset.file_type == "csv":
            return pd.read_csv(dataset.file_path)
        else:
            return pd.read_excel(dataset.file_path)
    else:
        raise ValueError("Invalid view")
from app.services.ml.role_service import MLRoleService
from app.services.ml.preprocessing_service import MLPreprocessingService
from app.services.ml.training_service import MLTrainingService
from app.services.ml.evaluation_service import MLEvaluationService
from app.services.ml.explainability_service import MLExplainabilityService
from app.services.ml.artifact_service import MLArtifactService
from app.services.ml.serialization import sanitize_for_json

class MLService:
    @staticmethod
    def get_dataset_metadata(db: Session, workspace_id: str, dataset_id: str, view: str = "mapped") -> MLMetadataResponse:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.workspace_id == workspace_id).first()
        if not dataset:
            raise ValueError("Dataset not found.")

        df = get_dataset_dataframe(db, dataset, view)
        
        # Build dict of inferred types
        inferred_types = {col.normalized_name: col.inferred_type for col in dataset.columns if col.mapping_status != "exclude"}
        if view == "original":
             inferred_types = {col.original_name: col.inferred_type for col in dataset.columns}

        target_candidates = MLRoleService.get_target_candidates(df, inferred_types)
        
        data_sufficiency_warnings = []
        if len(df) < 30:
            data_sufficiency_warnings.append("Dataset has less than 30 rows. Training is not possible.")

        return MLMetadataResponse(
            dataset_name=dataset.name,
            view=view,
            has_cleaning_plan=dataset.cleaning_plan is not None,
            row_count=len(df),
            target_candidates=target_candidates,
            data_sufficiency_warnings=data_sufficiency_warnings
        )

    @staticmethod
    def validate_configuration(db: Session, workspace_id: str, dataset_id: str, req: MLValidateRequest) -> MLValidateResponse:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.workspace_id == workspace_id).first()
        if not dataset:
            raise ValueError("Dataset not found.")

        df = get_dataset_dataframe(db, dataset, req.view)
        
        inferred_types = {col.normalized_name: col.inferred_type for col in dataset.columns if col.mapping_status != "exclude"}
        if req.view == "original":
             inferred_types = {col.original_name: col.inferred_type for col in dataset.columns}
             
        # Evaluate features
        all_features = MLRoleService.get_feature_recommendations(df, req.target_column, inferred_types)
        
        if req.selected_features is None:
            resp_recommended = [f for f in all_features if f.feature_status == "recommended"]
            resp_optional = [f for f in all_features if f.feature_status == "optional"]
            resp_excluded = [f for f in all_features if f.feature_status == "excluded"]
            resp_default = [f.name for f in all_features if f.selected_by_default]
            req.selected_features = resp_default
        else:
            resp_recommended = None
            resp_optional = None
            resp_excluded = None
            resp_default = None

        included_features = []
        excluded_features = []
        validation_warnings = []
        validation_issues = []
        
        for f in all_features:
            if f.feature_status == "excluded":
                excluded_features.append(f.name)
            elif f.name in req.selected_features:
                included_features.append(f.name)
            else:
                excluded_features.append(f.name)
                
        if len(included_features) == 0:
            msg = "No valid features selected for training."
            validation_warnings.append(msg)
            validation_issues.append(MLValidationIssue(
                code="NO_FEATURES_SELECTED",
                severity="error",
                message=msg
            ))
            
        if len(included_features) > 100:
            msg = f"Too many features selected ({len(included_features)}). Maximum recommended is 100."
            validation_warnings.append(msg)
            validation_issues.append(MLValidationIssue(
                code="TOO_MANY_FEATURES",
                severity="warning",
                message=msg,
                actual=len(included_features),
                required=100
            ))
            
        # Leakage
        from app.services.ml.training_service import MLTrainingService
        try:
            # Generate deterministic training partition for statistical leakage checks
            X_tmp, _, y_tmp, _ = MLTrainingService.split_data(df[included_features + [req.target_column]], req.target_column, req.task_type, test_size=req.test_size)
            df_train_tmp = X_tmp.copy()
            df_train_tmp[req.target_column] = y_tmp
            leakage_warnings = MLRoleService.detect_leakage(df_train_tmp, req.target_column, included_features)
        except Exception:
            leakage_warnings = MLRoleService.detect_leakage(df, req.target_column, included_features)
        
        # Target
        candidates = MLRoleService.get_target_candidates(df, inferred_types)
        target_info = next((c for c in candidates if c.name == req.target_column), None)
        target_stats = MLRoleService.calculate_target_stats(df, req.target_column)
        
        if not target_info or not target_info.is_eligible:
            msg = target_info.exclusion_reason if target_info else "Target is invalid."
            validation_warnings.append(msg)
            validation_issues.append(MLValidationIssue(
                code="INVALID_TARGET",
                severity="error",
                message=msg
            ))
            
        if target_info and target_info.recommended_task != req.task_type and target_info.alternative_task != req.task_type and req.task_type != "none":
            msg = f"Task type '{req.task_type}' is not recommended for this target."
            validation_warnings.append(msg)
            validation_issues.append(MLValidationIssue(
                code="UNRECOMMENDED_TASK",
                severity="warning",
                message=msg
            ))
                
        # Data size
        can_train = True
        if len(df) < 30:
            msg = f"Dataset has fewer than 30 usable rows ({len(df)}). Training is not permitted."
            validation_warnings.append(msg)
            validation_issues.append(MLValidationIssue(
                code="INSUFFICIENT_TOTAL_ROWS",
                severity="error",
                message=msg,
                actual=len(df),
                required=30
            ))
            can_train = False
            
        if req.task_type == "classification" and target_stats and target_stats.class_distribution:
            try:
                min_class_count = target_stats.smallest_class_count
                if min_class_count is not None and min_class_count < 5:
                    msg = f"The smallest target class contains only {min_class_count} record(s). At least 5 records per class are required."
                    validation_warnings.append(msg)
                    validation_issues.append(MLValidationIssue(
                        code="INSUFFICIENT_CLASS_SIZE",
                        severity="error",
                        message=msg,
                        class_label=target_stats.smallest_class_label,
                        actual=min_class_count,
                        required=5
                    ))
                    can_train = False
            except Exception:
                pass
            
        for l in leakage_warnings:
            if l.get("action_taken") == "blocked":
                can_train = False
                msg = f"Leakage detected: {l['feature']} - {l['evidence']}"
                validation_warnings.append(msg)
                validation_issues.append(MLValidationIssue(
                    code="DATA_LEAKAGE",
                    severity="error",
                    message=msg,
                    class_label=l['feature']
                ))
                
        # Estimate encoded features
        estimated_encoded_features = 0
        for f in included_features:
            if pd.api.types.is_numeric_dtype(df[f]) or pd.api.types.is_bool_dtype(df[f]) or pd.api.types.is_datetime64_any_dtype(df[f]):
                estimated_encoded_features += 1
            else:
                # bounded by min_frequency=0.01 (max 100 per categorical feature)
                nunique = df[f].nunique()
                estimated_encoded_features += min(nunique, 100)

        if estimated_encoded_features > 5000:
            msg = f"Estimated encoded features ({estimated_encoded_features}) exceeds the limit of 5000. Please reduce selected categorical features."
            validation_warnings.append(msg)
            validation_issues.append(MLValidationIssue(
                code="EXCESSIVE_ENCODED_FEATURES",
                severity="error",
                message=msg,
                actual=estimated_encoded_features,
                required=5000
            ))
            can_train = False

        if len(included_features) > 200:
            msg = f"Raw selected features ({len(included_features)}) exceeds the limit of 200."
            validation_warnings.append(msg)
            validation_issues.append(MLValidationIssue(
                code="EXCESSIVE_RAW_FEATURES",
                severity="error",
                message=msg,
                actual=len(included_features),
                required=200
            ))
            can_train = False

        if len(included_features) == 0 or target_stats.row_count < 30:
            can_train = False

        test_size_count = int(len(df) * req.test_size)
        train_size_count = len(df) - test_size_count

        return MLValidateResponse(
            task_type=req.task_type,
            included_features=included_features,
            excluded_features=excluded_features,
            leakage_warnings=leakage_warnings,
            target_statistics=target_stats,
            estimated_training_size=train_size_count,
            estimated_test_size=test_size_count,
            validation_warnings=validation_warnings,
            validation_issues=validation_issues,
            can_train=can_train,
            recommended_features_meta=resp_recommended,
            optional_features_meta=resp_optional,
            excluded_features_meta=resp_excluded,
            default_selected_features=resp_default
        )

    @staticmethod
    def train_experiment(db: Session, workspace_id: str, dataset_id: str, req: MLTrainRequest) -> MLExperimentResponse:
        # Validate first
        val = MLService.validate_configuration(db, workspace_id, dataset_id, MLValidateRequest(
            view=req.view,
            target_column=req.target_column,
            task_type=req.task_type,
            selected_features=req.selected_features,
            test_size=req.test_size
        ))
        
        if not val.can_train:
            raise ValueError("Validation failed. Cannot proceed with training: " + ", ".join(val.validation_warnings))

        dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.workspace_id == workspace_id).first()
        df = get_dataset_dataframe(db, dataset, req.view)
        
        # Max rows sample
        if len(df) > 100000:
            df = df.sample(n=100000, random_state=42)
            
        # Create experiment record
        experiment = MLExperiment(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_view=req.view,
            target_column=req.target_column,
            task_type=req.task_type,
            selected_features=val.included_features,
            excluded_features=val.excluded_features,
            status="running",
            row_count=len(df),
            random_seed=42,
            configuration_json={"test_size": req.test_size}
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        
        try:
            # Splitting
            X_train, X_test, y_train, y_test = MLTrainingService.split_data(df[val.included_features + [req.target_column]], req.target_column, req.task_type, test_size=req.test_size)
            
            experiment.training_row_count = len(X_train)
            experiment.test_row_count = len(X_test)
            
            # Training candidates
            try:
                training_result, baseline_pipeline = MLTrainingService.train_candidates(X_train, y_train, req.task_type, val.included_features)
                candidate_results = training_result.candidate_results
                final_pipeline = training_result.winner_pipeline
                metric_direction = training_result.metric_direction
            except Exception as e:
                # Sanitize errors
                experiment.status = "failed"
                experiment.error_message = str(e).split('\n')[0]
                db.commit()
                raise ValueError(experiment.error_message)
            
            # Find best candidate
            best_candidate = None
            baseline_metric = None
            for r in candidate_results:
                if r.is_baseline:
                    baseline_metric = r.cv_mean
                if r.status == "completed" and not r.is_baseline:
                    if best_candidate is None:
                        best_candidate = r
                    else:
                        if metric_direction == "higher_is_better" and r.cv_mean > best_candidate.cv_mean:
                            best_candidate = r
                        elif metric_direction == "lower_is_better" and r.cv_mean < best_candidate.cv_mean:
                            best_candidate = r
            
            if not best_candidate:
                experiment.status = "failed"
                experiment.error_message = "All non-baseline models failed to complete."
                db.commit()
                raise ValueError(experiment.error_message)
                
            experiment.primary_metric = best_candidate.primary_metric_name
            experiment.best_model_name = best_candidate.display_name
            experiment.best_cv_metric = str(best_candidate.cv_mean)
            experiment.baseline_metric = str(baseline_metric)
            
            # Evaluation on test set
            if req.task_type == "classification":
                eval_res = MLEvaluationService.evaluate_classification(final_pipeline, X_test, y_test)
                baseline_res = MLEvaluationService.evaluate_classification(baseline_pipeline, X_test, y_test)
                experiment.test_metric = str(eval_res.f1_weighted)
                metrics_dict = eval_res.model_dump()
                metrics_dict["baseline"] = baseline_res.model_dump()
                experiment.metrics_json = sanitize_for_json(metrics_dict)
            else:
                eval_res = MLEvaluationService.evaluate_regression(final_pipeline, X_test, y_test)
                baseline_res = MLEvaluationService.evaluate_regression(baseline_pipeline, X_test, y_test)
                experiment.test_metric = str(eval_res.rmse)
                metrics_dict = eval_res.model_dump()
                metrics_dict["baseline"] = baseline_res.model_dump()
                experiment.metrics_json = sanitize_for_json(metrics_dict)
                
            # Explainability
            feature_importance, importance_method = MLExplainabilityService.extract_feature_importances(final_pipeline, req.task_type)
            experiment.feature_importance_json = sanitize_for_json([fi.model_dump() for fi in feature_importance])
            
            # Save Preprocessing Manifest
            import copy
            config_json = copy.deepcopy(experiment.configuration_json or {})
            config_json["preprocessing_manifest"] = training_result.preprocessing_manifest
            experiment.configuration_json = sanitize_for_json(config_json)
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(experiment, "configuration_json")
            
            # Prediction schema
            feature_meta_map = {}
            if val.recommended_features_meta:
                for f in val.recommended_features_meta: feature_meta_map[f.name] = f
            if val.optional_features_meta:
                for f in val.optional_features_meta: feature_meta_map[f.name] = f
            
            resolved_map = {f.name: f for f in training_result.resolved_features}

            schema = []
            for col in val.included_features:
                meta = feature_meta_map.get(col)
                resolved = resolved_map.get(col)
                dtype = str(X_train[col].dtype)
                
                categories = None
                input_type = "text"
                role = "feature"
                
                if resolved:
                    role = resolved.role
                    if role == "datetime":
                        input_type = "date"
                    elif role == "boolean":
                        input_type = "boolean"
                    elif role == "categorical":
                        input_type = "select"
                        categories = sorted([str(x) for x in X_train[col].dropna().unique()])
                    elif role == "numeric":
                        if pd.api.types.is_integer_dtype(X_train[col]):
                            input_type = "integer"
                        else:
                            input_type = "decimal"
                            
                schema_entry = {
                    "name": col,
                    "display_name": meta.display_name if meta else col,
                    "role": role,
                    "type": dtype,
                    "input_type": input_type,
                    "categories": categories,
                }
                if role == "numeric":
                    mn = X_train[col].min()
                    mx = X_train[col].max()
                    schema_entry["min"] = float(mn) if not pd.isna(mn) else None
                    schema_entry["max"] = float(mx) if not pd.isna(mx) else None
                    schema_entry["is_integer"] = bool(pd.api.types.is_integer_dtype(X_train[col]))
                    
                schema.append(schema_entry)
                
            experiment.prediction_schema = sanitize_for_json(schema)
            
            # Artifacts
            artifact_path = MLArtifactService.save_pipeline(experiment.id, final_pipeline)
            experiment.artifact_path = artifact_path
            
            # Strict Completion Gate
            assert experiment.best_model_name is not None
            assert experiment.metrics_json is not None
            if req.task_type == "regression":
                assert "rmse" in experiment.metrics_json
                assert "mae" in experiment.metrics_json
                assert "mse" in experiment.metrics_json
                assert "r2" in experiment.metrics_json
                assert "explained_variance" in experiment.metrics_json
            
            assert experiment.prediction_schema
            assert len(experiment.prediction_schema) == len(val.included_features)
            for field in experiment.prediction_schema:
                assert field.get("name")
                assert field.get("role")
                assert field.get("input_type")
            
            assert config_json.get("preprocessing_manifest")
            assert experiment.artifact_path is not None
            import os
            assert os.path.exists(experiment.artifact_path)
            
            experiment.status = "completed"
            experiment.completed_at = utc_now()
            
            db.commit()
            
            # Build full response
            return MLService.get_experiment(db, workspace_id, experiment.id, True)

        except Exception as e:
            db.rollback()
            experiment.status = "failed"
            experiment.error_message = sanitize_for_json(str(e))
            experiment.completed_at = utc_now()
            db.commit()
            
            # Log traceback internally but don't expose
            traceback.print_exc()
            
            # Return a non-success HTTP response by raising RuntimeError
            raise RuntimeError(f"Training failed: {experiment.error_message}")

    @staticmethod
    def list_experiments(db: Session, workspace_id: str, dataset_id: str = None, task_type: str = None, status: str = None) -> List[Any]:
        from app.schemas.ml import MLExperimentSummary
        import os
        
        query = db.query(MLExperiment).join(Dataset).filter(MLExperiment.workspace_id == workspace_id)
        
        if dataset_id:
            query = query.filter(MLExperiment.dataset_id == dataset_id)
        if task_type:
            query = query.filter(MLExperiment.task_type == task_type)
        if status:
            query = query.filter(MLExperiment.status == status)
            
        exps = query.order_by(MLExperiment.created_at.desc()).all()
        
        results = []
        for exp in exps:
            artifact_available = False
            if exp.status == "completed" and exp.artifact_path:
                try:
                    MLArtifactService.get_artifact_path(exp.id)
                    artifact_available = os.path.exists(MLArtifactService.get_artifact_path(exp.id))
                except ValueError:
                    pass
            
            results.append(MLExperimentSummary(
                id=exp.id,
                dataset_id=exp.dataset_id,
                dataset_name=exp.dataset.name,
                dataset_view=exp.dataset_view,
                target_column=exp.target_column,
                task_type=exp.task_type,
                status=exp.status,
                best_model_name=exp.best_model_name,
                primary_metric=exp.primary_metric,
                best_cv_metric=float(exp.best_cv_metric) if exp.best_cv_metric else None,
                test_metric=float(exp.test_metric) if exp.test_metric else None,
                created_at=exp.created_at.isoformat() if exp.created_at else "",
                completed_at=exp.completed_at.isoformat() if exp.completed_at else None,
                artifact_available=artifact_available
            ))
            
        return results

    @staticmethod
    def get_experiment(db: Session, workspace_id: str, experiment_id: str, include_details: bool = False) -> MLExperimentResponse:
        exp = db.query(MLExperiment).filter(MLExperiment.id == experiment_id, MLExperiment.workspace_id == workspace_id).first()
        if not exp:
            raise ValueError("Experiment not found.")
            
        resp = MLExperimentResponse(
            id=exp.id,
            workspace_id=exp.workspace_id,
            dataset_id=exp.dataset_id,
            dataset_view=exp.dataset_view,
            target_column=exp.target_column,
            task_type=exp.task_type,
            status=exp.status,
            selected_features=exp.selected_features,
            excluded_features=exp.excluded_features,
            primary_metric=exp.primary_metric,
            best_model_name=exp.best_model_name,
            baseline_metric=float(exp.baseline_metric) if exp.baseline_metric else None,
            best_cv_metric=float(exp.best_cv_metric) if exp.best_cv_metric else None,
            test_metric=float(exp.test_metric) if exp.test_metric else None,
            row_count=exp.row_count,
            training_row_count=exp.training_row_count,
            test_row_count=exp.test_row_count,
            error_message=exp.error_message,
            created_at=exp.created_at.isoformat() if exp.created_at else "",
            completed_at=exp.completed_at.isoformat() if exp.completed_at else None,
            artifact_available=False
        )
        
        import os
        if exp.status == "completed" and exp.artifact_path:
            try:
                MLArtifactService.get_artifact_path(exp.id)
                resp.artifact_available = os.path.exists(MLArtifactService.get_artifact_path(exp.id))
            except ValueError:
                pass
                
        
        if include_details and exp.status == "completed":
            if exp.task_type == "classification" and exp.metrics_json:
                resp.classification_evaluation = exp.metrics_json
            elif exp.task_type == "regression" and exp.metrics_json:
                resp.regression_evaluation = exp.metrics_json
                
            if exp.feature_importance_json:
                resp.feature_importance = exp.feature_importance_json
                
            if exp.prediction_schema:
                pipeline = None
                if resp.artifact_available:
                    try:
                        pipeline = MLArtifactService.load_pipeline(exp.id)
                    except Exception:
                        pass
                
                normalized = []
                for item in exp.prediction_schema:
                    name = item.get("name") or item.get("feature_name") or item.get("column_name") or item.get("field_name")
                    if not name:
                        continue
                        
                    display_name = item.get("display_name")
                    if not display_name:
                        display_name = name.replace("_", " ").title()
                        
                    raw_type = item.get("input_type") or item.get("type") or "text"
                    raw_type = str(raw_type).lower()
                    role = item.get("role", "feature")
                    
                    categories = item.get("categories") or item.get("known_categories") or item.get("options")
                    is_datetime = role in ["datetime", "date"] or raw_type in ["date", "datetime"]
                    
                    is_legacy_categorical_date = False
                    
                    if pipeline:
                        preprocessor = pipeline.named_steps.get("preprocessor")
                        if preprocessor:
                            transformers = getattr(preprocessor, "transformers_", [])
                            for t_name, t_obj, t_cols in transformers:
                                if name in t_cols:
                                    if t_name == "dt":
                                        is_datetime = True
                                    elif t_name == "cat" and (name.endswith("_date") or name == "date" or role in ["date", "datetime"] or raw_type in ["date", "datetime"]):
                                        is_legacy_categorical_date = True
                                        is_datetime = False # explicitly it wasn't a datetime transformer
                                        
                                    encoder = None
                                    if hasattr(t_obj, "named_steps"):
                                        encoder = t_obj.named_steps.get("onehot")
                                    elif hasattr(t_obj, "categories_"):
                                        encoder = t_obj
                                        
                                    if t_name == "cat" and encoder and hasattr(encoder, "categories_") and not categories:
                                        idx = list(t_cols).index(name)
                                        if len(encoder.categories_) > idx:
                                            categories = [str(c) for c in encoder.categories_[idx]]
                    
                    if is_legacy_categorical_date:
                        from app.schemas.ml import LegacyPreprocessingWarning
                        warning_obj = LegacyPreprocessingWarning(
                            code="DATETIME_ENCODED_AS_CATEGORY",
                            feature=name,
                            message=f"{display_name} was encoded as a categorical value in this legacy experiment. Unseen dates may be ignored. Retraining is recommended."
                        )
                        # avoid duplicate warnings
                        if not any(w.code == "DATETIME_ENCODED_AS_CATEGORY" and w.feature == name for w in resp.legacy_preprocessing_warnings):
                            resp.legacy_preprocessing_warnings.append(warning_obj)
                            
                    input_type = item.get("input_type")
                    if not input_type or input_type == "text":
                        if is_datetime:
                            input_type = "date"
                        elif role == "boolean" or "bool" in raw_type:
                            input_type = "boolean"
                        elif role in ["categorical", "category"] or (categories and len(categories) > 0) or raw_type in ["select", "categorical", "category"]:
                            input_type = "select"
                        elif raw_type == "integer" or "int" in raw_type:
                            input_type = "integer"
                        elif raw_type == "decimal" or raw_type == "number" or "float" in raw_type:
                            input_type = "decimal"
                        else:
                            input_type = "text"
                            
                    if is_datetime:
                        categories = None
                        
                    normalized.append({
                        "name": name,
                        "display_name": display_name,
                        "role": role,
                        "input_type": input_type,
                        "required": item.get("required", False),
                        "allows_missing": item.get("allows_missing", True),
                        "categories": categories,
                        "minimum": item.get("minimum") or item.get("min"),
                        "maximum": item.get("maximum") or item.get("max"),
                        "step": item.get("step")
                    })
                resp.prediction_schema = normalized
            
        return resp
        
    @staticmethod
    def delete_experiment(db: Session, workspace_id: str, experiment_id: str) -> None:
        exp = db.query(MLExperiment).filter(MLExperiment.id == experiment_id, MLExperiment.workspace_id == workspace_id).first()
        if not exp:
            raise ValueError("Experiment not found.")
            
        MLArtifactService.delete_artifact(exp.id)
        db.delete(exp)
        db.commit()

    @staticmethod
    def delete_dataset_models(db: Session, workspace_id: str, dataset_id: str) -> None:
        """
        Deletes all ML experiments and their corresponding model artifacts for a given dataset.
        """
        exps = db.query(MLExperiment).filter(MLExperiment.dataset_id == dataset_id, MLExperiment.workspace_id == workspace_id).all()
        for exp in exps:
            MLArtifactService.delete_artifact(exp.id)
            db.delete(exp)
        db.commit()

    @staticmethod
    def predict(db: Session, workspace_id: str, experiment_id: str, features: Dict[str, Any]) -> Any:
        exp = db.query(MLExperiment).filter(MLExperiment.id == experiment_id, MLExperiment.workspace_id == workspace_id).first()
        if not exp or exp.status != "completed":
            raise ValueError("Experiment not found or not completed.")
            
        try:
            pipeline = MLArtifactService.load_pipeline(exp.id)
        except FileNotFoundError:
            raise ValueError("Model artifact is not available. Prediction cannot be performed.")
        
        schema = exp.prediction_schema or []
        schema_map = {f["name"]: f for f in schema}
        warnings = []
        filtered_features = {}
        
        for k, v in features.items():
            if k == exp.target_column:
                warnings.append(f"Target column '{k}' was ignored.")
                continue
            if k not in schema_map:
                warnings.append(f"Field '{k}' was ignored because it was not used during training.")
                continue
            
            sch = schema_map[k]
            if v is not None and v != "":
                if sch.get("categories"):
                    if str(v) not in sch["categories"]:
                        warnings.append(f"The value \"{v}\" was not present in the trained category set for {k} and was treated as an unknown category.")
                elif str(sch.get("type", "")).startswith("int") or str(sch.get("type", "")).startswith("float"):
                    try:
                        v = float(v)
                    except ValueError:
                        warnings.append(f"Field '{k}' expected numeric but got '{v}'. Value may be ignored or imputed.")
            filtered_features[k] = v
            
        for k in schema_map:
            if k not in filtered_features:
                filtered_features[k] = None

        df = pd.DataFrame([filtered_features])
        
        pred = pipeline.predict(df)[0]
        
        res = {
            "task_type": exp.task_type,
            "prediction": sanitize_for_json(pred),
            "input_validation_warnings": warnings
        }
        
        if hasattr(pipeline, "predict_proba"):
            try:
                proba = pipeline.predict_proba(df)[0]
                classes = pipeline.classes_
                probs = [{"label": str(c), "probability": float(p)} for c, p in zip(classes, proba)]
                res["probabilities"] = probs
                
                max_prob = float(max(proba))
                res["maximum_probability"] = max_prob
                if max_prob < 0.60:
                    res["low_confidence"] = True
                    res["confidence_message"] = "The model is not strongly confident in this prediction."
                else:
                    res["low_confidence"] = False
                    res["confidence_message"] = None
            except Exception as e:
                import traceback
                print("PREDICT_PROBA EXCEPTION:", traceback.format_exc())
                res["probabilities"] = None
                
        return res
