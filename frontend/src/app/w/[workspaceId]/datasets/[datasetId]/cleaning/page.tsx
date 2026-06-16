"use client";

import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useWorkspace } from "@/providers/workspace-provider";
import { cleaningApi, CleaningConfiguration, OutlierRule, MissingValueRule, CaseRule, CleaningPreviewResponse } from "@/lib/api/cleaning";
import { profilingApi } from "@/lib/api/profiling";
import { getDatasetDetail } from "@/lib/api/datasets";
import { DatasetTabs } from "@/components/workspace/datasets/DatasetTabs";
import { ArrowLeft, Loader2, Save, RotateCcw, AlertCircle, AlertTriangle, Play, Sparkles } from "lucide-react";
import { formatPercentage } from "@/lib/formatters";
import Link from "next/link";

const DEFAULT_CONFIG: CleaningConfiguration = {
  version: 1,
  convert_empty_strings_to_null: true,
  trim_whitespace: true,
  remove_exact_duplicates: false,
  case_rules: [],
  missing_value_rules: [],
  outlier_rules: []
};

export default function CleaningPage() {
  const params = useParams();
  const { activeWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const datasetId = params.datasetId as string;

  const { isLoading: isDatasetLoading } = useQuery({
    queryKey: ['dataset', activeWorkspace?.id, datasetId],
    queryFn: () => getDatasetDetail(activeWorkspace!.id, datasetId),
    enabled: !!activeWorkspace && !!datasetId,
  });

  const { data: profile } = useQuery({
    queryKey: ['dataset_profile', activeWorkspace?.id, datasetId, 'mapped'],
    queryFn: () => profilingApi.getProfile(activeWorkspace!.id, datasetId, 'mapped'),
    enabled: !!activeWorkspace && !!datasetId,
  });

  const { data: planData, isLoading: isPlanLoading } = useQuery({
    queryKey: ['cleaning_plan', activeWorkspace?.id, datasetId],
    queryFn: () => cleaningApi.getPlan(activeWorkspace!.id, datasetId),
    enabled: !!activeWorkspace && !!datasetId,
  });

  const [config, setConfig] = useState<CleaningConfiguration>(DEFAULT_CONFIG);
  const [preview, setPreview] = useState<CleaningPreviewResponse | null>(null);
  const [lastPreviewedConfigStr, setLastPreviewedConfigStr] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeColumnId, setActiveColumnId] = useState<string | null>(null);

  const isPreviewStale = preview !== null && lastPreviewedConfigStr !== null && lastPreviewedConfigStr !== JSON.stringify(config);

  useEffect(() => {
    if (planData?.has_plan && planData.plan) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setConfig(planData.plan.configuration);
    }
  }, [planData]);

  useEffect(() => {
    if (profile?.columns?.length && !activeColumnId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setActiveColumnId(profile.columns[0].final_name);
    }
  }, [profile, activeColumnId]);

  const handlePreview = async () => {
    if (!activeWorkspace) return;
    setIsPreviewLoading(true);
    setError(null);
    try {
      const result = await cleaningApi.previewPlan(activeWorkspace.id, datasetId, config);
      setPreview(result);
      setLastPreviewedConfigStr(JSON.stringify(config));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate preview");
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleSave = async () => {
    if (!activeWorkspace) return;
    setIsSaving(true);
    setError(null);
    try {
      await cleaningApi.savePlan(activeWorkspace.id, datasetId, config);
      queryClient.invalidateQueries({ queryKey: ['cleaning_plan'] });
      queryClient.invalidateQueries({ queryKey: ['dataset_profile'] });
      queryClient.invalidateQueries({ queryKey: ['dataset_quality'] });
      setPreview(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save cleaning plan");
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    if (!activeWorkspace) return;
    if (!confirm("Are you sure you want to revert all cleaning operations? This will restore the original mapped data.")) return;
    
    setIsResetting(true);
    setError(null);
    try {
      await cleaningApi.resetPlan(activeWorkspace.id, datasetId);
      setConfig(DEFAULT_CONFIG);
      setPreview(null);
      queryClient.invalidateQueries({ queryKey: ['cleaning_plan'] });
      queryClient.invalidateQueries({ queryKey: ['dataset_profile'] });
      queryClient.invalidateQueries({ queryKey: ['dataset_quality'] });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reset cleaning plan");
    } finally {
      setIsResetting(false);
    }
  };

  const updateColumnRule = (type: 'missing' | 'case' | 'outlier', colName: string, updates: Record<string, unknown>) => {
    setConfig(prev => {
      const newConfig = { ...prev };
      
      if (type === 'missing') {
        const rules = [...newConfig.missing_value_rules.filter(r => r.column !== colName)];
        if (updates.strategy !== 'keep') {
          rules.push({ column: colName, ...updates } as MissingValueRule);
        }
        newConfig.missing_value_rules = rules;
      } 
      else if (type === 'case') {
        const rules = [...newConfig.case_rules.filter(r => r.column !== colName)];
        if (updates.strategy !== 'none') {
          rules.push({ column: colName, ...updates } as CaseRule);
        }
        newConfig.case_rules = rules;
      }
      else if (type === 'outlier') {
        const rules = [...newConfig.outlier_rules.filter(r => r.column !== colName)];
        if (updates.strategy !== 'keep') {
          rules.push({ column: colName, ...updates } as OutlierRule);
        }
        newConfig.outlier_rules = rules;
      }
      
      return newConfig;
    });
  };

  if (!activeWorkspace || isDatasetLoading || isPlanLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const activeColProfile = profile?.columns.find(c => c.final_name === activeColumnId);
  
  const currentMissingRule = config.missing_value_rules.find(r => r.column === activeColumnId) || { strategy: 'keep', value: '' };
  const currentCaseRule = config.case_rules.find(r => r.column === activeColumnId) || { strategy: 'none' };
  const currentOutlierRule = config.outlier_rules.find(r => r.column === activeColumnId) || { strategy: 'keep', iqr_multiplier: 1.5 };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-20">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between py-4 border-b gap-4">
        <div className="flex items-center gap-4">
          <Link 
            href={`/w/${activeWorkspace.id}/datasets`}
            className="p-2 rounded-md hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-indigo-500" />
              Data Cleaning
            </h1>
            <p className="text-sm text-muted-foreground">Configure automated rules to clean and standardize your dataset.</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {planData?.has_plan && (
            <button
              onClick={handleReset}
              disabled={isResetting || isSaving || isPreviewLoading}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-destructive/50 text-destructive hover:bg-destructive/10 h-10 px-4"
            >
              {isResetting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RotateCcw className="mr-2 h-4 w-4" />}
              Reset to Original
            </button>
          )}
          <button
            onClick={handlePreview}
            disabled={isPreviewLoading || isSaving || isResetting}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4"
          >
            {isPreviewLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4 text-blue-500" />}
            Preview
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || isPreviewLoading || isResetting}
            className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-6"
          >
            {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            Save Plan
          </button>
        </div>
      </div>

      <DatasetTabs workspaceId={activeWorkspace.id} datasetId={datasetId} />

      {error && (
        <div className="p-4 rounded-md bg-destructive/10 text-destructive flex items-center gap-3 border border-destructive/20">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {planData?.has_plan && !preview && (
        <div className="bg-green-50 text-green-800 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
          <p className="text-sm font-medium">A cleaning plan is currently active on this dataset.</p>
        </div>
      )}

      <div className="grid lg:grid-cols-12 gap-6">
        
        {/* Rules Sidebar */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-card border border-slate-200 rounded-xl shadow-sm p-4">
            <h3 className="font-semibold text-sm border-b pb-2 mb-3">Global Rules</h3>
            <div className="space-y-3">
              <label className="flex items-start gap-2 cursor-pointer">
                <input type="checkbox" className="mt-0.5 rounded border-gray-300 text-primary" checked={config.trim_whitespace} onChange={(e) => setConfig({...config, trim_whitespace: e.target.checked})} />
                <span className="text-xs text-slate-700">Trim Whitespace</span>
              </label>
              <label className="flex items-start gap-2 cursor-pointer">
                <input type="checkbox" className="mt-0.5 rounded border-gray-300 text-primary" checked={config.convert_empty_strings_to_null} onChange={(e) => setConfig({...config, convert_empty_strings_to_null: e.target.checked})} />
                <span className="text-xs text-slate-700">Empty Strings to Null</span>
              </label>
              <label className="flex items-start gap-2 cursor-pointer">
                <input type="checkbox" className="mt-0.5 rounded border-gray-300 text-primary" checked={config.remove_exact_duplicates} onChange={(e) => setConfig({...config, remove_exact_duplicates: e.target.checked})} />
                <span className="text-xs text-slate-700">Drop Exact Duplicates</span>
              </label>
            </div>
          </div>

          <div className="bg-card border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col h-[600px]">
            <h3 className="font-semibold text-sm border-b p-4 bg-slate-50">Column Rules</h3>
            <div className="overflow-y-auto flex-1 p-2 space-y-1">
              {profile?.columns.map(col => (
                <button
                  key={col.final_name}
                  onClick={() => setActiveColumnId(col.final_name)}
                  className={`w-full text-left px-3 py-2 text-sm rounded-md truncate transition-colors ${
                    activeColumnId === col.final_name 
                      ? 'bg-primary text-primary-foreground font-medium shadow-sm' 
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {col.final_name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Center Panel: Column Editor & Preview */}
        <div className="lg:col-span-9 space-y-6 flex flex-col">
          
          {/* Column Editor */}
          {activeColProfile && (
            <div className="bg-card border border-slate-200 rounded-xl shadow-sm p-6">
              <div className="flex items-center gap-3 mb-6 border-b pb-4">
                <h2 className="text-lg font-bold">{activeColProfile.final_name}</h2>
                <span className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-xs font-mono">{activeColProfile.inferred_type}</span>
                <span className="text-xs text-muted-foreground">{formatPercentage(activeColProfile.missing_percentage, 1)} missing</span>
              </div>
              
              <div className="grid sm:grid-cols-2 gap-8">
                {/* Missing Values */}
                <div className="space-y-3">
                  <label className="text-sm font-semibold text-slate-900 block">Handle Missing Values</label>
                  <select 
                    className="w-full text-sm rounded-md border border-slate-300 px-3 py-2 bg-white"
                    value={currentMissingRule.strategy}
                    onChange={(e) => updateColumnRule('missing', activeColProfile.final_name, { strategy: e.target.value })}
                  >
                    <option value="keep">Keep Missing (NaN)</option>
                    <option value="drop">Drop Rows with Missing</option>
                    
                    {['integer', 'float'].includes(activeColProfile.inferred_type) && (
                      <>
                        <option value="mean">Fill with Mean</option>
                        <option value="median">Fill with Median</option>
                        <option value="zero">Fill with Zero (0)</option>
                        <option value="custom">Fill Custom Numeric...</option>
                      </>
                    )}
                    
                    {['text', 'categorical', 'identifier'].includes(activeColProfile.inferred_type) && (
                      <>
                        <option value="mode">Fill with Most Frequent</option>
                        <option value="unknown_label">Fill with &apos;Unknown&apos;</option>
                        <option value="custom">Fill Custom Text...</option>
                      </>
                    )}
                    
                    {activeColProfile.inferred_type === 'boolean' && (
                      <>
                        <option value="true">Fill True</option>
                        <option value="false">Fill False</option>
                        <option value="mode">Fill with Most Frequent</option>
                      </>
                    )}

                    {activeColProfile.inferred_type === 'datetime' && (
                      <>
                        <option value="earliest">Fill Earliest Date</option>
                        <option value="latest">Fill Latest Date</option>
                        <option value="custom">Fill Custom Date...</option>
                      </>
                    )}
                  </select>
                  
                  {currentMissingRule.strategy === 'custom' && (
                    <input 
                      type={['integer', 'float'].includes(activeColProfile.inferred_type) ? 'number' : activeColProfile.inferred_type === 'datetime' ? 'datetime-local' : 'text'}
                      className="w-full text-sm rounded-md border border-slate-300 px-3 py-2"
                      placeholder="Enter custom value..."
                      value={(currentMissingRule as unknown as Record<string, unknown>).value as string | number || ''}
                      onChange={(e) => updateColumnRule('missing', activeColProfile.final_name, { 
                        strategy: 'custom', 
                        value: ['integer', 'float'].includes(activeColProfile.inferred_type) ? Number(e.target.value) : e.target.value 
                      })}
                    />
                  )}
                </div>

                {/* Case Normalization (Text) */}
                {['text', 'categorical', 'identifier'].includes(activeColProfile.inferred_type) && (
                  <div className="space-y-3">
                    <label className="text-sm font-semibold text-slate-900 block">Text Case Normalization</label>
                    <select 
                      className="w-full text-sm rounded-md border border-slate-300 px-3 py-2 bg-white"
                      value={currentCaseRule.strategy}
                      onChange={(e) => updateColumnRule('case', activeColProfile.final_name, { strategy: e.target.value })}
                    >
                      <option value="none">No Change</option>
                      <option value="lower">lowercase</option>
                      <option value="upper">UPPERCASE</option>
                      <option value="title">Title Case</option>
                    </select>
                  </div>
                )}

                {/* Outliers (Numeric) */}
                {['integer', 'float'].includes(activeColProfile.inferred_type) && (
                  <div className="space-y-3">
                    <label className="text-sm font-semibold text-slate-900 block">Handle Outliers</label>
                    <select 
                      className="w-full text-sm rounded-md border border-slate-300 px-3 py-2 bg-white"
                      value={currentOutlierRule.strategy}
                      onChange={(e) => updateColumnRule('outlier', activeColProfile.final_name, { 
                        strategy: e.target.value,
                        iqr_multiplier: currentOutlierRule.iqr_multiplier
                      })}
                    >
                      <option value="keep">Keep Outliers</option>
                      <option value="cap_iqr">Cap Outliers (IQR bounds)</option>
                      <option value="remove">Remove Outlier Rows</option>
                    </select>

                    {currentOutlierRule.strategy !== 'keep' && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-slate-500 whitespace-nowrap">IQR Multiplier:</span>
                        <input 
                          type="number"
                          step="0.1"
                          min="0.1"
                          className="w-full text-sm rounded-md border border-slate-300 px-3 py-1"
                          value={currentOutlierRule.iqr_multiplier}
                          onChange={(e) => updateColumnRule('outlier', activeColProfile.final_name, { 
                            strategy: currentOutlierRule.strategy, 
                            iqr_multiplier: parseFloat(e.target.value) || 1.5
                          })}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Preview Panel */}
          {preview ? (
            <div className={`bg-card border rounded-xl shadow-sm flex flex-col flex-1 min-h-[400px] ${isPreviewStale ? 'border-amber-300' : 'border-slate-200'}`}>
              <div className={`p-4 border-b flex items-center justify-between ${isPreviewStale ? 'bg-amber-50' : 'bg-slate-50'}`}>
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-slate-900">Preview Results</h3>
                  {isPreviewStale && (
                    <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" /> Stale (Config changed)
                    </span>
                  )}
                </div>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">Unsaved Preview</span>
              </div>
              
              <div className="p-4 border-b grid grid-cols-4 gap-4 bg-white">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Rows Kept</p>
                  <p className="text-xl font-bold">{preview.rows_after.toLocaleString()}</p>
                  <p className="text-xs text-slate-500">{preview.rows_before - preview.rows_after} removed</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Missing Filled</p>
                  <p className="text-xl font-bold text-green-600">{Math.max(0, preview.missing_cells_before - preview.missing_cells_after).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Dups Removed</p>
                  <p className="text-xl font-bold text-amber-600">{preview.duplicates_removed.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Outliers Capped</p>
                  <p className="text-xl font-bold text-indigo-600">{preview.outliers_affected.toLocaleString()}</p>
                </div>
              </div>

              {preview.warnings && preview.warnings.length > 0 && (
                <div className="bg-amber-50 border-b border-amber-100 p-3 text-sm text-amber-800">
                  <p className="font-semibold flex items-center gap-2 mb-1">
                    <AlertCircle className="h-4 w-4" />
                    Warnings during preview
                  </p>
                  <ul className="list-disc pl-5 space-y-0.5 text-xs">
                    {preview.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}

              <div className="overflow-auto max-h-[500px]">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-slate-50 border-b sticky top-0 z-10 shadow-sm">
                    <tr>
                      {preview.columns.map((col: string) => (
                        <th key={col} className="px-4 py-2 font-medium text-slate-500 whitespace-nowrap">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {preview.preview_data.map((row: Record<string, unknown>, i: number) => (
                      <tr key={i} className="hover:bg-slate-50">
                        {preview.columns.map((col: string) => (
                          <td key={col} className="px-4 py-2 whitespace-nowrap">
                            {row[col] !== null && row[col] !== undefined 
                              ? String(row[col]) 
                              : <span className="text-slate-400 italic text-xs">null</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {preview.preview_data.length === 0 && (
                  <div className="p-8 text-center text-slate-500">
                    No rows remaining after cleaning. Check your rules.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 border border-slate-200 border-dashed rounded-xl flex-1 flex flex-col items-center justify-center p-8 text-center min-h-[400px]">
              <div className="bg-white p-4 rounded-full shadow-sm border border-slate-100 mb-4">
                <Play className="h-8 w-8 text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Ready to Preview</h3>
              <p className="text-sm text-slate-500 max-w-sm mb-6">
                Adjust the cleaning rules for columns or globally, then click Preview to see how it affects your dataset before saving.
              </p>
              <button
                onClick={handlePreview}
                disabled={isPreviewLoading}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-white border border-slate-300 text-slate-700 shadow-sm hover:bg-slate-50 h-10 px-6"
              >
                {isPreviewLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4 text-blue-500" />}
                Generate Preview
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
