import pytest
from unittest.mock import MagicMock
from app.services.ml.ml_service import MLService
from app.models.ml_experiment import MLExperiment

def test_legacy_schema_normalizes_to_select_and_date():
    # Setup mock DB and experiment
    exp = MLExperiment(
        id="test-exp-1",
        workspace_id="test-workspace",
        dataset_id="test-dataset",
        dataset_view="Working",
        target_column="churn",
        task_type="classification",
        selected_features=["city", "plan_type", "signup_date"],
        excluded_features=[],
        status="completed",
        artifact_path="some_path.joblib",
        prediction_schema=[
            {"name": "city", "display_name": "City", "role": "feature", "type": "str"},
            {"name": "plan_type", "display_name": "Plan Type", "role": "categorical", "input_type": "text"},
            {"name": "signup_date", "display_name": "Signup Date", "role": "feature", "type": "str"}
        ]
    )
    
    class MockEncoder:
        def __init__(self, categories_):
            self.categories_ = categories_
            
    class MockPipeline:
        def __init__(self, named_steps):
            self.named_steps = named_steps
            
    mock_onehot = MockEncoder([["Mumbai", "Pune"], ["Basic", "Standard"]])
    
    mock_cat_transformer = MockPipeline({"onehot": mock_onehot})
    mock_dt_transformer = MockPipeline({})
    
    mock_preprocessor = MagicMock()
    mock_preprocessor.transformers_ = [
        ("cat", mock_cat_transformer, ["city", "plan_type"]),
        ("dt", mock_dt_transformer, ["signup_date"])
    ]
    
    mock_pipeline = MockPipeline({"preprocessor": mock_preprocessor})
    
    # Mock MLArtifactService.load_pipeline
    with pytest.MonkeyPatch.context() as m:
        from app.services.ml.artifact_service import MLArtifactService
        import os
        m.setattr(MLArtifactService, "load_pipeline", lambda x: mock_pipeline)
        m.setattr(MLArtifactService, "get_artifact_path", lambda x: "some_path.joblib")
        m.setattr(os.path, "exists", lambda x: True)
        
        db = MagicMock()
        db.query().filter().first.return_value = exp
        
        try:
            res = MLService.get_experiment(db, "test-workspace", "test-exp-1", include_details=True)
        except Exception as e:
            print("Error:", e)
            raise
        
        schemas = {s["name"]: s for s in res.prediction_schema}
        
        print("ACTUAL SCHEMAS:", schemas)
        
        assert schemas["city"]["input_type"] == "select"
        assert schemas["city"]["categories"] == ["Mumbai", "Pune"]
        
        assert schemas["plan_type"]["input_type"] == "select"
        assert schemas["plan_type"]["categories"] == ["Basic", "Standard"]
        
        assert schemas["signup_date"]["input_type"] == "date"
