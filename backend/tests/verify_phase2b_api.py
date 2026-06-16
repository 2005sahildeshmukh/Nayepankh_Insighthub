import httpx
import pandas as pd
import time
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app
from fastapi.testclient import TestClient

BASE_URL = "/api/v1"
client = TestClient(app)

import uuid

def create_workspace():
    name = f"Verification Workspace {uuid.uuid4()}"
    r = client.post(f"{BASE_URL}/workspaces", json={"name": name})
    r.raise_for_status()
    return r.json()["id"]

def delete_workspace(wid):
    client.delete(f"{BASE_URL}/workspaces/{wid}")

def run():
    wid = create_workspace()
    try:
        # 1. Upload dataset
        df = pd.DataFrame({
            "num": [1.0, 2.0, None, 100.0, 2.0], # missing, outlier, duplicate
            "text": [" hello", "world ", None, "world ", "world "], # leading/trailing space, missing, duplicate
            "email": ["a@b.com", "invalid", "c@d.com", "c@d.com", "c@d.com"],
            "id_col": [1, 2, 3, 3, 3], # duplicate identifier
            "constant": ["A", "A", "A", "A", "A"] # constant column
        })
        file_obj = io.BytesIO()
        df.to_csv(file_obj, index=False)
        file_obj.seek(0)

        filename = f"dirty_test_{uuid.uuid4()}.csv"
        r = client.post(
            f"{BASE_URL}/workspaces/{wid}/datasets",
            files={"file": (filename, file_obj, "text/csv")}
        )
        if r.status_code != 200:
            print("Upload failed:", r.text)
        r.raise_for_status()
        did = r.json()["id"]
        print(f"Uploaded dataset {did}")
        
        # wait for async parsing to finish
        time.sleep(1)

        # 2. Save mapping
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}")
        r.raise_for_status()
        cols = r.json()["columns"]
        col_map = {c["original_name"]: c["id"] for c in cols}

        mapping_data = {
            "columns": [
                {"id": col_map["num"], "mapping_status": "keep"},
                {"id": col_map["text"], "mapping_status": "keep"},
                {"id": col_map["email"], "mapping_status": "mapped", "standard_field": "email"},
                {"id": col_map["id_col"], "mapping_status": "mapped", "standard_field": "identifier"},
                {"id": col_map["constant"], "mapping_status": "keep"}
            ]
        }
        r = client.put(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/mapping", json=mapping_data)
        r.raise_for_status()
        print("Saved mapping")

        # 3. GET mapped profile
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/profile?source=mapped")
        r.raise_for_status()
        mapped_prof = r.json()
        print("GET mapped profile:", mapped_prof.keys())

        # 4. GET mapped quality
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/quality?source=mapped")
        r.raise_for_status()
        mapped_qual = r.json()
        print("GET mapped quality issues:", len(mapped_qual["issues"]))

        # 5. GET default cleaning plan
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/cleaning")
        r.raise_for_status()
        print("GET default cleaning plan has_plan:", r.json()["has_plan"])

        # 6. POST cleaning preview
        config = {
            "version": 1,
            "convert_empty_strings_to_null": True,
            "trim_whitespace": True,
            "remove_exact_duplicates": True,
            "case_rules": [],
            "missing_value_rules": [{"column": "num", "strategy": "zero"}],
            "outlier_rules": [{"column": "num", "strategy": "cap_iqr", "iqr_multiplier": 1.5}]
        }
        r = client.post(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/cleaning/preview", json={"configuration": config})
        r.raise_for_status()
        preview_res = r.json()
        print("POST cleaning preview: rows after =", preview_res["rows_after"])

        # 7. GET cleaning plan and confirm preview did not persist
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/cleaning")
        r.raise_for_status()
        assert not r.json()["has_plan"], "Preview should not persist!"

        # 8. PUT cleaning plan
        r = client.put(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/cleaning", json={"configuration": config})
        r.raise_for_status()
        print("PUT cleaning plan saved.")

        # 9. GET cleaning plan and confirm persistence
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/cleaning")
        r.raise_for_status()
        assert r.json()["has_plan"], "Plan should persist after PUT!"

        # 10. GET working preview
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/preview?source=working")
        r.raise_for_status()
        working_preview_rows = r.json()
        print("GET working preview count:", len(working_preview_rows))

        # 11. GET working profile
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/profile?source=working")
        r.raise_for_status()
        working_prof = r.json()
        print("GET working profile keys:", working_prof.keys())

        # 12. GET working quality
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/quality?source=working")
        r.raise_for_status()
        working_qual = r.json()
        print("GET working quality issues:", len(working_qual["issues"]))

        # 13. DELETE cleaning plan
        r = client.delete(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/cleaning")
        r.raise_for_status()
        print("DELETED cleaning plan.")

        # 14. Confirm working preview matches mapped data
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/preview?source=working")
        r.raise_for_status()
        reset_working_rows = r.json()
        print("After DELETE working preview count:", len(reset_working_rows))

        # 15. Confirm original preview never changed
        r = client.get(f"{BASE_URL}/workspaces/{wid}/datasets/{did}/preview?source=original")
        r.raise_for_status()
        print("GET original preview count:", len(r.json()))

        # 16. Delete dataset
        r = client.delete(f"{BASE_URL}/workspaces/{wid}/datasets/{did}")
        r.raise_for_status()
        print("Deleted dataset.")

    finally:
        delete_workspace(wid)
        print("Deleted verification workspace.")

if __name__ == "__main__":
    run()
