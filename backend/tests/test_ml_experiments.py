import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models.workspace import Workspace
from app.models.dataset import Dataset
from app.models.ml_experiment import MLExperiment
from app.main import app

@pytest.fixture
def experiment_test_data(session: Session):
    # Create workspace
    workspace = Workspace(name="Test Workspace")
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    workspace2 = Workspace(name="Other Workspace")
    session.add(workspace2)
    session.commit()
    session.refresh(workspace2)

    # Create dataset
    dataset = Dataset(
        workspace_id=workspace.id,
        name="test.csv",
        original_filename="test.csv",
        stored_filename="test.csv",
        file_path="test.csv",
        file_type="csv",
        file_size_bytes=1024,
        row_count=100,
        column_count=10,
        status="mapped"
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)

    # Create experiment
    exp = MLExperiment(
        workspace_id=workspace.id,
        dataset_id=dataset.id,
        dataset_view="mapped",
        target_column="target",
        task_type="classification",
        selected_features=["f1", "f2"],
        excluded_features=[],
        status="completed",
        primary_metric="f1",
        best_model_name="Random Forest",
        best_cv_metric="0.9",
        test_metric="0.85",
        metrics_json={"accuracy": 0.85},
        feature_importance_json=[{"feature": "f1", "importance": 0.8}, {"feature": "f2", "importance": 0.2}],
        prediction_schema=[{"name": "f1", "type": "int"}, {"name": "f2", "type": "float"}]
    )
    session.add(exp)
    session.commit()
    session.refresh(exp)

    return workspace.id, workspace2.id, dataset.id, exp.id

def test_list_experiments(client, experiment_test_data):
    w1_id, w2_id, ds_id, exp_id = experiment_test_data

    # List experiments for w1
    response = client.get(f"/api/v1/workspaces/{w1_id}/ml/experiments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == exp_id
    assert data[0]["dataset_name"] == "test.csv"
    assert data[0]["artifact_available"] == False
    assert "artifact_path" not in data[0]

    # List experiments for w2
    response2 = client.get(f"/api/v1/workspaces/{w2_id}/ml/experiments")
    assert response2.status_code == 200
    assert len(response2.json()) == 0

def test_get_experiment(client, experiment_test_data):
    w1_id, w2_id, ds_id, exp_id = experiment_test_data

    response = client.get(f"/api/v1/workspaces/{w1_id}/ml/experiments/{exp_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exp_id
    assert data["status"] == "completed"
    assert data["classification_evaluation"] == {"accuracy": 0.85}
    assert len(data["prediction_schema"]) == 2
    assert data["prediction_schema"][0]["name"] == "f1"
    assert data["prediction_schema"][0]["input_type"] == "integer"
    assert data["prediction_schema"][1]["name"] == "f2"
    assert data["prediction_schema"][1]["input_type"] == "decimal"
    assert data["artifact_available"] == False

    # Get from wrong workspace
    response2 = client.get(f"/api/v1/workspaces/{w2_id}/ml/experiments/{exp_id}")
    assert response2.status_code == 404

def test_delete_experiment(client, experiment_test_data):
    w1_id, w2_id, ds_id, exp_id = experiment_test_data

    response = client.delete(f"/api/v1/workspaces/{w1_id}/ml/experiments/{exp_id}")
    assert response.status_code == 200

    # Ensure it's deleted
    response2 = client.get(f"/api/v1/workspaces/{w1_id}/ml/experiments/{exp_id}")
    assert response2.status_code == 404
