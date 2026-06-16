import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.services.ml.ml_service import MLService
from app.services.ml.role_service import MLRoleService
from app.schemas.ml import MLValidateRequest
from app.models.dataset import Dataset, DatasetColumn

@pytest.fixture
def mock_db():
    return MagicMock()

def test_validation_issues_structure():
    # Setup mock data for a classification task with minority class < 5
    df = pd.DataFrame({
        "target": ["A", "A", "A", "A", "B"], # Class B has 1 row
        "feat1": [1, 2, 3, 4, 5]
    })
    
    mock_dataset = Dataset(
        id="ds1",
        workspace_id="ws1",
        columns=[
            DatasetColumn(original_name="target", normalized_name="target", inferred_type="string", mapping_status="text"),
            DatasetColumn(original_name="feat1", normalized_name="feat1", inferred_type="numeric", mapping_status="numeric"),
        ]
    )
    
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = mock_dataset
    
    with patch("app.services.ml.ml_service.get_dataset_dataframe", return_value=df):
        req = MLValidateRequest(
            view="working",
            target_column="target",
            task_type="classification",
            selected_features=["feat1"],
            test_size=0.2
        )
        
        resp = MLService.validate_configuration(mock_db, "ws1", "ds1", req)
        
        # Check issues
        assert resp.can_train is False
        
        issues = [i for i in resp.validation_issues]
        assert len(issues) >= 2 # 1 for <30 rows, 1 for minority class (maybe Unrecommended Task)
        
        codes = [i.code for i in issues]
        assert "INSUFFICIENT_TOTAL_ROWS" in codes
        assert "INSUFFICIENT_CLASS_SIZE" in codes
        
        class_issue = next(i for i in issues if i.code == "INSUFFICIENT_CLASS_SIZE")
        assert class_issue.severity == "error"
        assert class_issue.actual == 1
        assert class_issue.required == 5
        assert class_issue.class_label == "B"
        
        row_issue = next(i for i in issues if i.code == "INSUFFICIENT_TOTAL_ROWS")
        assert row_issue.actual == 5
        assert row_issue.required == 30
        
        # Check target stats
        stats = resp.target_statistics
        assert stats.row_count == 5
        assert stats.class_distribution == {"A": 4, "B": 1}
        assert stats.smallest_class_label == "B"
        assert stats.smallest_class_count == 1
        assert stats.num_classes == 2

def test_regression_does_not_get_class_warning():
    # Setup mock data for a regression task with tiny data
    df = pd.DataFrame({
        "target": [10.0, 11.0, 12.0, 13.0, 14.0],
        "feat1": [1, 2, 3, 4, 5]
    })
    
    mock_dataset = Dataset(
        id="ds1",
        workspace_id="ws1",
        columns=[
            DatasetColumn(original_name="target", normalized_name="target", inferred_type="numeric", mapping_status="numeric"),
            DatasetColumn(original_name="feat1", normalized_name="feat1", inferred_type="numeric", mapping_status="numeric"),
        ]
    )
    
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = mock_dataset
    
    with patch("app.services.ml.ml_service.get_dataset_dataframe", return_value=df):
        req = MLValidateRequest(
            view="working",
            target_column="target",
            task_type="regression",
            selected_features=["feat1"],
            test_size=0.2
        )
        
        resp = MLService.validate_configuration(mock_db, "ws1", "ds1", req)
        
        assert resp.can_train is False
        
        issues = [i for i in resp.validation_issues]
        # Should only have INSUFFICIENT_TOTAL_ROWS (and maybe others, but no CLASS_SIZE)
        codes = [i.code for i in issues]
        assert "INSUFFICIENT_TOTAL_ROWS" in codes
        assert "INSUFFICIENT_CLASS_SIZE" not in codes
        
        # Check target stats
        stats = resp.target_statistics
        assert stats.row_count == 5
        assert stats.min == 10.0
        assert stats.max == 14.0
