import pytest
from fastapi.testclient import TestClient
import pandas as pd
import json
import uuid
import os

from app.main import app
from app.core.database import get_session

@pytest.fixture
def test_ml_dataset(session):
    from app.models.workspace import Workspace
    from app.models.dataset import Dataset, DatasetColumn
    
    workspace = Workspace(id=str(uuid.uuid4()), name="ML Test Workspace")
    session.add(workspace)
    session.commit()
    
    dataset = Dataset(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        name="ml_test_data.csv",
        original_filename="ml_test_data.csv",
        stored_filename="ml_test_data.csv",
        file_path="ml_test_data.csv",
        file_type="text/csv",
        file_size_bytes=1024,
        row_count=50,
        column_count=4,
        status="mapped"
    )
    session.add(dataset)
    # Create temp CSV
    from app.services.file_storage_service import FileStorageService
    dataset_dir = FileStorageService.get_dataset_dir(workspace.id, dataset.id)
    os.makedirs(dataset_dir, exist_ok=True)
    file_path = os.path.join(dataset_dir, "ml_test_data.csv")
    
    dataset.file_path = file_path
    dataset.file_type = "csv"
    session.commit()
    
    df = pd.DataFrame({
        "volunteer_status": ["Active"]*25 + ["Inactive"]*25,
        "city": ["Mumbai", "Pune", "Thane", "Mumbai", "Pune"] * 10,
        "join_date": ["2023-01-01"] * 50,
        "hours": [10.5] * 50
    })
    
    df.to_csv(file_path, index=False)
    
    # Also write a mapped_data.csv so that working_dataframe view='mapped' does not complain about missing columns if it loads that?
    # Actually, working_dataframe.get_mapped_dataframe calls _load_raw_df(dataset) and then renames using columns. 
    # Let's write the mapped columns to the DB so it works correctly.
    from app.models.dataset import DatasetColumn
    columns = [
        DatasetColumn(dataset_id=dataset.id, original_name="volunteer_status", normalized_name="volunteer_status", position=0, inferred_type="categorical", mapping_status="keep"),
        DatasetColumn(dataset_id=dataset.id, original_name="city", normalized_name="city", position=1, inferred_type="categorical", mapping_status="keep"),
        DatasetColumn(dataset_id=dataset.id, original_name="join_date", normalized_name="join_date", position=2, inferred_type="datetime", mapping_status="keep"),
        DatasetColumn(dataset_id=dataset.id, original_name="hours", normalized_name="hours", position=3, inferred_type="float", mapping_status="keep")
    ]
    session.add_all(columns)
    session.commit()
    
    return workspace, dataset

def test_prediction_output(client, test_ml_dataset):
    workspace, dataset = test_ml_dataset
    
    # Run a classification train experiment
    train_res = client.post(f"/api/v1/workspaces/{workspace.id}/datasets/{dataset.id}/ml/train", json={
        "view": "mapped",
        "target_column": "volunteer_status",
        "task_type": "classification",
        "selected_features": ["city", "join_date", "hours"]
    })
    
    assert train_res.status_code == 200, train_res.text
    exp_id = train_res.json()["id"]
    
    # Verify the prediction_schema has categories for city
    exp_res = client.get(f"/api/v1/workspaces/{workspace.id}/ml/experiments/{exp_id}")
    assert exp_res.status_code == 200
    schema = exp_res.json()["prediction_schema"]
    print("SCHEMA:", schema)
    city_schema = next(s for s in schema if s["name"] == "city")
    assert "categories" in city_schema
    assert isinstance(city_schema["categories"], list)
    assert len(city_schema["categories"]) == 3
    
    # Run a prediction with a valid city
    pred_res = client.post(f"/api/v1/workspaces/{workspace.id}/ml/experiments/{exp_id}/predict", json={
        "features": {
            "city": city_schema["categories"][0],
            "join_date": "2023-01-01",
            "hours": 10.5,
            "volunteer_status": "Active",  # Target column should be rejected
            "fake_field": 100 # Extra field should be rejected
        }
    })
    
    assert pred_res.status_code == 200
    pred = pred_res.json()
    assert "prediction" in pred
    assert "probabilities" in pred
    assert "maximum_probability" in pred
    assert "input_validation_warnings" in pred
    
    warnings = pred["input_validation_warnings"]
    assert any("Target column" in w for w in warnings)
    assert any("fake_field" in w for w in warnings)
    
    # Unknown category warning
    pred_res2 = client.post(f"/api/v1/workspaces/{workspace.id}/ml/experiments/{exp_id}/predict", json={
        "features": {
            "city": "UnknownCityNotSeenBefore",
            "join_date": "2023-01-01",
            "hours": 10.5
        }
    })
    
    warnings2 = pred_res2.json()["input_validation_warnings"]
    assert any("not present in the trained category set" in w for w in warnings2)
    
    # Verify probabilities format and sums
    probs = pred["probabilities"]
    assert isinstance(probs, list)
    total_prob = sum(p["probability"] for p in probs)
    assert 0.99 < total_prob < 1.01
    
    # Check max probability matches prediction
    best_prob = max(probs, key=lambda x: x["probability"])
    assert best_prob["label"] == pred["prediction"]
    assert pred["maximum_probability"] == best_prob["probability"]
    
    # Check low confidence
    if pred["maximum_probability"] < 0.60:
        assert pred["low_confidence"] is True
        assert pred["confidence_message"] is not None
    else:
        assert pred["low_confidence"] is False
