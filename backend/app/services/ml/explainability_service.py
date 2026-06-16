import numpy as np
import pandas as pd
from typing import List
from app.schemas.ml import MLFeatureImportance

class MLExplainabilityService:
    @staticmethod
    def extract_feature_importances(pipeline, task_type: str) -> tuple[List[MLFeatureImportance], str]:
        """
        Extracts feature importances safely from the pipeline.
        Returns a tuple of (importances, method).
        """
        preprocessor = pipeline.named_steps['preprocessor']
        estimator = pipeline.steps[-1][1]
        
        # Get feature names from preprocessor if possible
        try:
            feature_names = preprocessor.get_feature_names_out()
        except Exception:
            # Cannot get feature names easily
            return [], "none"
            
        importances_arr = None
        method = "none"
        directions = None
        
        if hasattr(estimator, 'feature_importances_'):
            importances_arr = estimator.feature_importances_
            method = "Tree Impurity"
        elif hasattr(estimator, 'coef_'):
            coefs = estimator.coef_
            if task_type == "classification" and coefs.ndim > 1 and coefs.shape[0] > 1:
                # Multiclass linear: sum of absolute coefficients across classes
                importances_arr = np.sum(np.abs(coefs), axis=0)
                method = "Linear Coefficients (Multiclass abs sum)"
            else:
                coef_flat = coefs.flatten()
                importances_arr = np.abs(coef_flat)
                directions = ["positive" if c > 0 else "negative" for c in coef_flat]
                method = "Linear Coefficients (Magnitude)"
                
        if importances_arr is None:
            return [], "none"
            
        # Ensure lengths match
        if len(feature_names) != len(importances_arr):
            return [], "none"
            
        feature_importances = []
        for i, name in enumerate(feature_names):
            # Clean up the preprocessor prefixes if they exist (e.g. 'num__Age' -> 'Age')
            display_name = str(name)
            if '__' in display_name:
                display_name = display_name.split('__', 1)[1]
                
            imp = float(importances_arr[i])
            if np.isnan(imp) or np.isinf(imp):
                imp = 0.0
                
            direction = directions[i] if directions else None
            
            feature_importances.append(MLFeatureImportance(
                feature=display_name,
                original_feature=display_name,
                importance=imp,
                rank=0,
                direction=direction
            ))
            
        # Sort and rank
        feature_importances.sort(key=lambda x: x.importance, reverse=True)
        
        # Limit to top 20
        feature_importances = feature_importances[:20]
        
        for i, item in enumerate(feature_importances):
            item.rank = i + 1
            
        return feature_importances, method
