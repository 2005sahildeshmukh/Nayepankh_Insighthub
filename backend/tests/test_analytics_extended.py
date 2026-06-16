import pytest
from fastapi.testclient import TestClient
import pandas as pd
import json

from app.main import app
from app.core.database import get_session

@pytest.fixture
def extended_test_dataset(session):
    from app.models.workspace import Workspace
    from app.models.dataset import Dataset, DatasetColumn
    from app.models.cleaning_plan import DatasetCleaningPlan
    import uuid
    import os
    
    workspace = Workspace(id=str(uuid.uuid4()), name="Extended Analytics Workspace")
    session.add(workspace)
    session.commit()
    
    dataset = Dataset(
        id=str(uuid.uuid4()),
        workspace_id=workspace.id,
        name="extended_analytics_data.csv",
        original_filename="extended.csv",
        stored_filename="extended.csv",
        file_path=f"data/uploads/{workspace.id}/extended.csv",
        file_type="csv",
        file_size_bytes=100,
        row_count=100,
        column_count=8,
        status="ready"
    )
    session.add(dataset)
    session.commit()
    
    os.makedirs(f"data/uploads/{workspace.id}", exist_ok=True)
    
    df = pd.DataFrame({
        "volunteer_id": ["V001", "V002", "V003", "V004", "V005"],
        "age": [25, 30, 22, 45, 30],
        "score": [8.5, 9.0, 7.5, 9.5, 8.0],
        "score_constant": [5.0, 5.0, 5.0, 5.0, 5.0],
        "category": ["A", "B", "A", "C", "B"],
        "other_category": ["A", "B", "C", "D", "E"],
        "date_joined": ["2023-01-01", "2023-01-15", "2023-02-01", "2023-02-15", "2023-03-01"],
        "notes": ["good", "ok", "great", "excellent", "good"]
    })
    df.to_csv(dataset.file_path, index=False)
    
    columns = [
        DatasetColumn(dataset_id=dataset.id, original_name="volunteer_id", normalized_name="volunteer_id", inferred_type="string", standard_field="volunteer_id", mapping_status="map", position=0),
        DatasetColumn(dataset_id=dataset.id, original_name="age", normalized_name="age", inferred_type="integer", standard_field="age", mapping_status="map", position=1),
        DatasetColumn(dataset_id=dataset.id, original_name="score", normalized_name="score", inferred_type="float", standard_field="score", mapping_status="keep", position=2),
        DatasetColumn(dataset_id=dataset.id, original_name="score_constant", normalized_name="score_constant", inferred_type="float", mapping_status="keep", position=3),
        DatasetColumn(dataset_id=dataset.id, original_name="category", normalized_name="category", inferred_type="categorical", mapping_status="keep", position=4),
        DatasetColumn(dataset_id=dataset.id, original_name="other_category", normalized_name="other_category", inferred_type="categorical", mapping_status="keep", position=5),
        DatasetColumn(dataset_id=dataset.id, original_name="date_joined", normalized_name="date_joined", inferred_type="datetime", mapping_status="keep", position=6),
        DatasetColumn(dataset_id=dataset.id, original_name="notes", normalized_name="notes", inferred_type="text", mapping_status="exclude", position=7)
    ]
    session.add_all(columns)
    
    plan = DatasetCleaningPlan(
        dataset_id=dataset.id,
        configuration={"steps": []}
    )
    session.add(plan)
    session.commit()
    
    return dataset

@pytest.fixture
def ext_client(session):
    def override_get_session():
        yield session
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_1_mapping_readiness_returns_409(ext_client, session, extended_test_dataset):
    extended_test_dataset.status = "mapped"
    session.commit()
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": []})
    assert response.status_code == 409
    
    extended_test_dataset.status = "ready"
    session.commit()

def test_2_working_view_without_cleaning_plan_returns_409(ext_client, session, extended_test_dataset):
    from app.models.cleaning_plan import DatasetCleaningPlan
    plan = session.query(DatasetCleaningPlan).filter_by(dataset_id=extended_test_dataset.id).first()
    session.delete(plan)
    session.commit()
    
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "working", "filters": []})
    assert response.status_code == 409

def test_3_workspace_isolation_returns_404(ext_client, extended_test_dataset):
    response = ext_client.post(f"/api/v1/workspaces/invalid-workspace/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": []})
    assert response.status_code == 404

def test_4_excluded_columns_absent(ext_client, extended_test_dataset):
    response = ext_client.get(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/metadata?view=mapped")
    data = response.json()
    assert not any(c['name'] == 'notes' for c in data['columns'])

def test_5_identifier_columns_excluded_from_measures(ext_client, extended_test_dataset):
    response = ext_client.get(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/metadata?view=mapped")
    data = response.json()
    vol_id = next(c for c in data['columns'] if c['name'] == 'volunteer_id')
    assert vol_id['role'] == 'identifier'
    assert vol_id['is_identifier_like'] is True

def test_6_kpi_record_count(ext_client, extended_test_dataset):
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": []})
    data = response.json()
    kpi = next(k for k in data['kpis'] if k['id'] == 'kpi_total_records')
    assert kpi['value'] == 5

def test_7_kpi_numeric_sum(ext_client, extended_test_dataset):
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": []})
    data = response.json()
    kpi = next(k for k in data['kpis'] if k['source_column'] == 'age' and k['aggregation'] == 'sum')
    assert kpi['value'] == 152

def test_9_kpi_distinct_count(ext_client, extended_test_dataset):
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": []})
    data = response.json()
    kpi = next((k for k in data['kpis'] if k['source_column'] == 'category' and k['aggregation'] == 'distinct_count'), None)
    if kpi:
        assert kpi['value'] == 3

def test_10_filtered_kpi_values(ext_client, extended_test_dataset):
    filters = [{"column": "category", "operator": "equals", "value": "A"}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    data = response.json()
    kpi_records = next(k for k in data['kpis'] if k['id'] == 'kpi_total_records')
    assert kpi_records['value'] == 2
    kpi_sum = next(k for k in data['kpis'] if k['source_column'] == 'age' and k['aggregation'] == 'sum')
    assert kpi_sum['value'] == 47

def test_14_histogram_bins_and_counts(ext_client, extended_test_dataset):
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": []})
    data = response.json()
    hist = next((c for c in data['recommended_charts'] if c['chart_type'] == 'histogram'), None)
    assert hist is not None
    assert len(hist['data']) > 0
    assert 'bin' in hist['data'][0]
    assert 'count' in hist['data'][0]

def test_18_correlation_values(ext_client, extended_test_dataset):
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/correlation", json={"view": "mapped", "filters": []})
    data = response.json()
    assert 'age' in data['included_columns']
    assert 'score' in data['included_columns']
    assert data['limitation_note'] is not None

def test_19_constant_numeric_column_handling(ext_client, extended_test_dataset):
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/correlation", json={"view": "mapped", "filters": []})
    data = response.json()
    assert 'score_constant' in data['excluded_columns']

def test_27_categorical_equals_filter(ext_client, extended_test_dataset):
    filters = [{"column": "category", "operator": "equals", "value": "A"}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    assert response.json()['filtered_row_count'] == 2

def test_28_categorical_not_equals_filter(ext_client, extended_test_dataset):
    filters = [{"column": "category", "operator": "not_equals", "value": "A"}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    assert response.json()['filtered_row_count'] == 3

def test_29_categorical_in_filter(ext_client, extended_test_dataset):
    filters = [{"column": "category", "operator": "in", "value": ["A", "C"]}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    assert response.json()['filtered_row_count'] == 3

def test_30_numeric_comparison_filters(ext_client, extended_test_dataset):
    filters = [{"column": "age", "operator": "gt", "value": 30}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    assert response.json()['filtered_row_count'] == 1

def test_31_numeric_between_filter(ext_client, extended_test_dataset):
    filters = [{"column": "age", "operator": "between", "value": [25, 30]}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    assert response.json()['filtered_row_count'] == 3

def test_32_date_filters(ext_client, extended_test_dataset):
    filters = [{"column": "date_joined", "operator": "on_or_after", "value": "2023-02-01"}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    assert response.json()['filtered_row_count'] == 3

def test_33_null_filters(ext_client, extended_test_dataset):
    filters = [{"column": "age", "operator": "is_missing"}]
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/dashboard", json={"view": "mapped", "filters": filters})
    assert response.json()['filtered_row_count'] == 0

def test_37_custom_bar_chart(ext_client, extended_test_dataset):
    req = {
        "view": "mapped",
        "filters": [],
        "chart_type": "bar",
        "x_column": "category",
        "y_column": "age",
        "aggregation": "sum"
    }
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/custom-chart", json=req)
    data = response.json()
    assert data['specification']['chart_type'] == 'bar'
    assert len(data['specification']['data']) == 3

def test_42_invalid_chart_combination(ext_client, extended_test_dataset):
    req = {
        "view": "mapped",
        "filters": [],
        "chart_type": "scatter",
        "x_column": "category",
        "y_column": "age"
    }
    response = ext_client.post(f"/api/v1/workspaces/{extended_test_dataset.workspace_id}/datasets/{extended_test_dataset.id}/analytics/custom-chart", json=req)
    assert response.status_code == 422
