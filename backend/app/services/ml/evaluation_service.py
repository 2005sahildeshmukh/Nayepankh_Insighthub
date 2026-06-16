import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, roc_curve, log_loss,
    mean_absolute_error, mean_squared_error, r2_score, median_absolute_error, mean_absolute_percentage_error
)

try:
    from sklearn.metrics import root_mean_squared_error
except ImportError:
    root_mean_squared_error = None

def calculate_rmse(y_true, y_pred) -> float:
    if root_mean_squared_error is not None:
        value = root_mean_squared_error(y_true, y_pred)
    else:
        value = np.sqrt(mean_squared_error(y_true, y_pred))
    return float(value)

from app.schemas.ml import MLClassificationEvaluation, MLRegressionEvaluation, MLConfusionMatrix, MLClassDistribution

class MLEvaluationService:
    @staticmethod
    def evaluate_classification(pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> MLClassificationEvaluation:
        y_pred = pipeline.predict(X_test)
        
        # Determine labels
        labels = np.unique(np.concatenate([y_test.values, y_pred]))
        labels_str = [str(l) for l in labels]
        
        acc = accuracy_score(y_test, y_pred)
        bal_acc = balanced_accuracy_score(y_test, y_pred)
        
        prec_w = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec_w = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1_w = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        f1_m = f1_score(y_test, y_pred, average='macro', zero_division=0)
        
        cm = confusion_matrix(y_test, y_pred, labels=labels)
        cm_norm = confusion_matrix(y_test, y_pred, labels=labels, normalize='true')
        
        prec_per_class = precision_score(y_test, y_pred, average=None, labels=labels, zero_division=0)
        rec_per_class = recall_score(y_test, y_pred, average=None, labels=labels, zero_division=0)
        f1_per_class = f1_score(y_test, y_pred, average=None, labels=labels, zero_division=0)
        
        # Support
        support = []
        for l in labels:
            support.append((y_test == l).sum())
            
        per_class_metrics = {}
        for i, l in enumerate(labels_str):
            per_class_metrics[l] = {
                "precision": float(prec_per_class[i]),
                "recall": float(rec_per_class[i]),
                "f1": float(f1_per_class[i]),
                "support": int(support[i])
            }
            
        class_dist = []
        for l, count in y_test.value_counts().items():
            class_dist.append(MLClassDistribution(label=str(l), count=int(count)))
            
        # Optional probabilities
        roc_auc = None
        roc_curve_data = None
        ll = None
        if hasattr(pipeline, "predict_proba"):
            try:
                y_prob = pipeline.predict_proba(X_test)
                if len(labels) == 2:
                    # Binary ROC
                    pos_label = labels[1]
                    roc_auc = roc_auc_score(y_test, y_prob[:, 1])
                    fpr, tpr, thresholds = roc_curve(y_test, y_prob[:, 1], pos_label=pos_label)
                    roc_curve_data = [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)][::max(1, len(fpr)//20)]
                ll = log_loss(y_test, y_prob)
            except Exception:
                pass
                
        return MLClassificationEvaluation(
            accuracy=float(acc),
            balanced_accuracy=float(bal_acc),
            precision_weighted=float(prec_w),
            recall_weighted=float(rec_w),
            f1_weighted=float(f1_w),
            f1_macro=float(f1_m),
            per_class_metrics=per_class_metrics,
            confusion_matrix=MLConfusionMatrix(
                labels=labels_str,
                matrix=cm.tolist(),
                normalized_matrix=cm_norm.tolist()
            ),
            roc_auc=float(roc_auc) if roc_auc is not None else None,
            roc_curve_data=roc_curve_data,
            log_loss=float(ll) if ll is not None else None,
            class_distribution=class_dist
        )

    @staticmethod
    def evaluate_regression(pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> MLRegressionEvaluation:
        y_pred = pipeline.predict(X_test)
        
        from sklearn.metrics import explained_variance_score
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = calculate_rmse(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        explained_variance = explained_variance_score(y_test, y_pred)
        medae = median_absolute_error(y_test, y_pred)
        
        try:
            mape = mean_absolute_percentage_error(y_test, y_pred)
        except Exception:
            mape = None
            
        actual_vs_predicted = []
        residuals_list = []
        
        # sample up to 100 points
        sample_size = min(100, len(y_test))
        indices = np.random.choice(len(y_test), sample_size, replace=False)
        
        y_test_arr = y_test.values
        residuals_arr = y_test_arr - y_pred
        
        for i in indices:
            actual_vs_predicted.append({
                "actual": float(y_test_arr[i]),
                "predicted": float(y_pred[i])
            })
            residuals_list.append({
                "predicted": float(y_pred[i]),
                "residual": float(residuals_arr[i])
            })
            
        residual_summary = {
            "mean": float(np.mean(residuals_arr)),
            "std": float(np.std(residuals_arr)),
            "min": float(np.min(residuals_arr)),
            "max": float(np.max(residuals_arr))
        }
        
        target_range = {
            "min": float(np.min(y_test_arr)),
            "max": float(np.max(y_test_arr))
        }
        
        prediction_range = {
            "min": float(np.min(y_pred)),
            "max": float(np.max(y_pred))
        }
        
        return MLRegressionEvaluation(
            mae=float(mae),
            mse=float(mse),
            rmse=float(rmse),
            r2=float(r2),
            explained_variance=float(explained_variance),
            median_absolute_error=float(medae),
            mape=float(mape) if mape is not None else None,
            actual_vs_predicted=actual_vs_predicted,
            residuals=residuals_list,
            residual_summary=residual_summary,
            target_range=target_range,
            prediction_range=prediction_range
        )
