import { fetchClient } from './fetchClient';

export interface MlTargetCandidate {
  name: string;
  display_name: string;
  recommended_task: "classification" | "regression" | null;
  alternative_task: "classification" | "regression" | null;
  reason: string | null;
  non_null_count: number;
  missing_count: number;
  unique_count: number;
  is_eligible: boolean;
  exclusion_reason: string | null;
}

export interface MlFeatureRole {
  name: string;
  display_name: string;
  role: string;
  type: string;
  feature_status: "recommended" | "optional" | "excluded";
  selected_by_default: boolean;
  reason: string;
  warning: string | null;
}

export interface MLMetadataResponse {
  dataset_name: string;
  view: "mapped" | "working";
  has_cleaning_plan: boolean;
  row_count: number;
  target_candidates: MlTargetCandidate[];
  data_sufficiency_warnings: string[];
}

export interface MLValidateRequest {
  view: "mapped" | "working";
  target_column: string;
  task_type: "classification" | "regression";
  selected_features: string[] | null;
  test_size: number;
}

export interface MLValidationIssue {
  code: string;
  severity: string;
  message: string;
  class_label?: string;
  actual?: number;
  required?: number;
}

export interface MLValidateResponse {
  can_train: boolean;
  validation_warnings: string[];
  validation_issues: MLValidationIssue[];
  leakage_warnings: Array<{
    feature: string;
    severity: string;
    evidence: string;
    action_taken: string;
    explanation?: string;
  }>;
  target_statistics: {
    row_count: number;
    missing_count: number;
    unique_count: number;
    distribution?: Record<string, number>;
    class_distribution?: Record<string, number>;
    num_classes?: number;
    smallest_class_label?: string;
    smallest_class_count?: number;
    min?: number;
    max?: number;
    mean?: number;
  };
  estimated_training_size: number;
  estimated_test_size: number;
  recommended_features_meta?: MlFeatureRole[];
  optional_features_meta?: MlFeatureRole[];
  excluded_features_meta?: MlFeatureRole[];
  default_selected_features?: string[];
}

export interface MLTrainRequest {
  view: "mapped" | "working";
  target_column: string;
  task_type: "classification" | "regression";
  selected_features: string[];
  test_size: number;
  models: string[];
}

export interface MLModelCandidateResult {
  model_id: string;
  display_name: string;
  is_baseline: boolean;
  status: string;
  cv_mean?: number;
  cv_std?: number;
  cv_min?: number;
  cv_max?: number;
  cv_fold_scores?: number[];
  test_metric?: number;
  primary_metric_name: string;
  metric_direction?: string;
  training_duration_seconds: number;
  failure_reason?: string;
}

export interface MLExperimentSummary {
  id: string;
  dataset_id: string;
  dataset_name: string;
  dataset_view: string;
  target_column: string;
  task_type: string;
  status: string;
  best_model_name?: string;
  primary_metric?: string;
  best_cv_metric?: number;
  test_metric?: number;
  created_at: string;
  completed_at?: string;
  artifact_available: boolean;
}

export interface MLExperimentResponse {
  id: string;
  workspace_id: string;
  dataset_id: string;
  dataset_view: string;
  target_column: string;
  task_type: string;
  status: string;
  selected_features: string[];
  excluded_features: string[];
  primary_metric?: string;
  best_model_name?: string;
  baseline_metric?: number;
  best_cv_metric?: number;
  test_metric?: number;
  candidate_results?: MLModelCandidateResult[];
  classification_evaluation?: Record<string, unknown>;
  regression_evaluation?: Record<string, unknown>;
  feature_importance?: Array<{feature: string, importance: number}>;
  feature_importance_method?: string;
  prediction_schema?: Array<{
    name: string;
    display_name: string;
    role: string;
    input_type: 'integer' | 'decimal' | 'select' | 'boolean' | 'date' | 'text';
    required?: boolean;
    allows_missing?: boolean;
    categories?: string[] | null;
    minimum?: number | null;
    maximum?: number | null;
    step?: number | null;
  }> | null;
  row_count?: number;
  training_row_count?: number;
  test_row_count?: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
  legacy_preprocessing_warnings?: Array<{
    code: string;
    feature: string;
    message: string;
  }>;
  artifact_available: boolean;
}

export interface MLPredictRequest {
  features: Record<string, unknown>;
}

export interface MLClassProbability {
  label: string;
  probability: number;
}

export interface MLPredictResponse {
  task_type: string;
  prediction: unknown;
  probabilities?: MLClassProbability[] | null;
  maximum_probability?: number | null;
  low_confidence?: boolean;
  confidence_message?: string | null;
  limitation?: string;
  input_validation_warnings: string[];
}

function mlDatasetBase(workspaceId: string, datasetId: string): string {
  return `workspaces/${encodeURIComponent(workspaceId)}/datasets/${encodeURIComponent(datasetId)}/ml`;
}

function mlExperimentBase(workspaceId: string, experimentId: string): string {
  return `workspaces/${encodeURIComponent(workspaceId)}/ml/experiments/${encodeURIComponent(experimentId)}`;
}

export const MLService = {
  getMetadata: async (workspaceId: string, datasetId: string, view: string = "original"): Promise<MLMetadataResponse> => {
    return fetchClient(`${mlDatasetBase(workspaceId, datasetId)}/metadata?view=${view}`);
  },

  validateConfig: async (workspaceId: string, datasetId: string, req: MLValidateRequest): Promise<MLValidateResponse> => {
    return fetchClient(`${mlDatasetBase(workspaceId, datasetId)}/validate`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  train: async (workspaceId: string, datasetId: string, req: MLTrainRequest): Promise<MLExperimentResponse> => {
    return fetchClient(`${mlDatasetBase(workspaceId, datasetId)}/train`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  listExperiments: async (workspaceId: string, datasetId?: string): Promise<MLExperimentSummary[]> => {
    let url = `workspaces/${encodeURIComponent(workspaceId)}/ml/experiments`;
    if (datasetId) {
      url += `?dataset_id=${encodeURIComponent(datasetId)}`;
    }
    return fetchClient(url);
  },

  getExperiment: async (workspaceId: string, experimentId: string): Promise<MLExperimentResponse> => {
    return fetchClient(mlExperimentBase(workspaceId, experimentId));
  },

  deleteExperiment: async (workspaceId: string, experimentId: string): Promise<void> => {
    return fetchClient(mlExperimentBase(workspaceId, experimentId), {
      method: 'DELETE',
    });
  },

  predict: async (workspaceId: string, experimentId: string, features: Record<string, unknown>): Promise<MLPredictResponse> => {
    return fetchClient(`${mlExperimentBase(workspaceId, experimentId)}/predict`, {
      method: 'POST',
      body: JSON.stringify({ features }),
    });
  }
};
