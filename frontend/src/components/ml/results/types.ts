export interface MlPredictionSchemaItem {
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
}

export interface MlFeatureImportanceItem {
  feature: string;
  importance: number;
}

export interface MlLeaderboardRow {
  id?: string;
  display_name: string;
  is_baseline: boolean;
  status: string;
  cv_mean: number | null;
  cv_std?: number;
  cv_min?: number;
  cv_max?: number;
  training_time_seconds?: number;
}

export interface MlBaselineComparisonData {
  baselineMetric: number | null;
  candidateMetric: number | null;
  testMetric: number | null;
  primaryMetricName: string;
  direction: 'higher_is_better' | 'lower_is_better';
}

export interface MlClassificationMetrics {
  accuracy?: number;
  balanced_accuracy?: number;
  f1_weighted?: number;
  precision_weighted?: number;
  recall_weighted?: number;
  log_loss?: number;
  roc_auc?: number;
  per_class_metrics?: Record<string, {
    precision: number;
    recall: number;
    f1: number;
    support: number;
  }>;
  confusion_matrix?: {
    labels: string[];
    matrix: number[][];
    normalized_matrix: number[][];
  };
  roc_curve_data?: Array<{
    fpr: number;
    tpr: number;
    threshold?: number;
  }>;
  class_distribution?: Array<{
    label: string;
    count: number;
  }>;
}

export interface MlRegressionMetrics {
  rmse?: number;
  mae?: number;
  r2?: number;
  mse?: number;
  explained_variance?: number;
  max_error?: number;
  median_absolute_error?: number;
  actual_vs_predicted?: Array<{
    actual: number;
    predicted: number;
  }>;
  residuals?: Array<{
    actual: number;
    predicted: number;
    residual: number;
  }>;
  residual_summary?: {
    mean_residual: number;
    std_residual: number;
    min_residual: number;
    max_residual: number;
  };
}

export interface MlModelSummaryData {
  datasetName: string;
  view: string;
  target: string;
  task: string;
  bestModelName: string;
  status: string;
  trainingRowCount?: number;
  testRowCount?: number;
  createdAt: string;
  completedAt?: string;
  artifactAvailable: boolean;
}

export interface MlExperimentViewModel {
  summary: MlModelSummaryData;
  leaderboard: MlLeaderboardRow[];
  baselineComparison: MlBaselineComparisonData;
  testMetrics: MlClassificationMetrics | MlRegressionMetrics;
  baselineMetrics?: MlClassificationMetrics | MlRegressionMetrics;
  featureImportance: MlFeatureImportanceItem[];
  predictionSchema: MlPredictionSchemaItem[];
  isClassification: boolean;
  isRestored: boolean;
  rawEvaluationJson?: Record<string, unknown>;
  legacyPreprocessingWarnings?: Array<{
    code: string;
    feature: string;
    message: string;
  }>;
}
