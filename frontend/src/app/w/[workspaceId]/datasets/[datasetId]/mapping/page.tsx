"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { getDatasetDetail, getStandardFields, updateMapping, ColumnMappingUpdate } from "@/lib/api/datasets";
import { useWorkspace } from "@/providers/workspace-provider";
import { ArrowLeft, Save, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { formatPercentage } from "@/lib/formatters";
import Link from "next/link";
import { DatasetTabs } from "@/components/workspace/datasets/DatasetTabs";

export default function MappingPage() {
  const params = useParams();
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const datasetId = params.datasetId as string;

  const { data: dataset, isLoading: isDatasetLoading } = useQuery({
    queryKey: ['dataset', activeWorkspace?.id, datasetId],
    queryFn: () => getDatasetDetail(activeWorkspace!.id, datasetId),
    enabled: !!activeWorkspace && !!datasetId,
  });

  const { data: standardFields } = useQuery({
    queryKey: ['standard_fields'],
    queryFn: getStandardFields,
  });

  const [mappingState, setMappingState] = useState<Record<string, ColumnMappingUpdate>>({});
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const initializedRef = useRef(false);

  // Initialize state from dataset
  useEffect(() => {
    if (dataset && !initializedRef.current) {
      const initial: Record<string, ColumnMappingUpdate> = {};
      dataset.columns.forEach(col => {
        initial[col.id] = {
          id: col.id,
          mapping_status: col.mapping_status,
          standard_field: col.standard_field || '',
          custom_display_name: col.custom_display_name || col.original_name
        };
      });
      setMappingState(initial);
      initializedRef.current = true;
    }
  }, [dataset]);

  const handleUpdate = (colId: string, updates: Partial<ColumnMappingUpdate>) => {
    setMappingState(prev => ({
      ...prev,
      [colId]: { ...prev[colId], ...updates }
    }));
    setError(null);
  };

  const validateDuplicates = () => {
    const finalNames: string[] = [];
    Object.values(mappingState).forEach(col => {
      if (col.mapping_status === 'exclude') return;
      if (col.mapping_status === 'mapped' && col.standard_field) {
        finalNames.push(col.standard_field);
      } else if (col.mapping_status === 'keep') {
        const dcol = dataset?.columns.find(c => c.id === col.id);
        finalNames.push(col.custom_display_name || dcol?.original_name || '');
      }
    });
    
    const duplicates = finalNames.filter((item, index) => finalNames.indexOf(item) !== index);
    if (duplicates.length > 0) {
      return `Duplicate final column names detected: ${[...new Set(duplicates)].join(', ')}`;
    }
    return null;
  };

  const handleSave = async () => {
    if (!activeWorkspace || !dataset) return;
    
    const dupError = validateDuplicates();
    if (dupError) {
      setError(dupError);
      return;
    }

    // Check if mapped ones have a standard field selected
    const missingStandard = Object.values(mappingState).find(c => c.mapping_status === 'mapped' && !c.standard_field);
    if (missingStandard) {
      setError("Please select a standard field for all 'Mapped' columns.");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const updates = Object.values(mappingState);
      await updateMapping(activeWorkspace.id, datasetId, updates);
      queryClient.invalidateQueries({ queryKey: ['dataset', activeWorkspace.id, datasetId] });
      router.push(`/w/${activeWorkspace.id}/datasets/${datasetId}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save mapping.");
      setIsSaving(false);
    }
  };

  if (!activeWorkspace || isDatasetLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!dataset) return null;

  const totalCols = dataset.columns.length;
  const mappedCount = Object.values(mappingState).filter(s => s.mapping_status === 'mapped').length;
  const keptCount = Object.values(mappingState).filter(s => s.mapping_status === 'keep').length;
  const excludedCount = Object.values(mappingState).filter(s => s.mapping_status === 'exclude').length;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-20">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between sticky top-0 bg-background/80 backdrop-blur-md z-10 py-4 border-b gap-4">
        <div className="flex items-center gap-4">
          <Link 
            href={`/w/${activeWorkspace.id}/datasets`}
            className="p-2 rounded-md hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Map Columns</h1>
            <p className="text-sm text-muted-foreground">Define how your dataset aligns with the standard fields.</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-6"
          >
            {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            {isSaving ? "Saving..." : "Save Mapping"}
          </button>
        </div>
      </div>

      <DatasetTabs workspaceId={activeWorkspace.id} datasetId={dataset.id} />

      <div className="flex items-center gap-4 text-sm bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
        <div className="font-semibold text-slate-900">Summary:</div>
        <div className="text-slate-600"><span className="font-medium text-slate-900">{totalCols}</span> Total</div>
        <div className="text-blue-600"><span className="font-medium">{mappedCount}</span> Mapped</div>
        <div className="text-teal-600"><span className="font-medium">{keptCount}</span> Kept</div>
        <div className="text-red-600"><span className="font-medium">{excludedCount}</span> Excluded</div>
      </div>

      {error && (
        <div className="p-4 rounded-md bg-destructive/10 text-destructive flex items-center gap-3 border border-destructive/20 sticky top-20 z-10">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <div className="bg-card border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {dataset.columns.map((col, idx) => {
          const state = mappingState[col.id];
          if (!state) return null;
          
          return (
            <div key={col.id} className={`p-5 flex flex-col lg:flex-row lg:items-start gap-6 ${idx !== dataset.columns.length - 1 ? 'border-b border-slate-200' : ''} ${state.mapping_status === 'exclude' ? 'bg-slate-50 opacity-75' : ''}`}>
              
              {/* Column Info (Left side) */}
              <div className="lg:w-1/3 space-y-3">
                <div>
                  <h3 className="font-semibold text-lg text-slate-900 mb-1">{col.original_name}</h3>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono border border-slate-200">
                      {col.inferred_type}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {formatPercentage((col.missing_count || 0) / (dataset.row_count || 1) * 100, 0)} missing
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {col.unique_count} unique
                    </span>
                  </div>
                </div>
                
                {col.sample_values && col.sample_values.length > 0 && (
                  <div className="bg-slate-50 rounded-md p-3 border border-slate-200">
                    <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Samples</p>
                    <ul className="text-sm space-y-1 font-mono text-slate-600 break-all">
                      {col.sample_values.map((val, i) => (
                        <li key={i} className="line-clamp-1 truncate">{String(val)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Action Area (Right side) */}
              <div className="lg:w-2/3 flex flex-col space-y-4">
                
                {/* 3-way Toggle */}
                <div className="flex flex-col sm:flex-row gap-2 w-full max-w-xl">
                  <button
                    className={`flex-1 flex items-center justify-center gap-2 text-sm font-medium py-2 px-3 border rounded-md transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                      state.mapping_status === 'mapped' 
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm' 
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                    }`}
                    onClick={() => handleUpdate(col.id, { mapping_status: 'mapped' })}
                  >
                    {state.mapping_status === 'mapped' && <CheckCircle2 className="h-4 w-4" />}
                    Map Field
                  </button>
                  <button
                    className={`flex-1 flex items-center justify-center gap-2 text-sm font-medium py-2 px-3 border rounded-md transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                      state.mapping_status === 'keep' 
                      ? 'bg-teal-600 text-white border-teal-600 shadow-sm' 
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                    }`}
                    onClick={() => handleUpdate(col.id, { mapping_status: 'keep' })}
                  >
                    {state.mapping_status === 'keep' && <CheckCircle2 className="h-4 w-4" />}
                    Keep Custom
                  </button>
                  <button
                    className={`flex-1 flex items-center justify-center gap-2 text-sm font-medium py-2 px-3 border rounded-md transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                      state.mapping_status === 'exclude' 
                      ? 'bg-red-600 text-white border-red-600 shadow-sm' 
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50 hover:text-red-600'
                    }`}
                    onClick={() => handleUpdate(col.id, { mapping_status: 'exclude' })}
                  >
                    {state.mapping_status === 'exclude' && <CheckCircle2 className="h-4 w-4" />}
                    Exclude
                  </button>
                </div>

                {/* Mapping Controls */}
                {state.mapping_status === 'mapped' && standardFields && (
                  <div className="space-y-2 max-w-xl animate-in fade-in slide-in-from-top-2 duration-200">
                    <label className="text-sm font-medium text-slate-900 block">Select Standard Field</label>
                    <select
                      className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      value={state.standard_field || ''}
                      onChange={(e) => handleUpdate(col.id, { standard_field: e.target.value })}
                    >
                      <option value="" disabled>-- Select Field --</option>
                      {Object.entries(standardFields).map(([groupName, fields]) => (
                        <optgroup key={groupName} label={groupName} className="font-semibold text-slate-900 bg-slate-50">
                          {fields.map(field => (
                            <option key={field.name} value={field.name} className="font-normal text-slate-900 bg-white">
                              {field.label} ({field.name})
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                  </div>
                )}

                {state.mapping_status === 'keep' && (
                  <div className="space-y-2 max-w-xl animate-in fade-in slide-in-from-top-2 duration-200">
                    <label className="text-sm font-medium text-slate-900 block">Custom Display Name</label>
                    <input
                      type="text"
                      className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                      value={state.custom_display_name || ''}
                      onChange={(e) => handleUpdate(col.id, { custom_display_name: e.target.value })}
                      placeholder={col.original_name}
                    />
                    <p className="text-xs text-slate-500">
                      This column will remain in the dataset exactly as-is, just renamed.
                    </p>
                  </div>
                )}

                {state.mapping_status === 'exclude' && (
                  <div className="max-w-xl p-3 rounded-md bg-red-50 border border-red-100 text-red-700 text-sm animate-in fade-in slide-in-from-top-2 duration-200">
                    This column will be completely removed from the working dataset.
                  </div>
                )}

              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
