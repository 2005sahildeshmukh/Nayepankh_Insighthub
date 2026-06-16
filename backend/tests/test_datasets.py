import pytest
from fastapi.testclient import TestClient
from app.models.dataset import Dataset
import pandas as pd
from io import BytesIO

def test_list_datasets_empty(client: TestClient, session):
    ws_res = client.get("/api/v1/workspaces").json()
    ws_id = ws_res[0]["id"]
    res = client.get(f"/api/v1/workspaces/{ws_id}/datasets")
    assert res.status_code == 200
    assert len(res.json()) == 0

def test_upload_invalid_extension(client: TestClient):
    ws_res = client.get("/api/v1/workspaces").json()
    ws_id = ws_res[0]["id"]
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/datasets",
        files={"file": ("test.txt", b"some data", "text/plain")}
    )
    assert res.status_code == 400
    assert "Only CSV and XLSX" in res.json()["detail"]

def create_test_csv(content: str) -> BytesIO:
    return BytesIO(content.encode("utf-8"))

def test_upload_valid_csv_and_inspect(client: TestClient, session):
    ws_res = client.get("/api/v1/workspaces").json()
    ws_id = ws_res[0]["id"]
    
    csv_content = "id,name,email,score\n1,Alice,alice@a.com,9.5\n2,Bob,bob@b.com,8.0\n"
    file_obj = create_test_csv(csv_content)
    
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/datasets",
        files={"file": ("test.csv", file_obj, "text/csv")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "mapping_pending"
    assert data["row_count"] == 2
    assert data["column_count"] == 4
    
    # Check details and mapping
    ds_id = data["id"]
    res_det = client.get(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}")
    det = res_det.json()
    cols = det["columns"]
    assert len(cols) == 4
    
    col_names = {c["original_name"]: c for c in cols}
    assert col_names["id"]["mapping_status"] == "keep"
    assert col_names["id"]["standard_field"] == "volunteer_id"
    
    assert col_names["name"]["mapping_status"] == "keep" # name is in AMBIGUOUS_TERMS
    assert col_names["score"]["mapping_status"] == "keep" # ambiguous
    assert col_names["email"]["mapping_status"] == "mapped"
    assert col_names["email"]["standard_field"] == "email"



def test_dataset_deletion_cascades(client: TestClient, session):
    ws_res = client.get("/api/v1/workspaces").json()
    ws_id = ws_res[0]["id"]
    csv_content = "id,name\n1,Alice\n"
    res = client.post(f"/api/v1/workspaces/{ws_id}/datasets", files={"file": ("test2.csv", create_test_csv(csv_content), "text/csv")})
    ds_id = res.json()["id"]
    
    del_res = client.delete(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}")
    assert del_res.status_code == 204
    
    get_res = client.get(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}")
    assert get_res.status_code == 404

def test_mapping_update_duplicate_rejection(client: TestClient, session):
    ws_res = client.get("/api/v1/workspaces").json()
    ws_id = ws_res[0]["id"]
    csv_content = "col1,col2\nval1,val2\n"
    res = client.post(f"/api/v1/workspaces/{ws_id}/datasets", files={"file": ("test3.csv", create_test_csv(csv_content), "text/csv")})
    ds_id = res.json()["id"]
    
    cols = client.get(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}").json()["columns"]
    updates = [
        {"id": cols[0]["id"], "mapping_status": "mapped", "standard_field": "full_name"},
        {"id": cols[1]["id"], "mapping_status": "keep", "custom_display_name": "full_name"}
    ]
    
    put_res = client.put(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}/mapping", json={"columns": updates})
    assert put_res.status_code == 400
    assert "Duplicate final output column names" in put_res.json()["detail"]

def test_get_working_dataframe(client: TestClient, session):
    ws_res = client.get("/api/v1/workspaces").json()
    ws_id = ws_res[0]["id"]
    csv_content = "ignored,raw_email\n1,a@a.com\n"
    res = client.post(f"/api/v1/workspaces/{ws_id}/datasets", files={"file": ("test4.csv", create_test_csv(csv_content), "text/csv")})
    ds_id = res.json()["id"]
    
    cols = client.get(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}").json()["columns"]
    updates = [
        {"id": [c["id"] for c in cols if c["original_name"] == "ignored"][0], "mapping_status": "exclude"},
        {"id": [c["id"] for c in cols if c["original_name"] == "raw_email"][0], "mapping_status": "mapped", "standard_field": "email"}
    ]
    client.put(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}/mapping", json={"columns": updates})
    
    from app.utils.working_dataframe import get_working_dataframe
    df = get_working_dataframe(ds_id, session)
    
    assert list(df.columns) == ["email"]
    assert len(df) == 1
    assert df.iloc[0]["email"] == "a@a.com"
