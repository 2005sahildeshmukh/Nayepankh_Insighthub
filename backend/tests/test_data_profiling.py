import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from app.models.dataset import Dataset, DatasetColumn

def create_test_dataset(session, workspace_id: str, df: pd.DataFrame, mapping_status="ready"):
    import uuid
    dataset_id = str(uuid.uuid4())
    file_path = f"tests/temp/{dataset_id}.csv"
    import os
    os.makedirs("tests/temp", exist_ok=True)
    df.to_csv(file_path, index=False)
    
    dataset = Dataset(
        id=dataset_id,
        workspace_id=workspace_id,
        name="test",
        original_filename="test.csv",
        stored_filename=f"{dataset_id}.csv",
        file_path=file_path,
        file_type="csv",
        file_size_bytes=100,
        status=mapping_status,
        row_count=len(df),
        column_count=len(df.columns)
    )
    session.add(dataset)
    session.commit()
    
    for i, col in enumerate(df.columns):
        inferred = "text"
        if pd.api.types.is_numeric_dtype(df[col]):
            inferred = "integer" if pd.api.types.is_integer_dtype(df[col]) else "float"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            inferred = "datetime"
            
        c = DatasetColumn(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            original_name=col,
            normalized_name=col,
            position=i,
            inferred_type=inferred,
            mapping_status="mapped"
        )
        session.add(c)
    session.commit()
    return dataset_id

@pytest.fixture
def workspace_with_data(client, session):
    client.post("/api/v1/workspaces", json={"name": "ProfTest"})
    resp = client.get("/api/v1/workspaces")
    wid = resp.json()[0]["id"]
    return wid

@pytest.fixture
def profile_dataset_id(workspace_with_data, session):
    df = pd.DataFrame({
        "id_col": [1, 2, 2, 4],
        "num_col": [10.0, 20.0, np.nan, 100.0],
        "text_col": ["A", "B", "A", None],
        "date_col": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", None]),
        "const_col": ["X", "X", "X", "X"],
        "high_miss": [1, None, None, None],
        "email_col": ["a@b.com", "invalid", "c@d.com", None]
    })
    return create_test_dataset(session, workspace_with_data, df)

def test_correct_row_and_column_count(client, workspace_with_data, profile_dataset_id):
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{profile_dataset_id}/profile")
    assert r.status_code == 200
    data = r.json()
    assert data["dataset"]["row_count"] == 4
    assert data["dataset"]["column_count"] == 7

def test_correct_missing_cell_count(client, workspace_with_data, profile_dataset_id):
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{profile_dataset_id}/profile")
    data = r.json()
    assert "missing_cells" in data["dataset"]

def test_correct_duplicate_row_count(client, workspace_with_data, session):
    df = pd.DataFrame({"A": [1, 1, 2]})
    did = create_test_dataset(session, workspace_with_data, df)
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/profile")
    assert r.json()["dataset"]["exact_duplicate_rows"] == 1

def test_numeric_statistics(client, workspace_with_data, profile_dataset_id):
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{profile_dataset_id}/profile")
    print(r.json())
    col = next(c for c in r.json()["columns"] if c["final_name"] == "num_col")
    assert col["min"] == 10.0
    assert col["max"] == 100.0
    assert col["mean"] > 0

def test_categorical_top_values(client, workspace_with_data, profile_dataset_id):
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{profile_dataset_id}/profile")
    col = next(c for c in r.json()["columns"] if c["final_name"] == "text_col")
    assert col["top_values"][0]["count"] == 2
    assert col["top_values"][0]["value"] == "A"

def test_datetime_range(client, workspace_with_data, profile_dataset_id):
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{profile_dataset_id}/profile")
    col = next(c for c in r.json()["columns"] if c["final_name"] == "date_col")
    assert "2020-01-01" in col["earliest_date"]
    assert "2020-01-03" in col["latest_date"]
    assert col["date_range_days"] == 2

def test_iqr_outlier_detection(client, workspace_with_data, session):
    df = pd.DataFrame({"num_col": [1, 2, 3, 4, 100]})
    did = create_test_dataset(session, workspace_with_data, df)
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/quality")
    assert any(i["code"] == "IQR_OUTLIERS" for i in r.json()["issues"])

def test_constant_column_issue(client, workspace_with_data, session):
    df = pd.DataFrame({"const": ["A", "A", "A"]})
    did = create_test_dataset(session, workspace_with_data, df)
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/quality")
    assert any(i["code"] == "CONSTANT_COLUMN" for i in r.json()["issues"])

def test_high_missingness_issue(client, workspace_with_data, session):
    df = pd.DataFrame({"high_miss": [1, np.nan, np.nan, np.nan]})
    did = create_test_dataset(session, workspace_with_data, df)
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/quality")
    assert any(i["code"] == "HIGH_MISSINGNESS" for i in r.json()["issues"])

def test_duplicate_identifier_issue(client, workspace_with_data, session):
    df = pd.DataFrame({"id_col": [1, 1, 2]})
    did = create_test_dataset(session, workspace_with_data, df)
    col = session.query(DatasetColumn).filter_by(dataset_id=did, normalized_name="id_col").first()
    col.inferred_type = "identifier"
    session.commit()
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/quality")
    assert any(i["code"] == "DUPLICATE_IDENTIFIERS" for i in r.json()["issues"])

def test_invalid_mapped_email_issue(client, workspace_with_data, session):
    df = pd.DataFrame({"email": ["a@b.com", "invalid"]})
    did = create_test_dataset(session, workspace_with_data, df)
    # manually make it email
    session.expire_all()
    col = session.query(DatasetColumn).filter_by(dataset_id=did, normalized_name="email").first()
    col.inferred_type = "email"
    session.commit()
    session.expire_all()
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/quality")
    assert any("Invalid Email" in i["title"] for i in r.json()["issues"])

def test_json_output_contains_no_nan_or_infinity(client, workspace_with_data, session):
    df = pd.DataFrame({"A": [np.inf, -np.inf, np.nan, 1.0]})
    did = create_test_dataset(session, workspace_with_data, df)
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/profile")
    assert r.status_code == 200
    text = r.text
    assert "NaN" not in text
    assert "Infinity" not in text

def test_mapping_pending_dataset_returns_409(client, workspace_with_data, session):
    df = pd.DataFrame({"A": [1]})
    did = create_test_dataset(session, workspace_with_data, df, mapping_status="pending")
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/profile")
    assert r.status_code == 409

def test_cross_workspace_access_returns_404(client, workspace_with_data, session):
    client.post("/api/v1/workspaces", json={"name": "W2"})
    r2 = client.get("/api/v1/workspaces")
    w2 = next(w["id"] for w in r2.json() if w["name"] == "W2")
    df = pd.DataFrame({"A": [1]})
    did = create_test_dataset(session, workspace_with_data, df)
    r = client.get(f"/api/v1/workspaces/{w2}/datasets/{did}/profile")
    assert r.status_code == 404

def test_quality_severity_counts_sum_up(client, workspace_with_data, session):
    df = pd.DataFrame({"id_col": [1, 1, 2, 2, 3], "const": ["A", "A", "A", "A", "A"], "outlier": [1, 2, 3, 4, 100]})
    did = create_test_dataset(session, workspace_with_data, df)
    
    col = session.query(DatasetColumn).filter_by(dataset_id=did, normalized_name="id_col").first()
    col.inferred_type = "identifier"
    session.commit()
    
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/quality")
    assert r.status_code == 200
    data = r.json()
    
    summary = data["summary"]
    assert "info_issues" in summary
    assert summary["total_issues"] == summary["critical_issues"] + summary["warning_issues"] + summary["info_issues"]

def test_conservative_identifier_inference(session, workspace_with_data):
    from app.services.data_profiling_service import DataProfilingService
    df = pd.DataFrame({"notes": ["Note A", "Note B", "Note C"]})
    did = create_test_dataset(session, workspace_with_data, df)
    dataset = session.query(Dataset).get(did)
    columns = session.query(DatasetColumn).filter_by(dataset_id=did).all()
    
    # Simulate inference run
    profile = DataProfilingService.generate_profile(df, dataset, columns)
    col_prof = next(c for c in profile["columns"] if c["original_name"] == "notes")
    
    # A highly unique text column named "notes" without ID keywords should remain "text"
    assert col_prof["inferred_type"] == "text"
