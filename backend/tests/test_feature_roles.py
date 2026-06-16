import pytest
import pandas as pd
import numpy as np
from app.services.ml.feature_roles import MLFeatureRoleResolver, MLResolvedFeature
from app.services.ml.preprocessing_service import DatetimeFeatureExtractor

def test_resolve_feature_roles():
    df = pd.DataFrame({
        "signup_date": ["2024-01-01", "2024-02-01", "2024-04-01", "2024-03-01"],
        "age": [25, 30, 45, 22],
        "city": ["Mumbai", "Delhi", "Mumbai", "Pune"],
        "is_active": [True, False, True, True],
        "random_date_name": ["a", "b", "c", "d"], # not a date
        "some_id": ["id1", "id2", "id3", "id4"]
    })
    
    selected = ["signup_date", "age", "city", "is_active", "random_date_name", "some_id"]
    resolved = MLFeatureRoleResolver.resolve_roles(df, selected)
    
    roles = {r.name: r.role for r in resolved}
    
    assert roles["signup_date"] == "datetime" # >80% parsed
    assert roles["age"] == "numeric"
    assert roles["city"] == "categorical"
    assert roles["is_active"] == "boolean"
    assert roles["random_date_name"] == "categorical" # date in name but <80% parse
    assert roles["some_id"] == "categorical"

def test_resolve_feature_roles_explicit():
    df = pd.DataFrame({
        "my_col": ["a", "b", "c"]
    })
    resolved = MLFeatureRoleResolver.resolve_roles(df, ["my_col"], explicit_roles={"my_col": "datetime"})
    assert resolved[0].role == "datetime"

def test_datetime_feature_extractor():
    df = pd.DataFrame({
        "dt_col": ["2024-10-15", "2025-01-20", "invalid"]
    })
    
    extractor = DatetimeFeatureExtractor()
    out = extractor.transform(df)
    
    # 2024-10-15 vs 2025-01-20 components
    # row 0: 2024, 10, 15
    # row 1: 2025, 1, 20
    # row 2: -1, -1, -1 (invalid)
    
    assert out.shape == (3, 6) # year, month, day, day_of_week, quarter, is_weekend
    
    # 2024-10-15
    assert out[0, 0] == 2024
    assert out[0, 1] == 10
    assert out[0, 2] == 15
    
    # 2025-01-20
    assert out[1, 0] == 2025
    assert out[1, 1] == 1
    assert out[1, 2] == 20
    
    # invalid
    assert out[2, 0] == -1
    assert out[2, 1] == -1
    assert out[2, 2] == -1

    # Ensure different dates produce different vectors
    assert not np.array_equal(out[0], out[1])
