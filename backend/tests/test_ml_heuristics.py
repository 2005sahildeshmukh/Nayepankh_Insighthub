import pytest
import pandas as pd
from app.services.ml.role_service import MLRoleService
from app.services.ml.ml_service import MLService

def test_participation_hours_infers_regression():
    df = pd.DataFrame({
        'participation_hours': [5.5, 10.0, 2.0, 8.5, 12.0, 6.0],
        'volunteer_status': ['Active', 'Inactive', 'Active', 'Active', 'Inactive', 'Active'],
        'city': ['Mumbai', 'Pune', 'Thane', 'Nashik', 'Mumbai', 'Pune'],
        'join_date': ['2023-01-01', '2023-02-15', '2023-03-10', '2023-04-05', '2023-05-20', '2023-06-30'],
        'id': ['v1', 'v2', 'v3', 'v4', 'v5', 'v6']
    })
    inferred_types = {}
    
    candidates = MLRoleService.get_target_candidates(df, inferred_types)
    hours_cand = next(c for c in candidates if c.name == 'participation_hours')
    
    assert hours_cand.is_eligible == True
    assert hours_cand.recommended_task == 'regression'
    
def test_volunteer_status_infers_classification():
    df = pd.DataFrame({
        'participation_hours': [5.5, 10.0, 2.0, 8.5, 12.0, 6.0],
        'volunteer_status': ['Active', 'Inactive', 'Active', 'Active', 'Inactive', 'Active'],
    })
    inferred_types = {}
    
    candidates = MLRoleService.get_target_candidates(df, inferred_types)
    status_cand = next(c for c in candidates if c.name == 'volunteer_status')
    
    assert status_cand.is_eligible == True
    assert status_cand.recommended_task == 'classification'

def test_low_cardinality_city_string_is_categorical():
    df = pd.DataFrame({
        'participation_hours': [5.5, 10.0, 2.0, 8.5, 12.0],
        'city': ['Mumbai', 'Pune', 'Thane', 'Nashik', 'Mumbai']
    })
    
    features = MLRoleService.get_feature_recommendations(df, 'participation_hours', {})
    city_feat = next(f for f in features if f.name == 'city')
    
    assert city_feat.feature_status == 'recommended'

def test_join_date_detected_as_datetime():
    df = pd.DataFrame({
        'participation_hours': [5.5, 10.0, 2.0, 8.5, 12.0],
        'join_date': ['2023-01-01', '2023-02-15', '2023-03-10', '2023-04-05', '2023-05-20']
    })
    
    features = MLRoleService.get_feature_recommendations(df, 'participation_hours', {})
    date_feat = next(f for f in features if f.name == 'join_date')
    
    assert date_feat.role == 'datetime_feature'
    assert date_feat.feature_status == 'recommended'

def test_target_change_recomputes_recommendations():
    df = pd.DataFrame({
        'participation_hours': [5.5, 10.0, 2.0, 8.5, 12.0],
        'volunteer_status': ['Active', 'Inactive', 'Active', 'Active', 'Inactive'],
        'city': ['Mumbai', 'Pune', 'Thane', 'Nashik', 'Mumbai']
    })
    
    features_1 = MLRoleService.get_feature_recommendations(df, 'participation_hours', {})
    status_feat_1 = next(f for f in features_1 if f.name == 'volunteer_status')
    assert status_feat_1.feature_status == 'recommended'
    
    features_2 = MLRoleService.get_feature_recommendations(df, 'volunteer_status', {})
    hours_feat_2 = next(f for f in features_2 if f.name == 'participation_hours')
    assert hours_feat_2.feature_status == 'recommended'
    status_feat_2 = next((f for f in features_2 if f.name == 'volunteer_status'), None)
    assert status_feat_2.feature_status == 'excluded'

def test_normalize_tokens_internal_notes():
    tokens = MLRoleService._normalize_tokens("Internal Notes")
    assert "internal" in tokens
    assert "notes" in tokens
    assert "notes" in MLRoleService.FREE_TEXT_TOKENS

def test_internal_notes_rejected_as_target():
    df = pd.DataFrame({"Internal Notes": ["A", "B", "C", "D", "E"]})
    candidates = MLRoleService.get_target_candidates(df, {})
    cand = next(c for c in candidates if c.name == "Internal Notes")
    assert cand.is_eligible == False
    assert "Free-text" in cand.exclusion_reason

def test_internal_notes_variations_rejected():
    for name in ["InternalNotes", "internal_notes", "INTERNAL NOTES"]:
        df = pd.DataFrame({name: ["A", "B", "C", "D", "E"]})
        cand = MLRoleService.get_target_candidates(df, {})[0]
        assert cand.is_eligible == False

def test_internal_notes_excluded_as_feature():
    df = pd.DataFrame({"Internal Notes": ["A", "B", "C", "D", "E"], "Participation Hours": [1,2,3,4,5]})
    features = MLRoleService.get_feature_recommendations(df, "Participation Hours", {})
    feat = next(f for f in features if f.name == "Internal Notes")
    assert feat.feature_status == "excluded"
    assert feat.role == "free_text"

def test_volunteer_status_accepted_as_classification():
    for name in ["Volunteer Status", "volunteer_status"]:
        df = pd.DataFrame({name: ["Active", "Inactive", "Active", "Active", "Inactive"]})
        cand = MLRoleService.get_target_candidates(df, {})[0]
        assert cand.is_eligible == True
        assert cand.recommended_task == "classification"

def test_real_target_and_feature_recommendations():
    df = pd.DataFrame({
        "Participation Hours": [5.5, 10.0, 2.0, 8.5, 12.0],
        "Volunteer Status": ["Active", "Inactive", "Active", "Active", "Inactive"],
        "City": ["Mumbai", "Pune", "Thane", "Nashik", "Mumbai"],
        "Internal Notes": ["Great", "Needs work", "Excellent", "Good", "Absent"],
        "Volunteer ID": ["v1", "v2", "v3", "v4", "v5"]
    })
    
    # Target: Participation Hours
    features_1 = MLRoleService.get_feature_recommendations(df, "Participation Hours", {})
    assert next(f for f in features_1 if f.name == "Volunteer Status").feature_status == "recommended"
    assert next(f for f in features_1 if f.name == "City").feature_status == "recommended"
    assert next(f for f in features_1 if f.name == "Internal Notes").feature_status == "excluded"
    assert next(f for f in features_1 if f.name == "Volunteer ID").feature_status == "excluded"
    
    # Target: Volunteer Status
    features_2 = MLRoleService.get_feature_recommendations(df, "Volunteer Status", {})
    assert next(f for f in features_2 if f.name == "Participation Hours").feature_status == "recommended"
    assert next(f for f in features_2 if f.name == "City").feature_status == "recommended"
    assert next(f for f in features_2 if f.name == "Internal Notes").feature_status == "excluded"
