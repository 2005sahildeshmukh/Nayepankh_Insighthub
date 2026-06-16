export interface DatasetColumn {
  id: string;
  original_name: string;
  normalized_name: string;
  position: number;
  inferred_type: string;
  nullable: boolean;
  unique_count: number | null;
  missing_count: number | null;
  sample_values: unknown[] | null;
  mapping_status: 'mapped' | 'keep' | 'exclude';
  standard_field: string | null;
  custom_display_name: string | null;
}

export interface Dataset {
  id: string;
  workspace_id: string;
  name: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  status: 'uploaded' | 'mapping_pending' | 'ready' | 'failed';
  upload_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface DatasetDetail extends Dataset {
  columns: DatasetColumn[];
}

export interface ColumnMappingUpdate {
  id: string;
  mapping_status: 'mapped' | 'keep' | 'exclude';
  standard_field?: string | null;
  custom_display_name?: string | null;
}

export interface StandardFieldGroup {
  name: string;
  label: string;
  expected_type: string;
  aliases: string[];
}

export interface StandardFieldGroups {
  [group: string]: StandardFieldGroup[];
}

const API_BASE = '/backend-api/api/v1';

export async function getDatasets(workspaceId: string): Promise<Dataset[]> {
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/datasets`);
  if (!res.ok) throw new Error('Failed to fetch datasets');
  return res.json();
}

export async function uploadDataset(workspaceId: string, file: File): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/datasets`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to upload dataset');
  }
  return res.json();
}

export async function getDatasetDetail(workspaceId: string, datasetId: string): Promise<DatasetDetail> {
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/datasets/${datasetId}`);
  if (!res.ok) throw new Error('Failed to fetch dataset details');
  return res.json();
}

export async function deleteDataset(workspaceId: string, datasetId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/datasets/${datasetId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete dataset');
}

export async function getDatasetPreview(workspaceId: string, datasetId: string, limit = 20): Promise<Record<string, unknown>[]> {
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/datasets/${datasetId}/preview?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch preview');
  return res.json();
}

export async function getStandardFields(): Promise<StandardFieldGroups> {
  const res = await fetch(`${API_BASE}/standard-fields`);
  if (!res.ok) throw new Error('Failed to fetch standard fields');
  return res.json();
}

export async function updateMapping(workspaceId: string, datasetId: string, columns: ColumnMappingUpdate[]): Promise<DatasetDetail> {
  const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/datasets/${datasetId}/mapping`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ columns }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to update mapping');
  }
  return res.json();
}
