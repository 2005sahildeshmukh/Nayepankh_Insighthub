"use client";

import { useWorkspace } from "@/providers/workspace-provider";
import { useQuery } from "@tanstack/react-query";
import { getDatasets, deleteDataset } from "@/lib/api/datasets";
import { PlusCircle, Database, FileSpreadsheet, Loader2, AlertCircle, ArrowRight, Trash2 } from "lucide-react";
import { formatOptionalNumber, formatFileSize } from "@/lib/formatters";
import Link from "next/link";
import { useState } from "react";
import { useQueryClient, useMutation } from "@tanstack/react-query";

export default function DatasetsPage() {
  const { activeWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const [datasetToDelete, setDatasetToDelete] = useState<{ id: string, name: string } | null>(null);

  const deleteMutation = useMutation({
    mutationFn: (datasetId: string) => deleteDataset(activeWorkspace!.id, datasetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets', activeWorkspace?.id] });
      setDatasetToDelete(null);
    },
    onError: (err) => {
      alert(err instanceof Error ? err.message : "Failed to delete dataset");
      setDatasetToDelete(null);
    }
  });

  const { data: datasets, isLoading, error } = useQuery({
    queryKey: ['datasets', activeWorkspace?.id],
    queryFn: () => getDatasets(activeWorkspace!.id),
    enabled: !!activeWorkspace,
  });

  if (!activeWorkspace) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Data Workspace</h1>
          <p className="text-muted-foreground">Manage your uploaded datasets and data connections.</p>
        </div>
        <Link
          href={`/w/${activeWorkspace.id}/datasets/upload`}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
        >
          <PlusCircle className="mr-2 h-4 w-4" />
          Upload Dataset
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="p-4 rounded-md bg-destructive/10 text-destructive flex items-center gap-3 border border-destructive/20">
          <AlertCircle className="h-5 w-5" />
          <p>Failed to load datasets.</p>
        </div>
      ) : !datasets || datasets.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-center rounded-lg border border-dashed border-border bg-card">
          <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            <Database className="h-10 w-10 text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">No datasets found</h2>
          <p className="text-muted-foreground mb-6 max-w-sm">
            Upload your first CSV or Excel file to begin analyzing and generating insights.
          </p>
          <Link
            href={`/w/${activeWorkspace.id}/datasets/upload`}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-8"
          >
            Upload Now
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((dataset) => (
            <div key={dataset.id} className="rounded-xl border bg-card text-card-foreground shadow flex flex-col group overflow-hidden">
              <div className="p-6 flex-1">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2.5 bg-primary/10 rounded-lg">
                    <FileSpreadsheet className="h-5 w-5 text-primary" />
                  </div>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    dataset.status === 'ready' ? 'bg-green-500/10 text-green-500' :
                    dataset.status === 'mapping_pending' ? 'bg-yellow-500/10 text-yellow-500' :
                    dataset.status === 'failed' ? 'bg-red-500/10 text-red-500' :
                    'bg-blue-500/10 text-blue-500'
                  }`}>
                    {dataset.status === 'mapping_pending' ? 'Action Needed' : 
                     dataset.status === 'ready' ? 'Ready' : 
                     dataset.status === 'failed' ? 'Failed' : 'Processing'}
                  </span>
                </div>
                <h3 className="font-semibold text-lg line-clamp-1 mb-1">{dataset.name}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {formatFileSize(dataset.file_size_bytes)} • {formatOptionalNumber(dataset.row_count)} rows
                </p>
              </div>
              <div className="px-6 py-4 bg-muted/50 border-t flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {new Date(dataset.created_at).toLocaleDateString()}
                </span>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setDatasetToDelete({ id: dataset.id, name: dataset.name })}
                    className="text-muted-foreground hover:text-destructive transition-colors"
                    title="Delete Dataset"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                  <Link
                    href={dataset.status === 'mapping_pending' 
                      ? `/w/${activeWorkspace.id}/datasets/${dataset.id}/mapping`
                      : `/w/${activeWorkspace.id}/datasets/${dataset.id}`}
                    className="text-sm font-medium text-primary hover:underline flex items-center"
                  >
                    {dataset.status === 'mapping_pending' ? 'Complete Mapping' : 'View Details'}
                    <ArrowRight className="ml-1 h-3 w-3" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {datasetToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-6">
              <div className="flex items-center gap-3 text-destructive mb-4">
                <AlertCircle className="h-6 w-6" />
                <h3 className="text-xl font-semibold">Delete Dataset?</h3>
              </div>
              <p className="text-slate-600 mb-2">
                Are you sure you want to delete <strong>{datasetToDelete.name}</strong>?
              </p>
              <p className="text-slate-500 text-sm mb-6">
                This will permanently remove the dataset file, all its mapped columns, cleaning plans, and generated insights. This action cannot be undone.
              </p>
              
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => setDatasetToDelete(null)}
                  disabled={deleteMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => deleteMutation.mutate(datasetToDelete.id)}
                  disabled={deleteMutation.isPending}
                  className="px-4 py-2 text-sm font-medium text-white bg-destructive hover:bg-destructive/90 rounded-md shadow-sm transition-colors disabled:opacity-50 flex items-center"
                >
                  {deleteMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Delete Dataset
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
