import math
import pandas as pd
import numpy as np

def sanitize_for_json(obj):
    """
    Recursively purges NaN, Infinity, pd.DataFrame, np.ndarray, and unsupported types
    from dictionaries and lists to ensure valid JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, pd.Series):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict(orient="records"))
    else:
        return obj
