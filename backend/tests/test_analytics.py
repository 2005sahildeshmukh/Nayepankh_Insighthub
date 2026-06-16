import pytest
from fastapi.testclient import TestClient
import pandas as pd
import json

from app.main import app
from app.core.database import get_session

@pytest.fixture
def test_dataset(session):
    from app.models.workspace import Workspace
    from app.models.dataset import Dataset, DatasetColumn
    import uuid
    import os
    
    workspace = Workspace(id=str(uuid.uuid4()), name="Analytics Workspace")
    session.add(workspace)
    session.commit()
    
    dataset = Dataset(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        name="test_analytics_data.csv",
        original_filename="test_analytics_data.csv",
        stored_filename="test_analytics_data.csv",
        file_path=f"data/uploads/{workspace.id}/test_analytics_data.csv",
        file_type="csv",
        file_size_bytes=100,
        row_count=100,
        column_count=5,
        status="ready"
    )
    session.add(dataset)
    session.commit()
    
    # Create the test dataframe
    os.makedirs(f"data/uploads/{workspace.id}", exist_ok=True)
    
    # Data with varying types
    df = pd.DataFrame({
        "volunteer_id": ["V001", "V002", "V003", "V004", "V005"],
        "age": [25, 30, 22, 45, 30],
        "score": [8.5, 9.0, 7.5, 9.5, 8.0],
        "category": ["A", "B", "A", "C", "B"],
        "date_joined": ["2023-01-01", "2023-01-15", "2023-02-01", "2023-02-15", "2023-03-01"],
        "notes": ["good", "ok", "great", "excellent", "good"]
    })
    df.to_csv(dataset.file_path, index=False)
    
    columns = [
        DatasetColumn(dataset_id=dataset.id, original_name="volunteer_id", normalized_name="volunteer_id", inferred_type="string", standard_field="volunteer_id", mapping_status="map", position=0),
        DatasetColumn(dataset_id=dataset.id, original_name="age", normalized_name="age", inferred_type="integer", standard_field="age", mapping_status="map", position=1),
        DatasetColumn(dataset_id=dataset.id, original_name="score", normalized_name="score", inferred_type="float", standard_field="score", mapping_status="keep", position=2),
        DatasetColumn(dataset_id=dataset.id, original_name="category", normalized_name="category", inferred_type="categorical", mapping_status="keep", position=3),
        DatasetColumn(dataset_id=dataset.id, original_name="date_joined", normalized_name="date_joined", inferred_type="datetime", mapping_status="keep", position=4),
        DatasetColumn(dataset_id=dataset.id, original_name="notes", normalized_name="notes", inferred_type="text", mapping_status="exclude", position=5)
    ]
    session.add_all(columns)
    session.commit()
    
    return dataset

@pytest.fixture
def dataset_with_plan(session, test_dataset):
    from app.models.cleaning_plan import DatasetCleaningPlan
    import uuid
    import json
    
    plan = DatasetCleaningPlan(
        id=str(uuid.uuid4()),
        dataset_id=test_dataset.id,
        configuration={"transformations": []}
    )
    session.add(plan)
    session.commit()
    return test_dataset

def test_analytics_metadata(client, test_dataset):
    resp = client.get(f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/metadata?view=mapped")
    if resp.status_code != 200:
        print(resp.json())
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["columns"]) == 5 # Notes is excluded
    
    roles = {c["name"]: c["role"] for c in data["columns"]}
    assert roles["volunteer_id"] == "identifier"
    assert roles["age"] == "integer"
    assert roles["score"] == "float"

def test_mapped_dashboard(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/dashboard",
        json={"view": "mapped", "filters": []}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["overview"]["row_count"] == 5
    assert len(data["kpis"]) >= 1
    
    # Check that age sum works
    kpi_titles = [k["title"] for k in data["kpis"]]
    assert any("Age" in t for t in kpi_titles)
    
    # Verify chart data contract
    if len(data.get("recommended_charts", [])) > 0:
        chart = data["recommended_charts"][0]
        assert "x_key" in chart
        assert "y_key" in chart
        assert chart["x_key"] is not None
        
        # Every data row contains the X key
        for row in chart["data"]:
            assert chart["x_key"] in row
        
        # Every series data key exists and is numeric in at least one row
        for s in chart["series"]:
            assert "dataKey" in s
            has_numeric = any(isinstance(row.get(s["dataKey"]), (int, float)) for row in chart["data"])
            assert has_numeric, f"Series dataKey '{s['dataKey']}' has no valid numeric data"

def test_working_dashboard_without_plan(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/dashboard",
        json={"view": "working", "filters": []}
    )
    assert resp.status_code == 409
    assert "no cleaning plan exists" in resp.json()["detail"].lower()

def test_working_dashboard_with_plan(client, dataset_with_plan):
    resp = client.post(
        f"/api/v1/workspaces/{dataset_with_plan.workspace_id}/datasets/{dataset_with_plan.id}/analytics/dashboard",
        json={"view": "working", "filters": []}
    )
    if resp.status_code != 200:
        print(resp.json())
    assert resp.status_code == 200

def test_numeric_filter(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/dashboard",
        json={
            "view": "mapped", 
            "filters": [{"column": "age", "operator": "gt", "value": 26}]
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filtered_row_count"] == 3 # 30, 45, 30

def test_categorical_filter(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/dashboard",
        json={
            "view": "mapped", 
            "filters": [{"column": "category", "operator": "in", "value": ["A", "B"]}]
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filtered_row_count"] == 4

def test_invalid_filter_operator(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/dashboard",
        json={
            "view": "mapped", 
            "filters": [{"column": "age", "operator": "invalid_op", "value": 26}]
        }
    )
    assert resp.status_code == 422 # Invalid literal for operator

def test_correlation(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/correlation",
        json={"view": "mapped", "filters": []}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "age" in data["included_columns"]
    assert "score" in data["included_columns"]
    assert "volunteer_id" not in data["included_columns"] # Excluded as identifier

def test_custom_bar_chart(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/custom-chart",
        json={"view": "mapped", "chart_type": "bar", "x_column": "category"}
    )
    assert resp.status_code == 200
    data = resp.json()
    chart = data["specification"]
    assert chart["chart_type"] in ["bar", "horizontal_bar"]
    assert chart["x_column"] == "category"
    assert chart["y_column"] == "Record Count"
    assert chart["x_key"] == "x"
    assert chart["y_key"] == "y"
    
    # Verify data shape
    assert len(chart["data"]) == 3
    for row in chart["data"]:
        assert chart["x_key"] in row
        assert "y" in row
        assert isinstance(row["y"], (int, float))

def test_custom_line_chart(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/custom-chart",
        json={"view": "mapped", "chart_type": "line", "x_column": "date_joined", "y_column": "score", "time_granularity": "month"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["specification"]["chart_type"] == "line"

def test_invalid_custom_chart_combo(client, test_dataset):
    # Bar chart requires x_column
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/custom-chart",
        json={"view": "mapped", "chart_type": "bar"}
    )
    assert resp.status_code == 422

def test_workspace_isolation(client, test_dataset, session):
    from app.models.workspace import Workspace
    import uuid
    w2 = Workspace(id=str(uuid.uuid4()), name="W2")
    session.add(w2)
    session.commit()
    
    resp = client.get(f"/api/v1/workspaces/{w2.id}/datasets/{test_dataset.id}/analytics/metadata?view=mapped")
    assert resp.status_code == 404

def test_deterministic_insights_contain_evidence(client, test_dataset):
    resp = client.post(
        f"/api/v1/workspaces/{test_dataset.workspace_id}/datasets/{test_dataset.id}/analytics/dashboard",
        json={"view": "mapped", "filters": []}
    )
    assert resp.status_code == 200
    data = resp.json()
    
    insights = data["insights"]
    assert len(insights) > 0
    for insight in insights:
        assert "id" in insight
        assert "type" in insight
        assert "evidence" in insight
        assert "reliability" in insight
