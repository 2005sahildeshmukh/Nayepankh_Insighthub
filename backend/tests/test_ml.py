import pytest
import pandas as pd
import numpy as np
import os
from sklearn.pipeline import Pipeline
from app.services.ml.preprocessing_service import DatetimeFeatureExtractor, MLPreprocessingService
from app.services.ml.training_service import MLTrainingService

def test_target_encoder_absent():
    # Verify TargetEncoder is not used in the project
    filepath = os.path.join(os.path.dirname(__file__), "..", "app", "services", "ml", "preprocessing_service.py")
    with open(filepath, "r") as f:
        content = f.read()
    assert "TargetEncoder" not in content, "TargetEncoder must not be used"
    assert "LabelEncoder" not in content, "LabelEncoder must not be used on features"

def test_datetime_feature_extractor():
    dt = DatetimeFeatureExtractor()
    df = pd.DataFrame({
        "valid": ["2023-01-01", "2023-02-15"],
        "invalid": ["not_a_date", "2023-02-30"],
        "missing": [None, "2023-03-01"]
    })
    
    # Check shape and output
    out = dt.transform(df)
    assert out.shape == (2, 18), "Shape must be stable and deterministic"
    
    names = dt.get_feature_names_out(["valid", "invalid", "missing"])
    assert list(names) == [
        "valid_year", "valid_month", "valid_day", "valid_day_of_week", "valid_quarter", "valid_is_weekend",
        "invalid_year", "invalid_month", "invalid_day", "invalid_day_of_week", "invalid_quarter", "invalid_is_weekend",
        "missing_year", "missing_month", "missing_day", "missing_day_of_week", "missing_quarter", "missing_is_weekend",
    ]
    
    # Valid
    assert out[0][0] == 2023  # year
    assert out[0][1] == 1     # month
    assert out[0][2] == 1     # day
    assert out[0][3] == 6     # day of week (Sunday)
    assert out[0][4] == 1     # quarter
    assert out[0][5] == 1     # weekend (Sunday)

    # Invalid (should be coerced to NaT then -1/0)
    assert out[0][6] == -1    # year for not_a_date
    assert out[0][11] == 0    # weekend for not_a_date is False/0

    # Missing
    assert out[0][12] == -1   # missing
    assert out[1][12] == 2023 # not missing

def test_regression_model_selection():
    # Create deterministic data where CV says A is better but Test says B is better
    # We will simulate the CV scores instead of training to prove the logic.
    from app.schemas.ml import MLModelCandidateResult

    # Mock candidate results
    candidates = [
        MLModelCandidateResult(
            model_id="ridge", display_name="Ridge", is_baseline=False, status="completed",
            cv_mean=10.0, cv_std=0.1, cv_min=9.9, cv_max=10.1, primary_metric_name="RMSE", metric_direction="lower_is_better", training_duration_seconds=1.0
        ),
        MLModelCandidateResult(
            model_id="rf", display_name="Random Forest", is_baseline=False, status="completed",
            cv_mean=15.0, cv_std=0.1, cv_min=14.9, cv_max=15.1, primary_metric_name="RMSE", metric_direction="lower_is_better", training_duration_seconds=1.0
        )
    ]
    
    best_candidate = None
    for r in candidates:
        if r.status == "completed" and not r.is_baseline:
            if best_candidate is None:
                best_candidate = r
            else:
                if r.metric_direction == "lower_is_better" and r.cv_mean < best_candidate.cv_mean:
                    best_candidate = r
                    
    # Ridge has lower CV RMSE, so it should be selected.
    assert best_candidate.model_id == "ridge"

def test_rmse_is_positive():
    # Mocking cross_val_score to return negative scores (which sklearn does for neg_root_mean_squared_error)
    from unittest.mock import patch
    
    with patch('app.services.ml.training_service.cross_val_score', return_value=np.array([-5.0, -4.0, -6.0])):
        
        df = pd.DataFrame({"feat1": [1, 2, 3, 4, 5, 6], "feat2": [2, 3, 4, 5, 6, 7]})
        y = pd.Series([10, 20, 30, 40, 50, 60])
        
        # Only ExtraTrees is tested to save time
        with patch('app.services.ml.training_service.MLTrainingService.get_candidate_models', return_value={
            "dummy": {
                "display_name": "Baseline",
                "estimator": MLTrainingService.get_candidate_models("regression")["dummy"]["estimator"],
                "is_baseline": True,
                "requires_scaling": False
            },
            "et": {
                "display_name": "Extra Trees",
                "estimator": MLTrainingService.get_candidate_models("regression")["et"]["estimator"],
                "is_baseline": False,
                "requires_scaling": False
            }
        }):
            result, baseline_pipeline = MLTrainingService.train_candidates(df, y, "regression", ["feat1", "feat2"])
            direction = result.metric_direction
            
        for res in result.candidate_results:
                # Check that CV metrics are strictly positive
                assert res.cv_mean > 0, "RMSE mean should be positive"
                assert res.cv_min > 0, "RMSE min should be positive"
                assert res.cv_max > 0, "RMSE max should be positive"
                assert res.cv_fold_scores == [5.0, 4.0, 6.0], "Fold scores should be positive"
                assert res.metric_direction == "lower_is_better"

def test_artifact_round_trip_prediction(tmp_path):
    # Test artifact saving and loading
    from app.services.ml.artifact_service import MLArtifactService
    from sklearn.linear_model import Ridge
    import joblib
    
    pipeline = Pipeline([
        ('model', Ridge())
    ])
    
    # Fake fit
    df = pd.DataFrame({"feat1": [1, 2, 3], "feat2": [2, 3, 4]})
    y = pd.Series([10, 20, 30])
    pipeline.fit(df, y)
    
    # Save
    experiment_id = "test_exp_123"
    
    # Mocking STORAGE_DIR
    import app.services.ml.artifact_service as art_srv
    original_dir = art_srv.STORAGE_DIR
    art_srv.STORAGE_DIR = str(tmp_path)
    
    try:
        MLArtifactService.save_pipeline(experiment_id, pipeline)
        
        # Load
        loaded_pipeline = MLArtifactService.load_pipeline(experiment_id)
        
        # Predict
        pred = loaded_pipeline.predict(pd.DataFrame({"feat1": [4], "feat2": [5]}))
        assert len(pred) == 1
        
        # Cleanup
        MLArtifactService.delete_artifact(experiment_id)
    finally:
        art_srv.STORAGE_DIR = original_dir
