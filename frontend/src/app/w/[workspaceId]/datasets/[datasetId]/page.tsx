"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { getDatasetDetail, getDatasetPreview, deleteDataset } from "@/lib/api/datasets";
import { useWorkspace } from "@/providers/workspace-provider";
import { ArrowLeft, Trash2, FileSpreadsheet, Loader2, AlertCircle, Settings } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { formatFileSize } from "@/lib/formatters";
import { DatasetTabs } from "@/components/workspace/datasets/DatasetTabs";

export default function DatasetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const datasetId = params.datasetId as string;

  const [isDeleting, setIsDeleting] = useState(false);

  const { data: dataset, isLoading: isDatasetLoading, error: datasetError } = useQuery({
    queryKey: ['dataset', activeWorkspace?.id, datasetId],
    queryFn: () => getDatasetDetail(activeWorkspace!.id, datasetId),
    enabled: !!activeWorkspace && !!datasetId,
  });

  const { data: preview, isLoading: isPreviewLoading } = useQuery({
    queryKey: ['dataset_preview', activeWorkspace?.id, datasetId],
    queryFn: () => getDatasetPreview(activeWorkspace!.id, datasetId, 20),
    enabled: !!activeWorkspace && !!datasetId && dataset?.status !== 'failed',
  });

  const handleDelete = async () => {
    if (!activeWorkspace || !confirm("Are you sure you want to delete this dataset? This action cannot be undone.")) return;
    
    setIsDeleting(true);
    try {
      await deleteDataset(activeWorkspace.id, datasetId);
      queryClient.invalidateQueries({ queryKey: ['datasets', activeWorkspace.id] });
      router.push(`/w/${activeWorkspace.id}/datasets`);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete dataset");
      setIsDeleting(false);
    }
  };

  if (!activeWorkspace) return null;

  if (isDatasetLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (datasetError || !dataset) {
    return (
      <div className="p-4 rounded-md bg-destructive/10 text-destructive flex items-center gap-3 border border-destructive/20">
        <AlertCircle className="h-5 w-5" />
        <p>Failed to load dataset details.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link 
            href={`/w/${activeWorkspace.id}/datasets`}
            className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <FileSpreadsheet className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-3">
                {dataset.name}
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                  dataset.status === 'ready' ? 'bg-green-500/10 text-green-500' :
                  dataset.status === 'mapping_pending' ? 'bg-yellow-500/10 text-yellow-500' :
                  dataset.status === 'failed' ? 'bg-red-500/10 text-red-500' :
                  'bg-blue-500/10 text-blue-500'
                }`}>
                  {dataset.status === 'mapping_pending' ? 'Mapping Pending' : 
                   dataset.status === 'ready' ? 'Ready' : 
                   dataset.status === 'failed' ? 'Failed' : 'Processing'}
                </span>
              </h1>
              <p className="text-sm text-muted-foreground">
                Uploaded on {new Date(dataset.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Link
            href={`/w/${activeWorkspace.id}/datasets/${dataset.id}/mapping`}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
          >
            <Settings className="mr-2 h-4 w-4" />
            Edit Mapping
          </Link>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-destructive/50 text-destructive hover:bg-destructive/10 h-9 px-4 py-2"
          >
            {isDeleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
            {isDeleting ? "" : "Delete"}
          </button>
        </div>
      </div>

      <DatasetTabs workspaceId={activeWorkspace.id} datasetId={dataset.id} />

      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Total Rows</h3>
          <p className="text-2xl font-bold">{dataset.row_count.toLocaleString()}</p>
        </div>
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Columns</h3>
          <p className="text-2xl font-bold">{dataset.column_count.toLocaleString()}</p>
        </div>
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">File Size</h3>
          <p className="text-2xl font-bold">{formatFileSize(dataset.file_size_bytes)}</p>
        </div>
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">File Type</h3>
          <p className="text-2xl font-bold uppercase">{dataset.file_type}</p>
        </div>
      </div>

      {dataset.status === 'failed' && dataset.upload_error && (
        <div className="p-4 rounded-md bg-destructive/10 text-destructive flex items-center gap-3 border border-destructive/20">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p><strong>Processing Failed:</strong> {dataset.upload_error}</p>
        </div>
      )}

      {dataset.status !== 'failed' && (
        <div className="rounded-xl border bg-card text-card-foreground shadow overflow-hidden flex flex-col">
          <div className="p-6 border-b flex items-center justify-between">
            <h3 className="font-semibold text-lg">Data Preview</h3>
            <span className="text-sm text-muted-foreground">Showing up to 20 rows</span>
          </div>
          
          <div className="overflow-x-auto">
            {isPreviewLoading ? (
              <div className="flex justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : !preview || preview.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">
                No preview data available.
              </div>
            ) : (
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-muted/50 border-b">
                  <tr>
                    {dataset.columns.map((col) => (
                      <th key={col.id} className="px-6 py-3 font-medium text-muted-foreground whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className="text-foreground">{col.original_name}</span>
                          <span className={`text-[10px] font-normal mt-0.5 ${
                            col.mapping_status === 'exclude' ? 'text-red-400' :
                            col.mapping_status === 'mapped' ? 'text-green-400' : 'text-blue-400'
                          }`}>
                            {col.mapping_status === 'exclude' ? 'EXCLUDED' : 
                             col.mapping_status === 'mapped' ? `MAPPED: ${col.standard_field}` : 
                             `KEPT: ${col.custom_display_name || col.original_name}`}
                          </span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i} className="border-b last:border-0 hover:bg-muted/20">
                      {dataset.columns.map((col) => (
                        <td key={col.id} className="px-6 py-4 whitespace-nowrap">
                          {row[col.original_name] !== null && row[col.original_name] !== undefined 
                            ? String(row[col.original_name]) 
                            : <span className="text-muted-foreground italic">null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
