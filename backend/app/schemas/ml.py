from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class MLTargetStats(BaseModel):
    row_count: int
    missing_count: int
    unique_count: int
    distribution: Optional[Dict[str, int]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    class_distribution: Optional[Dict[str, int]] = None
    num_classes: Optional[int] = None
    smallest_class_label: Optional[str] = None
    smallest_class_count: Optional[int] = None

class MLValidationIssue(BaseModel):
    code: str
    severity: str
    message: str
    class_label: Optional[str] = None
    actual: Optional[float] = None
    required: Optional[float] = None


class MLTargetCandidate(BaseModel):
    name: str
    display_name: str
    recommended_task: Optional[str] = None
    alternative_task: Optional[str] = None
    reason: Optional[str] = None
    non_null_count: int
    missing_count: int
    unique_count: int
    is_eligible: bool
    exclusion_reason: Optional[str] = None

class MLFeatureRole(BaseModel):
    name: str
    display_name: str
    role: str
    type: str
    feature_status: Literal["recommended", "optional", "excluded"]
    selected_by_default: bool
    reason: str
    warning: Optional[str] = None

class MLTaskRecommendation(BaseModel):
    recommended_task: str
    reason: str
    alternative_task: Optional[str] = None
    can_override: bool = False
    warnings: List[str] = []

class MLMetadataResponse(BaseModel):
    dataset_name: str
    view: str
    has_cleaning_plan: bool
    row_count: int
    target_candidates: List[MLTargetCandidate]
    data_sufficiency_warnings: List[str]

class MLValidateRequest(BaseModel):
    view: Literal["mapped", "working"]
    target_column: str
    task_type: str
    selected_features: Optional[List[str]] = None
    test_size: float = Field(default=0.2)

class MLValidateResponse(BaseModel):
    task_type: str
    included_features: List[str]
    excluded_features: List[str]
    leakage_warnings: List[Dict[str, Any]]
    target_statistics: MLTargetStats
    estimated_training_size: int
    estimated_test_size: int
    validation_warnings: List[str]  # Deprecated
    validation_issues: List[MLValidationIssue] = []
    can_train: bool
    
    # Optional recommendation fields when requested
    recommended_features_meta: Optional[List[MLFeatureRole]] = None
    optional_features_meta: Optional[List[MLFeatureRole]] = None
    excluded_features_meta: Optional[List[MLFeatureRole]] = None
    default_selected_features: Optional[List[str]] = None

class MLTrainRequest(BaseModel):
    view: Literal["mapped", "working"]
    target_column: str
    task_type: str
    selected_features: List[str]
    test_size: float = Field(default=0.2)
    
class MLModelCandidateResult(BaseModel):
    model_id: str
    display_name: str
    is_baseline: bool
    status: str
    cv_mean: Optional[float] = None
    cv_std: Optional[float] = None
    cv_min: Optional[float] = None
    cv_max: Optional[float] = None
    cv_fold_scores: Optional[List[float]] = None
    test_metric: Optional[float] = None
    primary_metric_name: str
    metric_direction: Optional[str] = None
    training_duration_seconds: float
    failure_reason: Optional[str] = None

class MLFeatureImportance(BaseModel):
    feature: str
    original_feature: Optional[str] = None
    importance: float
    rank: int
    direction: Optional[str] = None # positive or negative

class MLPredictionSchemaItem(BaseModel):
    name: str
    display_name: str
    role: str
    input_type: Literal["integer", "decimal", "select", "boolean", "date", "text"]
    required: bool = False
    allows_missing: bool = True
    categories: Optional[List[str]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None

class MLClassDistribution(BaseModel):
    label: str
    count: int

class MLConfusionMatrix(BaseModel):
    labels: List[str]
    matrix: List[List[int]]
    normalized_matrix: List[List[float]]

class MLClassificationEvaluation(BaseModel):
    accuracy: float
    balanced_accuracy: float
    precision_weighted: float
    recall_weighted: float
    f1_weighted: float
    f1_macro: float
    per_class_metrics: Dict[str, Dict[str, float]]
    confusion_matrix: MLConfusionMatrix
    roc_curve_data: Optional[List[Dict[str, float]]] = None
    roc_auc: Optional[float] = None
    log_loss: Optional[float] = None
    class_distribution: List[MLClassDistribution]

class MLRegressionEvaluation(BaseModel):
    mae: float
    mse: float
    rmse: float
    r2: float
    explained_variance: float
    median_absolute_error: Optional[float] = None
    mape: Optional[float] = None
    actual_vs_predicted: Optional[List[Dict[str, Any]]] = None
    residuals: Optional[List[Dict[str, Any]]] = None
    residual_summary: Optional[Dict[str, Any]] = None
    target_range: Optional[Dict[str, float]] = None
    prediction_range: Optional[Dict[str, float]] = None

class MLExperimentSummary(BaseModel):
    id: str
    dataset_id: str
    dataset_name: str
    dataset_view: str
    target_column: str
    task_type: str
    status: str
    best_model_name: Optional[str] = None
    primary_metric: Optional[str] = None
    best_cv_metric: Optional[float] = None
    test_metric: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None
    artifact_available: bool
class LegacyPreprocessingWarning(BaseModel):
    code: str
    feature: str
    message: str


class MLExperimentResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: str
    dataset_view: str
    target_column: str
    task_type: str
    status: str
    
    selected_features: List[str]
    excluded_features: List[str]
    
    primary_metric: Optional[str] = None
    best_model_name: Optional[str] = None
    baseline_metric: Optional[float] = None
    best_cv_metric: Optional[float] = None
    test_metric: Optional[float] = None
    
    candidate_results: Optional[List[MLModelCandidateResult]] = None
    
    classification_evaluation: Optional[MLClassificationEvaluation] = None
    regression_evaluation: Optional[MLRegressionEvaluation] = None
    
    feature_importance: Optional[List[MLFeatureImportance]] = None
    feature_importance_method: Optional[str] = None
    
    prediction_schema: Optional[List[MLPredictionSchemaItem]] = None
    legacy_preprocessing_warnings: List[LegacyPreprocessingWarning] = []
    
    row_count: Optional[int] = None
    training_row_count: Optional[int] = None
    test_row_count: Optional[int] = None
    
    error_message: Optional[str] = None
    warnings: List[str] = []
    
    created_at: str
    completed_at: Optional[str] = None
    artifact_available: bool = False

class MLPredictRequest(BaseModel):
    features: Dict[str, Any]

class MLClassProbability(BaseModel):
    label: str
    probability: float

class MLPredictResponse(BaseModel):
    task_type: str
    prediction: Any
    probabilities: Optional[List[MLClassProbability]] = None
    maximum_probability: Optional[float] = None
    low_confidence: Optional[bool] = False
    confidence_message: Optional[str] = None
    limitation: Optional[str] = "Predicted probabilities are model estimates and are not guarantees."
    input_validation_warnings: List[str] = []
