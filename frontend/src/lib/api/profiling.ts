import { fetchClient } from './fetchClient';

export interface ColumnProfile {
  original_name: string;
  final_name: string;
  inferred_type: string;
  standard_field: string | null;
  mapping_status: string;
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  unique_percentage: number;
  min?: number | string | null;
  max?: number | string | null;
  mean?: number | null;
  median?: number | null;
  std?: number | null;
  q1?: number | null;
  q3?: number | null;
  iqr?: number | null;
  zero_count?: number;
  negative_count?: number;
  outlier_count?: number;
  outlier_percentage?: number;
  top_values?: { value: string | number; count: number }[];
  most_frequent_value?: string | number | null;
  most_frequent_value_percentage?: number;
  average_text_length?: number | null;
  min_text_length?: number | null;
  max_text_length?: number | null;
  uniqueness_ratio?: number;
  duplicate_identifier_count?: number;
  earliest_date?: string | null;
  latest_date?: string | null;
  date_range_days?: number | null;
  true_count?: number;
  false_count?: number;
}

export interface DatasetProfile {
  generated_at: string;
  view: 'mapped' | 'working';
  has_cleaning_plan: boolean;
  dataset: {
    row_count: number;
    column_count: number;
    total_cells: number;
    missing_cells: number;
    missing_percentage: number;
    complete_rows: number;
    complete_rows_percentage: number;
    exact_duplicate_rows: number;
  };
  columns: ColumnProfile[];
}

export interface QualityIssue {
  code: string;
  severity: 'critical' | 'warning' | 'info';
  column: string | null;
  title: string;
  explanation: string;
  affected_count: number;
  affected_percentage: number;
  suggested_action: string;
}

export interface QualityReport {
  generated_at: string;
  view: 'mapped' | 'working';
  has_cleaning_plan: boolean;
  summary: {
    completeness_percentage: number;
    total_issues: number;
    critical_issues: number;
    warning_issues: number;
    info_issues: number;
    duplicate_rows: number;
  };
  issues: QualityIssue[];
}

export const profilingApi = {
  getProfile: async (workspaceId: string, datasetId: string, view: 'mapped' | 'working' = 'mapped'): Promise<DatasetProfile> => {
    return fetchClient(`/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/profile?view=${view}`);
  },

  getQualityReport: async (workspaceId: string, datasetId: string, view: 'mapped' | 'working' = 'mapped'): Promise<QualityReport> => {
    return fetchClient(`/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/quality?view=${view}`);
  }
};
