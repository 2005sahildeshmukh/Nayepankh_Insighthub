import pytest
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.database import get_session

# Uses client fixture from conftest.py

@pytest.fixture
def mock_dataset(session):
    from app.models.workspace import Workspace
    from app.models.dataset import Dataset
    import os
    
    workspace = Workspace(id=str(uuid.uuid4()), name="ML Routing Test Workspace")
    session.add(workspace)
    session.commit()
    
    dataset = Dataset(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        name="ml_test_data.csv",
        original_filename="ml_test_data.csv",
        stored_filename="ml_test_data.csv",
        file_path=f"data/uploads/{workspace.id}/ml_test_data.csv",
        file_type="csv",
        file_size_bytes=100,
        row_count=100,
        column_count=5,
        status="ready"
    )
    session.add(dataset)
    session.commit()
    
    # Create empty mock file
    os.makedirs(os.path.dirname(dataset.file_path), exist_ok=True)
    with open(dataset.file_path, "w") as f:
        f.write("target,feat1,feat2\n1,2,3\n")
        
    return workspace.id, dataset.id, dataset.file_path

def test_ml_metadata_routing(client, mock_dataset):
    workspace_id, dataset_id, _ = mock_dataset
    
    # We must mock get_mapped_dataframe or get_working_dataframe because of db dependency
    import pandas as pd
    from unittest.mock import patch
    df = pd.DataFrame({"target": [1, 2], "feat1": [2, 3], "feat2": [3, 4]})
    with patch("app.services.ml.ml_service.get_mapped_dataframe", return_value=df):
        # Verify exact path using /api/v1 prefix
        correct_path = f"/api/v1/workspaces/{workspace_id}/datasets/{dataset_id}/ml/metadata"
        response = client.get(f"{correct_path}?view=mapped")
        assert response.status_code == 200, f"Should return 200 for mapped view, got {response.status_code} {response.text}"
        
        # Working view without cleaning plan should return 409
        response_working = client.get(f"{correct_path}?view=working")
        assert response_working.status_code == 409, "Should return 409 when no cleaning plan exists"
        
        # Prefix-less should NOT exist on canonical backend
        incorrect_path = f"/workspaces/{workspace_id}/datasets/{dataset_id}/ml/metadata"
        response_incorrect = client.get(f"{incorrect_path}?view=working")
        assert response_incorrect.status_code == 404, "Prefix-less route should return 404 on FastAPI"

        # Cross-workspace access should return 404
        fake_workspace_id = str(uuid.uuid4())
        cross_path = f"/api/v1/workspaces/{fake_workspace_id}/datasets/{dataset_id}/ml/metadata"
        response_cross = client.get(f"{cross_path}?view=mapped")
        assert response_cross.status_code == 404, "Cross-workspace access must return 404"
