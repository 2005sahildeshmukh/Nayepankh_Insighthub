import pytest
import pandas as pd
import numpy as np
from tests.test_data_profiling import create_test_dataset, workspace_with_data

@pytest.fixture
def cleaning_dataset_id(workspace_with_data, session):
    df = pd.DataFrame({
        "A": [" foo ", "", "foo", "foo", "bar", None, "baz"],
        "B": [10, 20, 30, 40, 50, np.nan, 1000],
        "C": [True, False, True, True, False, None, True]
    })
    return create_test_dataset(session, workspace_with_data, df)

def test_default_plan_changes_nothing(client, workspace_with_data, session):
    df = pd.DataFrame({"A": ["a", "b"]})
    did = create_test_dataset(session, workspace_with_data, df)
    config = {
        "version": 1,
        "convert_empty_strings_to_null": False,
        "trim_whitespace": False,
        "remove_exact_duplicates": False,
        "case_rules": [],
        "missing_value_rules": [],
        "outlier_rules": []
    }
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/cleaning/preview", json={"configuration": config})
    assert r.status_code == 200
    assert r.json()["rows_before"] == r.json()["rows_after"] == 2

def test_whitespace_trimming(client, workspace_with_data, cleaning_dataset_id):
    config = {
        "version": 1,
        "trim_whitespace": True,
        "convert_empty_strings_to_null": False,
        "remove_exact_duplicates": False,
        "case_rules": [], "missing_value_rules": [], "outlier_rules": []
    }
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    data = r.json()["preview_data"]
    assert any(row["A"] == "foo" for row in data)
    assert not any(row["A"] == " foo " for row in data)

def test_empty_strings_to_null(client, workspace_with_data, cleaning_dataset_id):
    config = {
        "version": 1,
        "trim_whitespace": False,
        "convert_empty_strings_to_null": True,
        "remove_exact_duplicates": False,
        "case_rules": [], "missing_value_rules": [], "outlier_rules": []
    }
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    # The empty string should be None
    # Original has "" at index 1
    assert r.json()["preview_data"][1]["A"] is None

def test_exact_duplicate_removal(client, workspace_with_data, session):
    df = pd.DataFrame({"A": [1, 1, 2]})
    did = create_test_dataset(session, workspace_with_data, df)
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": True, "case_rules": [], "missing_value_rules": [], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/cleaning/preview", json={"configuration": config})
    assert r.json()["rows_after"] == 2
    assert r.json()["duplicates_removed"] == 1

def test_numeric_mean_filling(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "B", "strategy": "mean"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    data = r.json()["preview_data"]
    # Mean of 10,20,30,40,50,1000 = 1150/6 = 191.66
    assert data[5]["B"] > 190 and data[5]["B"] < 192

def test_numeric_median_filling(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "B", "strategy": "median"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.json()["preview_data"][5]["B"] == 35.0

def test_categorical_mode_filling(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "A", "strategy": "mode"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.json()["preview_data"][5]["A"] == "foo"

def test_custom_text_filling(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "A", "strategy": "custom", "value": "CUSTOM"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.json()["preview_data"][5]["A"] == "CUSTOM"

def test_missing_row_removal(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "B", "strategy": "drop"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.json()["rows_after"] == 6

def test_text_case_normalization(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [{"column": "A", "strategy": "upper"}], "missing_value_rules": [], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.json()["preview_data"][2]["A"] == "FOO"

def test_iqr_capping(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [], "outlier_rules": [{"column": "B", "strategy": "cap_iqr", "iqr_multiplier": 1.5}]}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    # 1000 should be capped
    val = r.json()["preview_data"][6]["B"]
    assert val < 1000

def test_iqr_row_removal(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [], "outlier_rules": [{"column": "B", "strategy": "remove", "iqr_multiplier": 1.5}]}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.json()["rows_after"] == 6

def test_invalid_rule_type_combinations_rejected(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "convert_empty_strings_to_null": False, "trim_whitespace": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "B", "strategy": "bad_strategy"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.status_code == 422 # Pydantic validation

def test_unknown_columns_rejected(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "convert_empty_strings_to_null": False, "trim_whitespace": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "UNKNOWN_COL", "strategy": "mean"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    assert r.status_code == 400

def test_preview_does_not_persist(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "convert_empty_strings_to_null": False, "trim_whitespace": False, "remove_exact_duplicates": True, "case_rules": [], "missing_value_rules": [], "outlier_rules": []}
    client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning/preview", json={"configuration": config})
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning")
    assert not r.json()["has_plan"]

def test_saved_plan_persists(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "convert_empty_strings_to_null": False, "trim_whitespace": False, "remove_exact_duplicates": True, "case_rules": [], "missing_value_rules": [], "outlier_rules": []}
    client.put(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning", json={"configuration": config})
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning")
    assert r.json()["has_plan"]
    assert r.json()["plan"]["configuration"]["remove_exact_duplicates"] == True

def test_reset_restores_mapped_data(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "convert_empty_strings_to_null": False, "trim_whitespace": False, "remove_exact_duplicates": True, "case_rules": [], "missing_value_rules": [], "outlier_rules": []}
    client.put(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning", json={"configuration": config})
    client.delete(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning")
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning")
    assert not r.json()["has_plan"]

def test_original_file_remains_unchanged(client, workspace_with_data, cleaning_dataset_id, session):
    from app.models.dataset import Dataset
    d = session.query(Dataset).filter_by(id=cleaning_dataset_id).first()
    df_original = pd.read_csv(d.file_path)
    config = {"version": 1, "convert_empty_strings_to_null": False, "trim_whitespace": False, "remove_exact_duplicates": True, "case_rules": [], "missing_value_rules": [], "outlier_rules": []}
    client.put(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning", json={"configuration": config})
    df_after = pd.read_csv(d.file_path)
    pd.testing.assert_frame_equal(df_original, df_after)

def test_excluded_columns_remain_excluded(client, workspace_with_data, session):
    from app.models.dataset import DatasetColumn
    df = pd.DataFrame({"A": [1], "B": [2]})
    did = create_test_dataset(session, workspace_with_data, df)
    # manually exclude B
    col = session.query(DatasetColumn).filter_by(dataset_id=did, normalized_name="B").first()
    col.mapping_status = "exclude"
    session.commit()
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/cleaning/preview", json={"configuration": config})
    assert "B" not in r.json()["columns"]

def test_zero_iqr_column_handled_safely(client, workspace_with_data, session):
    df = pd.DataFrame({"A": [1, 1, 1, 1, 1]})
    did = create_test_dataset(session, workspace_with_data, df)
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [], "outlier_rules": [{"column": "A", "strategy": "cap_iqr", "iqr_multiplier": 1.5}]}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/cleaning/preview", json={"configuration": config})
    assert r.status_code == 200

def test_all_null_column_handled_safely(client, workspace_with_data, session):
    df = pd.DataFrame({"A": [np.nan, np.nan]})
    did = create_test_dataset(session, workspace_with_data, df)
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "A", "strategy": "mean"}], "outlier_rules": []}
    r = client.post(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/cleaning/preview", json={"configuration": config})
    assert r.status_code == 200

def test_plan_producing_zero_rows_rejected(client, workspace_with_data, session):
    df = pd.DataFrame({"A": [np.nan]})
    did = create_test_dataset(session, workspace_with_data, df)
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [{"column": "A", "strategy": "drop"}], "outlier_rules": []}
    r = client.put(f"/api/v1/workspaces/{workspace_with_data}/datasets/{did}/cleaning", json={"configuration": config})
    assert r.status_code == 400
    assert "removes all rows" in r.json()["detail"].lower()

def test_dataset_deletion_removes_cleaning_plan(client, workspace_with_data, cleaning_dataset_id):
    config = {"version": 1, "trim_whitespace": False, "convert_empty_strings_to_null": False, "remove_exact_duplicates": False, "case_rules": [], "missing_value_rules": [], "outlier_rules": []}
    client.put(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning", json={"configuration": config})
    client.delete(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}")
    r = client.get(f"/api/v1/workspaces/{workspace_with_data}/datasets/{cleaning_dataset_id}/cleaning")
    assert r.status_code == 404

def test_cross_workspace_cleaning_access_returns_404(client, workspace_with_data, session):
    client.post("/api/v1/workspaces", json={"name": "W2"})
    r2 = client.get("/api/v1/workspaces")
    w2 = next(w["id"] for w in r2.json() if w["name"] == "W2")
    df = pd.DataFrame({"A": [1]})
    did = create_test_dataset(session, workspace_with_data, df)
    r = client.get(f"/api/v1/workspaces/{w2}/datasets/{did}/cleaning")
    assert r.status_code == 404
