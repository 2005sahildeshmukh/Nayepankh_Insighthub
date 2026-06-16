import { fetchClient } from './fetchClient';

export interface MissingValueRule {
  column: string;
  strategy: 'keep' | 'drop' | 'mean' | 'median' | 'zero' | 'mode' | 'custom' | 'unknown_label' | 'true' | 'false' | 'earliest' | 'latest';
  value?: string | number | boolean | null;
}

export interface CaseRule {
  column: string;
  strategy: 'none' | 'lower' | 'upper' | 'title';
}

export interface OutlierRule {
  column: string;
  strategy: 'keep' | 'cap_iqr' | 'remove';
  iqr_multiplier: number;
}

export interface CleaningConfiguration {
  version: number;
  convert_empty_strings_to_null: boolean;
  trim_whitespace: boolean;
  remove_exact_duplicates: boolean;
  case_rules: CaseRule[];
  missing_value_rules: MissingValueRule[];
  outlier_rules: OutlierRule[];
}

export interface CleaningPlan {
  id?: string;
  dataset_id?: string;
  configuration: CleaningConfiguration;
  created_at?: string;
  updated_at?: string;
}

export interface CleaningPlanResponse {
  has_plan: boolean;
  plan: CleaningPlan;
}

export interface CleaningPreviewRequest {
  configuration: CleaningConfiguration;
}

export interface CleaningPreviewResponse {
  rows_before: number;
  rows_after: number;
  missing_cells_before: number;
  missing_cells_after: number;
  duplicates_removed: number;
  outliers_affected: number;
  warnings: string[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  preview_data: Record<string, any>[];
  columns: string[];
}

export interface CleaningSaveResponse {
  plan: CleaningPlan;
  rows: number;
  columns: number;
  missing_cells: number;
}

export interface WorkingPreviewResponse {
  offset: number;
  limit: number;
  total_rows: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<string, any>[];
  columns: string[];
}

export const cleaningApi = {
  getPlan: async (workspaceId: string, datasetId: string): Promise<CleaningPlanResponse> => {
    return fetchClient(`/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/cleaning`);
  },

  previewPlan: async (workspaceId: string, datasetId: string, config: CleaningConfiguration): Promise<CleaningPreviewResponse> => {
    return fetchClient(`/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/cleaning/preview`, {
      method: 'POST',
      body: JSON.stringify({ configuration: config }),
    });
  },

  savePlan: async (workspaceId: string, datasetId: string, config: CleaningConfiguration): Promise<CleaningSaveResponse> => {
    return fetchClient(`/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/cleaning`, {
      method: 'PUT',
      body: JSON.stringify({ configuration: config }),
    });
  },

  resetPlan: async (workspaceId: string, datasetId: string): Promise<void> => {
    return fetchClient(`/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/cleaning`, {
      method: 'DELETE',
    });
  },

  getWorkingPreview: async (workspaceId: string, datasetId: string, offset = 0, limit = 50): Promise<WorkingPreviewResponse> => {
    return fetchClient(`/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/working-preview?offset=${offset}&limit=${limit}`);
  }
};
