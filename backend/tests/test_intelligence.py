import pytest
import json
from unittest.mock import patch, MagicMock
from sqlmodel import Session
from fastapi.testclient import TestClient
from app.models.workspace import Workspace
from app.models.dataset import Dataset, DatasetColumn
from app.models.ml_experiment import MLExperiment
from app.services.intelligence.context_service import IntelligenceContextBuilder
from app.services.intelligence.gemini_service import GeminiService
from app.schemas.intelligence import CopilotResponse, DecisionsResponse, ReportResponse

@pytest.fixture
def intelligence_test_data(session: Session):
    # Create workspace
    workspace = Workspace(name="Intelligence Workspace")
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
        name="nayepankh_donation_regression_test.csv",
        original_filename="nayepankh_donation_regression_test.csv",
        stored_filename="nayepankh_donation_regression_test.csv",
        file_path="nayepankh_donation_regression_test.csv",
        file_type="csv",
        file_size_bytes=1024,
        row_count=100,
        column_count=4,
        status="ready"
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)

    # Add columns (some sensitive)
    col1 = DatasetColumn(dataset_id=dataset.id, original_name="donor_id", normalized_name="donor_id", position=0, inferred_type="identifier", mapping_status="keep")
    col2 = DatasetColumn(dataset_id=dataset.id, original_name="donor_email", normalized_name="donor_email", position=1, inferred_type="email", mapping_status="keep")
    col3 = DatasetColumn(dataset_id=dataset.id, original_name="monthly_income", normalized_name="monthly_income", position=2, inferred_type="integer", mapping_status="keep")
    col4 = DatasetColumn(dataset_id=dataset.id, original_name="donor_name", normalized_name="donor_name", position=3, inferred_type="text", mapping_status="keep")
    session.add_all([col1, col2, col3, col4])
    session.commit()

    return workspace, workspace2, dataset

def test_context_excludes_sensitive_fields(session: Session, intelligence_test_data):
    workspace, _, dataset = intelligence_test_data
    
    # Mock AnalyticsService dataframe loader to return a dummy df matching columns
    import pandas as pd
    dummy_df = pd.DataFrame({
        "donor_id": [1, 2],
        "donor_email": ["a@b.com", "c@d.com"],
        "monthly_income": [1000, 2000],
        "donor_name": ["Alice", "Bob"]
    })
    
    with patch('app.services.analytics_service.AnalyticsService.get_analytics_dataframe') as mock_df:
        mock_df.return_value = (dummy_df, False)
        with patch('app.services.analytics_service.AnalyticsService.get_column_roles') as mock_roles:
            mock_roles.return_value = {
                "donor_id": {"role": "identifier", "is_identifier_like": True},
                "donor_email": {"role": "text", "is_identifier_like": False},
                "monthly_income": {"role": "integer", "is_identifier_like": False},
                "donor_name": {"role": "text", "is_identifier_like": False}
            }
            
            context = IntelligenceContextBuilder.build_context(session, workspace.id, dataset.id, "mapped")
            
            # Serialize to string and assert no sensitive info is present
            context_str = json.dumps(context)
            
            assert "Alice" not in context_str
            assert "Bob" not in context_str
            assert "a@b.com" not in context_str
            assert "c@d.com" not in context_str
            
            # The column profiles and names themselves must be redacted if checked by sensitive keywords
            assert "Total Monthly Income" in context_str
            assert "[REDACTED]" in context_str



def test_workspace_dataset_isolation(client: TestClient, intelligence_test_data):
    workspace, workspace2, dataset = intelligence_test_data
    
    # Requesting with workspace2 should return 404 since dataset is in workspace
    resp = client.post(
        f"/api/v1/workspaces/{workspace2.id}/intelligence/copilot",
        json={"dataset_id": dataset.id, "view": "mapped", "question": "test"}
    )
    assert resp.status_code == 404

def test_unsupported_view_is_rejected(client: TestClient, intelligence_test_data):
    workspace, _, dataset = intelligence_test_data
    
    # Requesting with view="original" should return 422
    resp = client.post(
        f"/api/v1/workspaces/{workspace.id}/intelligence/copilot",
        json={"dataset_id": dataset.id, "view": "original", "question": "test"}
    )
    assert resp.status_code == 422

def test_missing_api_key_returns_deterministic_fallback(client: TestClient, intelligence_test_data):
    workspace, _, dataset = intelligence_test_data
    
    import pandas as pd
    dummy_df = pd.DataFrame({"monthly_income": [1000, 2000]})
    
    with patch('app.services.analytics_service.AnalyticsService.get_analytics_dataframe') as mock_df:
        mock_df.return_value = (dummy_df, False)
        with patch('app.services.analytics_service.AnalyticsService.get_column_roles') as mock_roles:
            mock_roles.return_value = {"monthly_income": {"role": "integer", "is_identifier_like": False}}
            with patch('app.core.config.settings.GEMINI_API_KEY', None):
                resp = client.post(
                    f"/api/v1/workspaces/{workspace.id}/intelligence/copilot",
                    json={"dataset_id": dataset.id, "view": "mapped", "question": "test"}
                )
                assert resp.status_code == 200
                data = resp.json()
                assert "AI generation is temporarily unavailable" in data["answer"]
                assert len(data["evidence"]) > 0

def test_invalid_gemini_json_returns_deterministic_fallback(client: TestClient, intelligence_test_data):
    workspace, _, dataset = intelligence_test_data
    
    import pandas as pd
    dummy_df = pd.DataFrame({"monthly_income": [1000, 2000]})
    
    with patch('app.services.analytics_service.AnalyticsService.get_analytics_dataframe') as mock_df:
        mock_df.return_value = (dummy_df, False)
        with patch('app.services.analytics_service.AnalyticsService.get_column_roles') as mock_roles:
            mock_roles.return_value = {"monthly_income": {"role": "integer", "is_identifier_like": False}}
            with patch('app.services.intelligence.gemini_service.GeminiService.call_gemini') as mock_call:
                mock_call.side_effect = Exception("Invalid json response")
                with patch('app.core.config.settings.GEMINI_API_KEY', "fake-key"):
                    resp = client.post(
                        f"/api/v1/workspaces/{workspace.id}/intelligence/copilot",
                        json={"dataset_id": dataset.id, "view": "mapped", "question": "test"}
                    )
                    assert resp.status_code == 200
                    data = resp.json()
                    assert "AI generation is temporarily unavailable" in data["answer"]

def test_report_works_without_ml_experiment(client: TestClient, intelligence_test_data):
    workspace, _, dataset = intelligence_test_data
    
    import pandas as pd
    dummy_df = pd.DataFrame({"monthly_income": [1000, 2000]})
    
    with patch('app.services.analytics_service.AnalyticsService.get_analytics_dataframe') as mock_df:
        mock_df.return_value = (dummy_df, False)
        with patch('app.services.analytics_service.AnalyticsService.get_column_roles') as mock_roles:
            mock_roles.return_value = {"monthly_income": {"role": "integer", "is_identifier_like": False}}
            
            # Call report endpoint (no experiment created)
            resp = client.post(
                f"/api/v1/workspaces/{workspace.id}/intelligence/report",
                json={"dataset_id": dataset.id, "view": "mapped"}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "title" in data
            assert len(data["sections"]) > 0
            
            # Check ML section contents
            ml_sect = next(s for s in data["sections"] if s["heading"] == "Machine Learning Results")
            assert "No completed machine-learning experiment" in ml_sect["content"]
