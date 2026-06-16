import pytest
import os
import pandas as pd
import numpy as np
from app.services.ml.ml_service import MLService
from app.services.ml.evaluation_service import MLEvaluationService, calculate_rmse
from app.schemas.ml import MLTrainRequest, MLValidateRequest
from unittest.mock import patch, MagicMock
from app.models.ml_experiment import MLExperiment
from app.core.database import SessionLocal

def test_rmse_helper():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    assert calculate_rmse(y_true, y_pred) == 0.0
    
    y_true = np.array([1.0, 2.0])
    y_pred = np.array([0.0, 0.0])
    # mse = (1 + 4) / 2 = 2.5
    # rmse = sqrt(2.5) ≈ 1.5811
    assert abs(calculate_rmse(y_true, y_pred) - 1.5811) < 1e-4

def test_regression_evaluation_metrics():
    y_test = pd.Series([10.0, 20.0, 30.0], name="target")
    pipeline = MagicMock()
    pipeline.predict.return_value = np.array([12.0, 18.0, 30.0])
    
    res = MLEvaluationService.evaluate_regression(pipeline, pd.DataFrame(), y_test)
    
    assert "rmse" in res.model_dump()
    assert "mae" in res.model_dump()
    assert "mse" in res.model_dump()
    assert "r2" in res.model_dump()
    assert "explained_variance" in res.model_dump()
    assert res.mae == 4.0 / 3.0
    assert res.mse == 8.0 / 3.0
    assert res.r2 is not None

def test_evaluation_exception_results_in_status_failed():
    # If an exception is thrown during evaluation, the whole process fails
    from app.services.ml.ml_service import MLService
    db = SessionLocal()
    try:
        # Mocking train_candidates to succeed, but evaluate_regression to throw an exception
        with patch('app.services.ml.ml_service.MLService.validate_configuration') as mock_val:
            from app.schemas.ml import MLValidateResponse, MLTargetStats
            mock_val.return_value = MLValidateResponse(
                status="valid", task_type="regression", included_features=["monthly_income"],
                selected_features=["monthly_income"], excluded_features=[], leakage_warnings=[], validation_warnings=[],
                target_statistics=MLTargetStats(type="numeric", missing_count=0, row_count=100, unique_count=100, mean=50, std=10, min=0, max=100),
                estimated_training_size=80, estimated_test_size=20, can_train=True, row_count=100
            )
            with patch('app.services.ml.ml_service.get_dataset_dataframe') as mock_df:
                mock_df.return_value = pd.DataFrame(columns=["monthly_income", "age"])
                with patch('app.services.ml.ml_service.MLTrainingService.split_data') as mock_split:
                    import numpy as np
                    X_tr = pd.DataFrame({"monthly_income": [1.0, 2.0]})
                    X_te = pd.DataFrame({"monthly_income": [3.0]})
                    y_tr = np.array([100.0, 200.0])
                    y_te = np.array([300.0])
                    mock_split.return_value = (X_tr, X_te, y_tr, y_te)
                    with patch('app.services.ml.training_service.MLTrainingService.train_candidates') as mock_train:
                        from app.services.ml.feature_roles import MLTrainingResult, MLResolvedFeature
                        from app.schemas.ml import MLModelCandidateResult
                        dummy_candidate = MLModelCandidateResult(
                            model_id="ridge", display_name="Ridge Regression", is_baseline=False,
                            status="completed", cv_mean=0.5, primary_metric_name="RMSE",
                            metric_direction="lower_is_better", training_duration_seconds=0.1
                        )
                        baseline_candidate = MLModelCandidateResult(
                            model_id="dummy", display_name="Dummy Baseline", is_baseline=True,
                            status="completed", cv_mean=1.0, primary_metric_name="RMSE",
                            metric_direction="lower_is_better", training_duration_seconds=0.01
                        )
                        training_result = MLTrainingResult(
                            winner_pipeline=MagicMock(),
                            winner_name="Ridge Regression",
                            candidate_results=[baseline_candidate, dummy_candidate],
                            resolved_features=[MLResolvedFeature(name="monthly_income", role="numeric", inferred_type="float64", reason="numeric dtype")],
                            preprocessing_manifest={"numeric_features": ["monthly_income"], "categorical_features": [], "boolean_features": [], "datetime_features": []},
                            metric_direction="lower_is_better"
                        )
                        mock_train.return_value = (training_result, MagicMock())
                        with patch('app.services.ml.evaluation_service.MLEvaluationService.evaluate_regression') as mock_eval:
                            mock_eval.side_effect = Exception("Simulated Evaluation Crash")
        
                            req = MLTrainRequest(
                                view="mapped", target_column="age", task_type="regression",
                                selected_features=["monthly_income"], test_size=0.2, models=["Ridge Regression"]
                            )
        
                            try:
                                # Mock Dataset query
                                with patch.object(db, 'query') as mock_query:
                                    mock_query.return_value.filter.return_value.first.return_value = MagicMock()
                                    MLService.train_experiment(db, "fake-workspace", "fake-dataset", req)
                                    pytest.fail("Should have raised RuntimeError")
                            except RuntimeError as e:
                                assert "Simulated Evaluation Crash" in str(e)
    finally:
        db.close()
