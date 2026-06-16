import pytest
from app.services.ml.ml_service import MLService

class MockPipeline:
    def __init__(self):
        self.classes_ = ["No", "Yes"]
        self.named_steps = {}
        
    def predict(self, df):
        return ["Yes"]
        
    def predict_proba(self, df):
        return [[0.2, 0.8]]

class MockMLArtifactService:
    @staticmethod
    def get_artifact_path(exp_id):
        return f"storage/models/{exp_id}.joblib"
        
    @staticmethod
    def load_pipeline(exp_id):
        return MockPipeline()

class MockExperiment:
    def __init__(self):
        self.id = "test-exp-123"
        self.workspace_id = "test-workspace"
        self.dataset_id = "test-dataset"
        self.status = "completed"
        self.task_type = "classification"
        self.artifact_path = "storage/models/test-exp-123.joblib"
        self.target_column = "churned"
        self.metrics_json = {"accuracy": 0.8}
        self.feature_importance_json = {}
        self.created_at = None
        self.completed_at = None
        self.error_message = None
        self.dataset_view = "working"
        self.selected_features = ["signup_date", "city"]
        self.excluded_features = []
        self.primary_metric = "accuracy"
        self.best_model_name = "RF"
        self.baseline_metric = 0.5
        self.best_cv_metric = 0.8
        self.test_metric = 0.8
        self.row_count = 100
        self.training_row_count = 80
        self.test_row_count = 20
        
        # Test input: signup_date has datetime role but we pretend the pipeline assigned categories 
        self.prediction_schema = [
            {
                "name": "signup_date",
                "display_name": "Signup Date",
                "role": "datetime",
                "type": "str",
                "categories": ["2024-08-09", "2024-08-13"]
            },
            {
                "name": "city",
                "display_name": "City",
                "role": "feature",
                "type": "str",
                "categories": ["Mumbai", "Pune"]
            }
        ]
        

def test_datetime_schema_normalization(monkeypatch):
    monkeypatch.setattr("app.services.ml.ml_service.MLArtifactService", MockMLArtifactService)
    monkeypatch.setattr("os.path.exists", lambda path: True)
    
    exp = MockExperiment()
    
    class MockDB:
        def query(self, *args, **kwargs):
            return self
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return exp

    db = MockDB()
    resp = MLService.get_experiment(db, "test-workspace", "test-exp-123", include_details=True)
    
    assert resp.prediction_schema is not None
    
    # 1. signup_date role is datetime
    # 2. signup_date input type is date
    # 3. signup_date categories are null
    # 4. Datetime role has priority over recovered categories
    signup = next(item for item in resp.prediction_schema if item["name"] == "signup_date")
    assert signup["role"] == "datetime"
    assert signup["input_type"] == "date"
    assert signup["categories"] is None

    # City should still be select
    city = next(item for item in resp.prediction_schema if item["name"] == "city")
    assert city["input_type"] == "select"
    assert city["categories"] == ["Mumbai", "Pune"]


def test_predict_arbitrary_date_no_warning(monkeypatch):
    monkeypatch.setattr("app.services.ml.ml_service.MLArtifactService", MockMLArtifactService)
    
    exp = MockExperiment()
    exp.prediction_schema = [
        {"name": "signup_date", "role": "datetime", "input_type": "date"},
        {"name": "city", "role": "feature", "input_type": "select", "categories": ["Mumbai"]}
    ]
    
    class MockDB:
        def query(self, *args, **kwargs):
            return self
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return exp

    db = MockDB()
    
    features = {
        "signup_date": "2024-10-15",
        "city": "Mumbai"
    }
    
    res = MLService.predict(db, "test-workspace", "test-exp-123", features)
    
    # Arbitrary valid date `2024-10-15` is accepted
    # New valid date does not produce unknown-category warning
    warnings = res["input_validation_warnings"]
    assert len(warnings) == 0
    assert res["prediction"] == "Yes"

def test_predict_unknown_category_warning(monkeypatch):
    monkeypatch.setattr("app.services.ml.ml_service.MLArtifactService", MockMLArtifactService)
    
    exp = MockExperiment()
    exp.prediction_schema = [
        {"name": "city", "role": "feature", "input_type": "select", "categories": ["Mumbai"]}
    ]
    
    class MockDB:
        def query(self, *args, **kwargs):
            return self
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return exp

    db = MockDB()
    
    features = {
        "city": "UnknownCity"
    }
    
    res = MLService.predict(db, "test-workspace", "test-exp-123", features)
    
    warnings = res["input_validation_warnings"]
    assert len(warnings) == 1
    assert "UnknownCity" in warnings[0]

def test_legacy_preprocessing_warning_included(monkeypatch):
    class MockLegacyPipeline:
        def __init__(self):
            self.classes_ = ["No", "Yes"]
            class MockEncoder:
                categories_ = [["2024-01-01", "2024-01-02"]]
            self.named_steps = {"preprocessor": type("MockPrep", (), {"transformers_": [("cat", MockEncoder(), ["signup_date"])]})()}
            
    monkeypatch.setattr("app.services.ml.ml_service.MLArtifactService.load_pipeline", lambda exp_id: MockLegacyPipeline())
    monkeypatch.setattr("app.services.ml.ml_service.MLArtifactService.get_artifact_path", lambda exp_id: "fake/path")
    monkeypatch.setattr("os.path.exists", lambda path: True)
    
    exp = MockExperiment()
    exp.prediction_schema = [
        {"name": "signup_date", "display_name": "Signup Date", "role": "feature", "type": "str", "input_type": "text"}
    ]
    exp.configuration_json = {"preprocessing_manifest": {"datetime_features": []}} # not treated as datetime during training
    
    class MockDB:
        def query(self, *args, **kwargs): return self
        def filter(self, *args, **kwargs): return self
        def first(self): return exp

    db = MockDB()
    resp = MLService.get_experiment(db, "workspace", "exp", include_details=True)
    
    assert len(resp.legacy_preprocessing_warnings) == 1
    assert resp.legacy_preprocessing_warnings[0].code == "DATETIME_ENCODED_AS_CATEGORY"
    assert resp.legacy_preprocessing_warnings[0].feature == "signup_date"

def test_legacy_preprocessing_warning_not_included(monkeypatch):
    class MockCorrectPipeline:
        def __init__(self):
            self.classes_ = ["No", "Yes"]
            self.named_steps = {"preprocessor": type("MockPrep", (), {"transformers_": [("datetime", type("MockDT", (), {})(), ["signup_date"])]})()}
            
    monkeypatch.setattr("app.services.ml.ml_service.MLArtifactService.load_pipeline", lambda exp_id: MockCorrectPipeline())
    monkeypatch.setattr("app.services.ml.ml_service.MLArtifactService.get_artifact_path", lambda exp_id: "fake/path")
    monkeypatch.setattr("os.path.exists", lambda path: True)
    
    exp = MockExperiment()
    exp.prediction_schema = [
        {"name": "signup_date", "display_name": "Signup Date", "role": "datetime", "type": "str", "input_type": "date"}
    ]
    exp.configuration_json = {"preprocessing_manifest": {"datetime_features": ["signup_date"]}}
    
    class MockDB:
        def query(self, *args, **kwargs): return self
        def filter(self, *args, **kwargs): return self
        def first(self): return exp

    db = MockDB()
    resp = MLService.get_experiment(db, "workspace", "exp", include_details=True)
    
    assert len(resp.legacy_preprocessing_warnings) == 0
