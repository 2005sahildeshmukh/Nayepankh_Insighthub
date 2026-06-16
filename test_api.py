import httpx
import json

response = httpx.get("http://localhost:8000/api/v1/workspaces")
workspaces = response.json()
if not workspaces:
    print("No workspaces")
    exit()

ws_id = workspaces[0]["id"]
print(f"Workspace: {ws_id}")

response = httpx.get(f"http://localhost:8000/api/v1/workspaces/{ws_id}/datasets")
datasets = response.json()
if not datasets:
    print("No datasets")
    exit()

ds_id = datasets[-1]["id"]
print(f"Dataset: {ds_id}")

payload = {
    "view": "mapped",
    "filters": []
}

try:
    response = httpx.post(f"http://localhost:8000/api/v1/workspaces/{ws_id}/datasets/{ds_id}/analytics/dashboard", json=payload)
    data = response.json()
    print("KPIs:", len(data.get("kpis", [])))
    print("Charts:", len(data.get("recommended_charts", [])))
    for c in data.get("recommended_charts", []):
        print(f"- {c['title']} ({c['chart_type']})")
except Exception as e:
    print("Error", e)
