'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { workspacesApi, Workspace } from '@/lib/api/workspaces';

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  isLoading: boolean;
  error: string | null;
  setActiveWorkspace: (workspaceId: string) => void;
  refreshWorkspaces: () => Promise<Workspace[]>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

const WORKSPACE_STORAGE_KEY = 'nayepankh_active_workspace_id';

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspaceState] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const pathname = usePathname();
  const router = useRouter();



  const setActiveWorkspace = (workspaceId: string) => {
    const workspace = workspaces.find((w) => w.id === workspaceId);
    if (workspace) {
      setActiveWorkspaceState(workspace);
      localStorage.setItem(WORKSPACE_STORAGE_KEY, workspaceId);
      
      // If we are currently in a workspace route, navigate to the new one
      if (pathname.startsWith('/w/')) {
        const segments = pathname.split('/');
        // Assuming format /w/[workspaceId]/...
        if (segments.length >= 3) {
          segments[2] = workspaceId;
          router.push(segments.join('/'));
        }
      } else {
        router.push(`/w/${workspaceId}`);
      }
    }
  };

  const initializeWorkspaces = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const loadedWorkspaces = await workspacesApi.getWorkspaces();
      setWorkspaces(loadedWorkspaces);
      
      if (loadedWorkspaces.length > 0) {
        // 1. Check URL for workspace ID
        const pathSegments = pathname.split('/');
        const urlWorkspaceId = pathSegments[1] === 'w' ? pathSegments[2] : null;

        // 2. Check LocalStorage
        const storedWorkspaceId = localStorage.getItem(WORKSPACE_STORAGE_KEY);

        let selectedWorkspace = null;

        if (urlWorkspaceId) {
          selectedWorkspace = loadedWorkspaces.find(w => w.id === urlWorkspaceId);
          if (!selectedWorkspace) {
            // Invalid workspace URL, fallback to stored or first
            selectedWorkspace = loadedWorkspaces.find(w => w.id === storedWorkspaceId) || loadedWorkspaces[0];
            router.replace(`/w/${selectedWorkspace.id}`);
          }
        } else {
          selectedWorkspace = loadedWorkspaces.find(w => w.id === storedWorkspaceId) || loadedWorkspaces[0];
        }

        if (selectedWorkspace) {
          setActiveWorkspaceState(selectedWorkspace);
          localStorage.setItem(WORKSPACE_STORAGE_KEY, selectedWorkspace.id);
        }
      }
    } catch (err) {
      console.warn('Backend unavailable or failed to load workspaces:', err instanceof Error ? err.message : String(err));
      setError('Unable to connect to the backend server. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    initializeWorkspaces();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const refreshWorkspaces = async () => {
    await initializeWorkspaces();
    return workspaces;
  };

  if (error && workspaces.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
        <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 max-w-md w-full">
          <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Connection Error</h2>
          <p className="text-slate-600 mb-6">{error}</p>
          <button
            onClick={initializeWorkspaces}
            className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        isLoading,
        error,
        setActiveWorkspace,
        refreshWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}
