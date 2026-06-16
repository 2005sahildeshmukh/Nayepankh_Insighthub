import { fetchApi } from '../api-client';

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  dataset_count: number;
}

export interface WorkspaceCreate {
  name: string;
  description?: string;
}

export interface WorkspaceUpdate {
  name?: string;
  description?: string;
}

export const workspacesApi = {
  getWorkspaces: () => fetchApi<Workspace[]>('/workspaces'),
  getWorkspace: (id: string) => fetchApi<Workspace>(`/workspaces/${id}`),
  createWorkspace: (data: WorkspaceCreate) => fetchApi<Workspace>('/workspaces', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateWorkspace: (id: string, data: WorkspaceUpdate) => fetchApi<Workspace>(`/workspaces/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),
  deleteWorkspace: (id: string) => fetchApi<void>(`/workspaces/${id}`, {
    method: 'DELETE',
  }),
};
