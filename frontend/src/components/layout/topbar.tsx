'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useWorkspace } from '@/providers/workspace-provider';
import { ChevronDown, Plus, Settings as SettingsIcon, X, AlertCircle } from 'lucide-react';
import { workspacesApi, Workspace } from '@/lib/api/workspaces';

export function Topbar() {
  const { activeWorkspace, workspaces, setActiveWorkspace, refreshWorkspaces, isLoading } = useWorkspace();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center">
        {!isLoading && activeWorkspace && (
          <div className="relative" ref={dropdownRef}>
            <button 
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center text-sm font-medium text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 px-3 py-2 rounded-md transition-colors border border-slate-200"
            >
              {activeWorkspace.name}
              <ChevronDown className="ml-2 h-4 w-4 text-slate-400" />
            </button>
            
            {isDropdownOpen && (
              <div className="absolute left-0 mt-1 w-64 bg-white border border-slate-200 rounded-md shadow-lg transition-all duration-200 z-20">
                <div className="p-2">
                  <p className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Switch Workspace</p>
                  <div className="space-y-1 max-h-64 overflow-y-auto">
                    {workspaces.map((ws) => (
                      <button
                        key={ws.id}
                        onClick={() => {
                          setActiveWorkspace(ws.id);
                          setIsDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                          activeWorkspace.id === ws.id
                            ? 'bg-blue-50 text-blue-700 font-medium'
                            : 'text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        {ws.name}
                      </button>
                    ))}
                  </div>
                  
                  <div className="border-t border-slate-200 mt-2 pt-2">
                    <button 
                      onClick={() => { setIsCreateOpen(true); setIsDropdownOpen(false); }}
                      className="w-full flex items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md transition-colors"
                    >
                      <Plus className="mr-2 h-4 w-4 text-slate-400" />
                      Create New Workspace
                    </button>
                    <button 
                      onClick={() => { setIsSettingsOpen(true); setIsDropdownOpen(false); }}
                      className="w-full flex items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md transition-colors"
                    >
                      <SettingsIcon className="mr-2 h-4 w-4 text-slate-400" />
                      Workspace Settings
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      {/* Create Modal */}
      {isCreateOpen && (
        <CreateWorkspaceModal 
          onClose={() => setIsCreateOpen(false)} 
          onSuccess={(id) => {
            setIsCreateOpen(false);
            refreshWorkspaces().then(() => setActiveWorkspace(id));
          }} 
          workspaces={workspaces}
        />
      )}

      {/* Settings Modal */}
      {isSettingsOpen && activeWorkspace && (
        <SettingsWorkspaceModal 
          workspace={activeWorkspace} 
          workspaces={workspaces}
          onClose={() => setIsSettingsOpen(false)} 
          onSuccess={() => {
            refreshWorkspaces();
          }}
          onDelete={() => {
            setIsSettingsOpen(false);
            refreshWorkspaces().then((updatedList) => {
              if (updatedList.length > 0) setActiveWorkspace(updatedList[0].id);
            });
          }}
        />
      )}
    </header>
  );
}

function CreateWorkspaceModal({ onClose, onSuccess, workspaces }: { onClose: () => void, onSuccess: (id: string) => void, workspaces: Workspace[] }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Workspace name is required');
      return;
    }
    if (workspaces.some(w => w.name.toLowerCase() === name.trim().toLowerCase())) {
      setError('A workspace with this name already exists');
      return;
    }
    
    setIsSubmitting(true);
    try {
      const newWs = await workspacesApi.createWorkspace({ name: name.trim(), description: description.trim() });
      onSuccess(newWs.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workspace');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-slate-200">
          <h3 className="font-bold text-lg text-slate-900">Create Workspace</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm flex items-start"><AlertCircle className="w-4 h-4 mr-2 mt-0.5 shrink-0"/>{error}</div>}
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
            <input type="text" autoFocus value={name} onChange={e => setName(e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" placeholder="e.g. My Foundation" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description (Optional)</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" rows={3} placeholder="Brief description of this workspace" />
          </div>
          <div className="pt-2 flex justify-end space-x-3">
            <button type="button" onClick={onClose} className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg font-medium transition-colors">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50">
              {isSubmitting ? 'Creating...' : 'Create Workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SettingsWorkspaceModal({ workspace, workspaces, onClose, onSuccess, onDelete }: { workspace: Workspace, workspaces: Workspace[], onClose: () => void, onSuccess: () => void, onDelete: () => void }) {
  const [name, setName] = useState(workspace.name);
  const [description, setDescription] = useState(workspace.description || '');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Workspace name is required');
      return;
    }
    if (workspaces.some(w => w.id !== workspace.id && w.name.toLowerCase() === name.trim().toLowerCase())) {
      setError('Another workspace with this name already exists');
      return;
    }
    
    setIsSubmitting(true);
    try {
      await workspacesApi.updateWorkspace(workspace.id, { name: name.trim(), description: description.trim() });
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update workspace');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (workspaces.length <= 1) {
      setError('Cannot delete the last workspace in the system.');
      return;
    }
    if (workspace.dataset_count > 0) {
      setError('Cannot delete workspace containing datasets. Delete datasets first.');
      return;
    }
    
    if (confirm(`Are you sure you want to delete the "${workspace.name}" workspace? This cannot be undone.`)) {
      setIsDeleting(true);
      try {
        await workspacesApi.deleteWorkspace(workspace.id);
        onDelete();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete workspace');
        setIsDeleting(false);
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-slate-200">
          <h3 className="font-bold text-lg text-slate-900">Workspace Settings</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleUpdate} className="p-4 space-y-4">
          {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm flex items-start"><AlertCircle className="w-4 h-4 mr-2 mt-0.5 shrink-0"/>{error}</div>}
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
            <input type="text" autoFocus value={name} onChange={e => setName(e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" rows={3} />
          </div>
          
          <div className="pt-2 border-t border-slate-200 flex justify-between items-center mt-6">
            <button type="button" onClick={handleDelete} disabled={isDeleting || workspaces.length <= 1} className="text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50">
              {isDeleting ? 'Deleting...' : 'Delete Workspace'}
            </button>
            <div className="flex space-x-3">
              <button type="button" onClick={onClose} className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg font-medium transition-colors">Cancel</button>
              <button type="submit" disabled={isSubmitting} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50">
                {isSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
