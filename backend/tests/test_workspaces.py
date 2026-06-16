from fastapi.testclient import TestClient

def test_get_workspaces(client: TestClient):
    # App startup creates the default workspace "NayePankh Foundation"
    response = client.get("/api/v1/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "NayePankh Foundation"
    assert data[0]["dataset_count"] == 0

def test_create_workspace(client: TestClient):
    response = client.post(
        "/api/v1/workspaces",
        json={"name": "Test Workspace", "description": "A test workspace"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Workspace"
    assert data["description"] == "A test workspace"
    assert "id" in data
    assert data["dataset_count"] == 0

def test_create_workspace_trim_name(client: TestClient):
    response = client.post(
        "/api/v1/workspaces",
        json={"name": "  Spaced Name  "}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Spaced Name"

def test_create_workspace_empty_name(client: TestClient):
    response = client.post(
        "/api/v1/workspaces",
        json={"name": "   "}
    )
    assert response.status_code == 422

def test_create_duplicate_workspace_name(client: TestClient):
    # Create first
    client.post("/api/v1/workspaces", json={"name": "Unique Name"})
    # Attempt duplicate
    response = client.post("/api/v1/workspaces", json={"name": "unique name"})
    assert response.status_code == 409

def test_get_workspace(client: TestClient):
    create_resp = client.post("/api/v1/workspaces", json={"name": "Fetch Me"})
    ws_id = create_resp.json()["id"]
    
    response = client.get(f"/api/v1/workspaces/{ws_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Fetch Me"

def test_get_missing_workspace(client: TestClient):
    response = client.get("/api/v1/workspaces/invalid-id")
    assert response.status_code == 404

def test_update_workspace(client: TestClient):
    create_resp = client.post("/api/v1/workspaces", json={"name": "Update Me"})
    ws_id = create_resp.json()["id"]
    
    response = client.patch(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Updated Name", "description": "New description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "New description"

def test_delete_empty_workspace_when_another_exists_succeeds(client: TestClient):
    # Ensure at least two workspaces exist
    create_resp = client.post("/api/v1/workspaces", json={"name": "Delete Me"})
    ws_id = create_resp.json()["id"]
    
    # Workspace being deleted has zero datasets (by default on creation)
    response = client.delete(f"/api/v1/workspaces/{ws_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_resp = client.get(f"/api/v1/workspaces/{ws_id}")
    assert get_resp.status_code == 404

def test_delete_final_empty_workspace_returns_409(client: TestClient):
    # Start with exactly one workspace
    workspaces = client.get("/api/v1/workspaces").json()
    for ws in workspaces[1:]:
        client.delete(f"/api/v1/workspaces/{ws['id']}")
    
    final_ws_id = workspaces[0]["id"]
    # Ensure it has zero datasets
    assert workspaces[0]["dataset_count"] == 0
    
    response = client.delete(f"/api/v1/workspaces/{final_ws_id}")
    assert response.status_code == 409
    assert "The final remaining workspace cannot be deleted." in response.json()["detail"]

def test_delete_workspace_with_dataset_returns_409(client: TestClient):
    from io import BytesIO
    
    # Ensure at least two workspaces exist
    client.post("/api/v1/workspaces", json={"name": "Workspace with dataset"})
    workspaces = client.get("/api/v1/workspaces").json()
    assert len(workspaces) >= 2
    ws_id = workspaces[-1]["id"]
    
    # Upload a dataset into the workspace being deleted
    csv_content = "id,name\n1,Alice\n"
    client.post(
        f"/api/v1/workspaces/{ws_id}/datasets",
        files={"file": ("test.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")}
    )
    
    # DELETE it
    res_del = client.delete(f"/api/v1/workspaces/{ws_id}")
    
    # Expect 409 and specific message
    assert res_del.status_code == 409
    assert "This workspace contains datasets and cannot be deleted." in res_del.json()["detail"]

def test_delete_missing_workspace(client: TestClient):
    response = client.delete("/api/v1/workspaces/non-existent-id")
    assert response.status_code == 404

def test_delete_workspace_after_datasets_deleted(client: TestClient):
    from io import BytesIO
    
    # 1. Create a workspace
    create_resp = client.post("/api/v1/workspaces", json={"name": "To Be Deleted WS"})
    ws_id = create_resp.json()["id"]
    
    # 2. Upload a dataset
    csv_content = "id,name\n1,Alice\n"
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/datasets",
        files={"file": ("test.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")}
    )
    assert res.status_code == 200
    ds_id = res.json()["id"]
    
    # 3. Attempting to delete the workspace should fail (409)
    response_blocked = client.delete(f"/api/v1/workspaces/{ws_id}")
    assert response_blocked.status_code == 409
    
    # 4. Delete the dataset
    del_ds_res = client.delete(f"/api/v1/workspaces/{ws_id}/datasets/{ds_id}")
    assert del_ds_res.status_code == 204
    
    # 5. Deleting the workspace should now succeed
    response_success = client.delete(f"/api/v1/workspaces/{ws_id}")
    assert response_success.status_code == 204
