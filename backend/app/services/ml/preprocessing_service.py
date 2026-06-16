import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.base import BaseEstimator, TransformerMixin

class DatetimeFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_copy = X.copy()
        if isinstance(X_copy, pd.DataFrame):
            df = X_copy
        else:
            df = pd.DataFrame(X_copy)

        out_df = pd.DataFrame(index=df.index)
        for col in df.columns:
            series = pd.to_datetime(df[col], errors='coerce')
            out_df[f"{col}_year"] = series.dt.year.fillna(-1).astype(int)
            out_df[f"{col}_month"] = series.dt.month.fillna(-1).astype(int)
            out_df[f"{col}_day"] = series.dt.day.fillna(-1).astype(int)
            out_df[f"{col}_day_of_week"] = series.dt.dayofweek.fillna(-1).astype(int)
            out_df[f"{col}_quarter"] = series.dt.quarter.fillna(-1).astype(int)
            out_df[f"{col}_is_weekend"] = series.dt.dayofweek.isin([5, 6]).astype(int)
            # if series is NaT, isin([5,6]) is False. So is_weekend is 0 for NaT. We could leave it as 0.
            
        return out_df.values

    def get_feature_names_out(self, input_features=None):
        if input_features is None:
            return None
        names = []
        for col in input_features:
            names.extend([f"{col}_year", f"{col}_month", f"{col}_day", f"{col}_day_of_week", f"{col}_quarter", f"{col}_is_weekend"])
        return np.array(names)

class SafeBooleanTransformer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if isinstance(X, pd.DataFrame):
            arr = X.values
        else:
            arr = np.array(X)
        
        # safely convert to float, True -> 1.0, False -> 0.0, else NaN
        # then fillna with 0.0 or a specific value. We will use SimpleImputer downstream.
        out = []
        for row in arr:
            new_row = []
            for val in row:
                if pd.isna(val):
                    new_row.append(np.nan)
                elif isinstance(val, bool):
                    new_row.append(1.0 if val else 0.0)
                elif isinstance(val, str):
                    lower_val = val.lower().strip()
                    if lower_val in ['true', 'yes', '1', 't', 'y']:
                        new_row.append(1.0)
                    elif lower_val in ['false', 'no', '0', 'f', 'n']:
                        new_row.append(0.0)
                    else:
                        new_row.append(np.nan)
                else:
                    try:
                        fval = float(val)
                        new_row.append(1.0 if fval > 0 else 0.0)
                    except:
                        new_row.append(np.nan)
            out.append(new_row)
        return np.array(out, dtype=float)

    def get_feature_names_out(self, input_features=None):
        return input_features

class MLPreprocessingService:
    @staticmethod
    def build_preprocessor(resolved_features: list['MLResolvedFeature'], scale: bool = True) -> ColumnTransformer:
        """
        Builds a scikit-learn ColumnTransformer based on the explicit resolved roles.
        """
        numeric_features = []
        categorical_features = []
        boolean_features = []
        datetime_features = []
        excluded_features = []
        
        for feature in resolved_features:
            if feature.role == "numeric":
                numeric_features.append(feature.name)
            elif feature.role == "categorical":
                categorical_features.append(feature.name)
            elif feature.role == "boolean":
                boolean_features.append(feature.name)
            elif feature.role == "datetime":
                datetime_features.append(feature.name)
            else:
                excluded_features.append(feature.name)
                
        # Mutually exclusive groups assert
        assigned = (
            set(numeric_features)
            | set(categorical_features)
            | set(boolean_features)
            | set(datetime_features)
            | set(excluded_features)
        )
        assert assigned == set([f.name for f in resolved_features]), "Not all features were accounted for!"
        
        trainable = (
            set(numeric_features)
            | set(categorical_features)
            | set(boolean_features)
            | set(datetime_features)
        )
        assert len(trainable) == (
            len(numeric_features)
            + len(categorical_features)
            + len(boolean_features)
            + len(datetime_features)
        ), "Features overlap in preprocessing groups!"

        transformers = []

        if numeric_features:
            steps = [('imputer', SimpleImputer(strategy='median'))]
            if scale:
                steps.append(('scaler', StandardScaler()))
            numeric_transformer = Pipeline(steps=steps)
            transformers.append(('num', numeric_transformer, numeric_features))

        if categorical_features:
            # We use handle_unknown='ignore'
            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=True, min_frequency=0.01))
            ])
            transformers.append(('cat', categorical_transformer, categorical_features))

        if boolean_features:
            boolean_transformer = Pipeline(steps=[
                ('safe_bool', SafeBooleanTransformer()),
                ('imputer', SimpleImputer(strategy='most_frequent'))
            ])
            transformers.append(('bool', boolean_transformer, boolean_features))

        if datetime_features:
            steps = [
                ('dt_extract', DatetimeFeatureExtractor()),
                ('imputer', SimpleImputer(strategy='median'))
            ]
            if scale:
                steps.append(('scaler', StandardScaler()))
            dt_transformer = Pipeline(steps=steps)
            transformers.append(('dt', dt_transformer, datetime_features))

        preprocessor = ColumnTransformer(transformers=transformers, remainder='drop')
        return preprocessor
