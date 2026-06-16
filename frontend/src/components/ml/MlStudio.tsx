"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useWorkspace } from "@/providers/workspace-provider";
import MlDatasetSelector from "@/components/ml/MlDatasetSelector";
import { MLService, MLMetadataResponse, MLValidateResponse, MLExperimentResponse, MlFeatureRole, MLExperimentSummary } from "@/lib/api/ml";
import { Loader2, Brain, AlertTriangle, CheckCircle, BarChart2, Clock, Trash2, ChevronRight } from "lucide-react";
import { MlResultDashboard } from "./results/MlResultDashboard";
const formatColumnName = (name: string) => {
  if (name === 'volunteer_status') return 'Volunteer Status';
  if (name === 'join_date') return 'Join Date';
  if (name === 'city') return 'City';
  return name;
};

export default function MlStudio() {
  const { activeWorkspace } = useWorkspace();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryDatasetId = searchParams.get("dataset");
  const queryExperimentId = searchParams.get("experiment");

  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(queryDatasetId);
  const [view, setView] = useState<'mapped' | 'working'>('working');
  const [metadata, setMetadata] = useState<MLMetadataResponse | null>(null);
  const [isLoadingMeta, setIsLoadingMeta] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Configuration State
  const [targetColumn, setTargetColumn] = useState<string>("");
  const [taskType, setTaskType] = useState<"classification" | "regression">("classification");
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [testSize, setTestSize] = useState<number>(0.2);

  // Validation State
  const [validationResult, setValidationResult] = useState<MLValidateResponse | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isInferring, setIsInferring] = useState(false);

  // Training State
  const [isTraining, setIsTraining] = useState(false);
  const [experiment, setExperiment] = useState<MLExperimentResponse | null>(null);
  const [isLoadingExperiment, setIsLoadingExperiment] = useState(false);
  const [experimentLoadError, setExperimentLoadError] = useState<string | null>(null);
  const [isRestored, setIsRestored] = useState(false);

  // History State
  const [history, setHistory] = useState<MLExperimentSummary[]>([]);



  const handleDatasetSelect = React.useCallback((newDatasetId: string) => {
    setSelectedDatasetId(newDatasetId);
    setTargetColumn("");
    setSelectedFeatures([]);
    setValidationResult(null);
    setExperiment(null);
    if (activeWorkspace?.id) {
      router.replace(`/w/${encodeURIComponent(activeWorkspace.id)}/ml?dataset=${encodeURIComponent(newDatasetId)}`);
    }
  }, [activeWorkspace, router]);

  useEffect(() => {
    let active = true;
    if (!activeWorkspace?.id || !selectedDatasetId) {
      if (active) {
        setTimeout(() => {
          setMetadata(null);
          setValidationResult(null);
          setExperiment(null);
          setTargetColumn("");
        }, 0);
      }
      return;
    }

    const loadMeta = async () => {
      setIsLoadingMeta(true);
      setError(null);
      try {
        let meta;
        try {
          meta = await MLService.getMetadata(activeWorkspace.id, selectedDatasetId, view);
        } catch (initialErr: unknown) {
          if (view === 'working' && initialErr instanceof Error && initialErr.message.includes("cleaning plan")) {
            setView('mapped');
            return; // useEffect will retrigger with 'mapped'
          }
          throw initialErr;
        }

        if (active) {
          setMetadata(meta);
          setTargetColumn("");
          setValidationResult(null);
          setSelectedFeatures([]);
        }
      } catch (err: unknown) {
        if (active) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (active) setIsLoadingMeta(false);
      }
    };

    loadMeta();
    return () => { active = false; };
  }, [activeWorkspace, selectedDatasetId, view]);

  // Load History
  useEffect(() => {
    let active = true;
    if (!activeWorkspace?.id || !selectedDatasetId) return;

    const fetchHistory = async () => {
      try {
        const hist = await MLService.listExperiments(activeWorkspace.id, selectedDatasetId);
        if (active) {
          setHistory(hist);
        }
      } catch (err) {
        console.error("Failed to load experiment history", err);
      }
    };

    fetchHistory();
    return () => { active = false; };
  }, [activeWorkspace, selectedDatasetId]);

  // Handle URL Restore
  useEffect(() => {
    if (!activeWorkspace?.id || !selectedDatasetId || !queryExperimentId) return;

    let cancelled = false;

    async function loadExperiment() {
      setIsLoadingExperiment(true);
      setExperimentLoadError(null);

      try {
        const exp = await MLService.getExperiment(activeWorkspace!.id, queryExperimentId!);

        if (cancelled) return;

        if (exp.dataset_id === selectedDatasetId) {
          setExperiment(exp);
          setIsRestored(true);
          setView(exp.dataset_view as 'mapped' | 'working');
          setTargetColumn(exp.target_column);
          setTaskType(exp.task_type as "classification" | "regression");
          setSelectedFeatures(exp.selected_features);
        } else {
          setExperimentLoadError("Experiment does not belong to the selected dataset.");
          router.replace(`/w/${encodeURIComponent(activeWorkspace!.id)}/ml?dataset=${encodeURIComponent(selectedDatasetId!)}`);
        }
      } catch (err) {
        if (cancelled) return;
        console.error("Failed to load experiment", err);
        setExperimentLoadError("Unable to load the saved experiment.");
        // Clean URL if not found
        router.replace(`/w/${encodeURIComponent(activeWorkspace!.id)}/ml?dataset=${encodeURIComponent(selectedDatasetId!)}`);
      } finally {
        if (!cancelled) {
          setIsLoadingExperiment(false);
        }
      }
    }

    if (!experiment || experiment.id !== queryExperimentId) {
      void loadExperiment();
    }
    return () => { cancelled = true; };
  }, [activeWorkspace, selectedDatasetId, queryExperimentId, router, experiment]);

  useEffect(() => {
    let active = true;
    if (!activeWorkspace?.id || !selectedDatasetId || !targetColumn || !metadata) return;

    const candidate = metadata.target_candidates.find(c => c.name === targetColumn);
    if (!candidate) return;

    const recommendedTask = candidate.recommended_task || 'classification';
    // eslint-disable-next-line
    setTaskType(recommendedTask);

    const loadRecommendations = async () => {
      setIsInferring(true);
      setError(null);
      setValidationResult(null);
      try {
        const res = await MLService.validateConfig(activeWorkspace.id, selectedDatasetId, {
          view,
          target_column: targetColumn,
          task_type: recommendedTask as "classification" | "regression",
          selected_features: null,
          test_size: testSize
        });
        if (active) {
          setValidationResult(res);
          if (res.default_selected_features) {
            setSelectedFeatures(res.default_selected_features);
          }
        }
      } catch (err: unknown) {
        if (active) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (active) setIsInferring(false);
      }
    };

    loadRecommendations();
    return () => { active = false; };
  }, [activeWorkspace?.id, selectedDatasetId, view, targetColumn, metadata, testSize]);

  const handleValidate = async () => {
    if (!activeWorkspace?.id || !selectedDatasetId || !targetColumn) return;

    setIsValidating(true);
    setError(null);
    try {
      const res = await MLService.validateConfig(activeWorkspace.id, selectedDatasetId, {
        view,
        target_column: targetColumn,
        task_type: taskType,
        selected_features: selectedFeatures,
        test_size: testSize
      });
      setValidationResult(prev => {
        if (!prev) return res;
        return {
          ...res,
          recommended_features_meta: prev.recommended_features_meta || res.recommended_features_meta,
          optional_features_meta: prev.optional_features_meta || res.optional_features_meta,
          excluded_features_meta: prev.excluded_features_meta || res.excluded_features_meta,
        };
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsValidating(false);
    }
  };

  const handleTrain = async () => {
    if (!activeWorkspace?.id || !selectedDatasetId || !validationResult?.can_train || isTraining) return;

    setIsTraining(true);
    setError(null);
    try {
      const exp = await MLService.train(activeWorkspace.id, selectedDatasetId, {
        view,
        target_column: targetColumn,
        task_type: taskType,
        selected_features: selectedFeatures,
        test_size: testSize,
        models: ["Random Forest", "Gradient Boosting", "Linear Regression", "Logistic Regression", "Extra Trees", "Decision Tree"]
      });
      setExperiment(exp);
      setIsRestored(false);
      MLService.listExperiments(activeWorkspace.id, selectedDatasetId)
        .then(setHistory)
        .catch(err => console.error("Failed to load experiment history", err));
      router.push(`/w/${encodeURIComponent(activeWorkspace.id)}/ml?dataset=${encodeURIComponent(selectedDatasetId)}&experiment=${encodeURIComponent(exp.id)}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsTraining(false);
    }
  };

  const handleDeleteExperiment = async (experimentId: string) => {
    if (!activeWorkspace?.id) return;
    if (!confirm("Are you sure you want to delete this experiment and its models?")) return;

    try {
      await MLService.deleteExperiment(activeWorkspace.id, experimentId);
      setHistory(prev => prev.filter(h => h.id !== experimentId));
    } catch (err) {
      console.error("Failed to delete experiment", err);
      alert("Failed to delete experiment");
    }
  };

  const renderFeatureCheckbox = (f: MlFeatureRole, checked: boolean, onChange: (c: boolean) => void) => (
    <label key={`feature:${f.name}`} className="flex items-start gap-2 text-sm p-2 hover:bg-slate-50 rounded border border-transparent hover:border-slate-200 transition-colors cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1"
      />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900">{formatColumnName(f.display_name || f.name)}</span>
          <span className="text-slate-500 text-xs px-1.5 py-0.5 bg-slate-100 rounded">({f.type})</span>
          {f.warning && <span className="text-orange-500 ml-auto" title={f.warning}><AlertTriangle className="w-3 h-3 inline" /></span>}
        </div>
        <div className="text-xs text-slate-500 mt-0.5">{f.reason}</div>
      </div>
    </label>
  );

  const renderExcludedFeature = (f: MlFeatureRole) => (
    <div key={`feature:${f.name}`} className="flex items-start gap-2 text-sm p-2 bg-slate-50 rounded border border-slate-100 opacity-75">
      <div className="mt-1 w-3 h-3 border border-slate-300 rounded-sm bg-slate-200 flex-shrink-0" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-700 line-through">{formatColumnName(f.display_name || f.name)}</span>
          <span className="text-slate-400 text-xs px-1.5 py-0.5 bg-slate-200 rounded">({f.type})</span>
        </div>
        <div className="text-xs text-slate-500 mt-0.5">{f.reason}</div>
      </div>
    </div>
  );

  if (!activeWorkspace) return null;

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-600" />
            Machine Learning Studio
          </h1>
          <p className="text-slate-500 mt-1">Train and evaluate predictive models automatically</p>
        </div>
        <div className="flex items-center gap-4">
          <MlDatasetSelector
            workspaceId={activeWorkspace.id}
            selectedDatasetId={selectedDatasetId}
            onDatasetSelect={handleDatasetSelect}
          />

          {selectedDatasetId && (
            <div className="flex bg-white rounded-lg border border-slate-200 p-1">
              <button
                onClick={() => setView('mapped')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${view === 'mapped' ? 'bg-purple-100 text-purple-700' : 'text-slate-600 hover:bg-slate-50'}`}
              >
                Mapped
              </button>
              <button
                onClick={() => setView('working')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${view === 'working' ? 'bg-purple-100 text-purple-700' : 'text-slate-600 hover:bg-slate-50'}`}
              >
                Working
              </button>
            </div>
          )}
        </div>
      </div>

      {!selectedDatasetId && (
        <div className="flex flex-col items-center justify-center flex-1 text-center bg-white rounded-xl border border-slate-200 border-dashed p-12">
          <div className="w-16 h-16 bg-purple-50 text-purple-500 rounded-full flex items-center justify-center mb-4">
            <Brain className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-2">No Dataset Selected</h3>
          <p className="text-slate-500 max-w-sm">Select a dataset from the dropdown above to start configuring your ML pipeline.</p>
        </div>
      )}

      {isLoadingMeta && (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
        </div>
      )}

      {error && !experimentLoadError && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg flex gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {experimentLoadError && (
        <div className="bg-orange-50 border border-orange-200 text-orange-800 p-4 rounded-lg flex gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <p className="font-semibold">Unable to load the saved experiment.</p>
            <p className="text-sm mt-1">{experimentLoadError}</p>
          </div>
        </div>
      )}

      {isLoadingExperiment && (
        <div className="flex flex-col items-center justify-center p-12 space-y-4">
          <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
          <p className="text-slate-500 font-medium">Loading saved experiment...</p>
        </div>
      )}

      {metadata && !experiment && !isLoadingExperiment && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Target Column</label>
                  <select
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                    className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value="">Select Target...</option>
                    {metadata.target_candidates.filter(c => c.is_eligible).map(c => (
                      <option key={`target:${c.name}`} value={c.name}>{formatColumnName(c.display_name || c.name)} — {c.recommended_task ? (c.recommended_task.charAt(0).toUpperCase() + c.recommended_task.slice(1)) : ''}</option>
                    ))}
                  </select>
                </div>

                {targetColumn && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Task Type</label>
                      <div className="flex gap-4">
                        <label className="flex items-center gap-2 text-sm">
                          <input type="radio" checked={taskType === 'classification'} onChange={() => setTaskType('classification')} /> Classification
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                          <input type="radio" checked={taskType === 'regression'} onChange={() => setTaskType('regression')} /> Regression
                        </label>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Test Size: {testSize * 100}%</label>
                      <input
                        type="range" min="0.1" max="0.5" step="0.05"
                        value={testSize}
                        onChange={(e) => setTestSize(parseFloat(e.target.value))}
                        className="w-full"
                      />
                    </div>

                    {isInferring ? (
                      <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200 text-slate-600">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Analyzing features for {targetColumn}...</span>
                      </div>
                    ) : validationResult?.recommended_features_meta ? (
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="block text-sm font-medium text-slate-700">Feature Selection</label>
                          <span className="text-xs text-slate-500 font-medium">
                            {selectedFeatures.length} features selected
                          </span>
                        </div>

                        <div className="border border-slate-200 rounded-lg bg-slate-50 flex flex-col max-h-[400px] overflow-y-auto overflow-x-hidden">
                          {/* Recommended Features */}
                          {validationResult.recommended_features_meta.length > 0 && (
                            <div className="p-3">
                              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 px-2">Recommended</h4>
                              <div className="flex flex-col gap-1">
                                {validationResult.recommended_features_meta.map(f => renderFeatureCheckbox(f, selectedFeatures.includes(f.name), (checked) => {
                                  if (checked) setSelectedFeatures([...selectedFeatures, f.name]);
                                  else setSelectedFeatures(selectedFeatures.filter(x => x !== f.name));
                                }))}
                              </div>
                            </div>
                          )}

                          {/* Optional Features */}
                          {validationResult.optional_features_meta && validationResult.optional_features_meta.length > 0 && (
                            <div className="p-3 border-t border-slate-200">
                              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 px-2">Optional Eligible</h4>
                              <div className="flex flex-col gap-1">
                                {validationResult.optional_features_meta.map(f => renderFeatureCheckbox(f, selectedFeatures.includes(f.name), (checked) => {
                                  if (checked) setSelectedFeatures([...selectedFeatures, f.name]);
                                  else setSelectedFeatures(selectedFeatures.filter(x => x !== f.name));
                                }))}
                              </div>
                            </div>
                          )}

                          {/* Excluded Features */}
                          {validationResult.excluded_features_meta && validationResult.excluded_features_meta.length > 0 && (
                            <div className="p-3 border-t border-slate-200">
                              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 px-2">Excluded</h4>
                              <div className="flex flex-col gap-1">
                                {validationResult.excluded_features_meta.map(f => renderExcludedFeature(f))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : null}
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* Validation Panel */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Validation</h3>
              <button
                onClick={handleValidate}
                disabled={isValidating || !targetColumn || selectedFeatures.length === 0}
                className="w-full bg-slate-900 text-white font-medium py-2 rounded-lg hover:bg-slate-800 disabled:opacity-50 flex justify-center items-center gap-2"
              >
                {isValidating && <Loader2 className="w-4 h-4 animate-spin" />}
                Validate Configuration
              </button>

              {validationResult && !isInferring && (
                <div className="mt-6 space-y-4">
                  {!validationResult.can_train && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex gap-2 text-red-700 text-sm">
                      <AlertTriangle className="w-5 h-5 shrink-0" />
                      <div>
                        <p className="font-semibold">Training Blocked</p>
                        <p>Please resolve the issues below to proceed.</p>
                      </div>
                    </div>
                  )}
                  {validationResult.can_train && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm font-medium">
                      <CheckCircle className="w-4 h-4 inline mr-1" /> Ready for training
                    </div>
                  )}

                  {validationResult.target_statistics && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-2 flex items-center gap-1"><BarChart2 className="w-4 h-4" /> Target Statistics</h4>
                      <div className="p-3 border border-slate-200 bg-slate-50 rounded-lg text-sm text-slate-700 grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-slate-500">Row Count:</span> {validationResult.target_statistics.row_count}
                        </div>
                        {validationResult.target_statistics.num_classes !== undefined && (
                          <div>
                            <span className="text-slate-500">Classes:</span> {validationResult.target_statistics.num_classes}
                          </div>
                        )}
                        {validationResult.target_statistics.smallest_class_label && (
                          <div className="col-span-2">
                            <span className="text-slate-500">Smallest Class:</span> {validationResult.target_statistics.smallest_class_label} ({validationResult.target_statistics.smallest_class_count} rows)
                          </div>
                        )}
                        {validationResult.target_statistics.class_distribution && (
                          <div className="col-span-2 mt-2">
                            <span className="text-slate-500 block mb-1">Distribution:</span>
                            <div className="flex flex-wrap gap-2">
                              {Object.entries(validationResult.target_statistics.class_distribution).map(([lbl, cnt]) => (
                                <div key={lbl} className="bg-white border border-slate-200 px-2 py-1 rounded text-xs">
                                  <span className="font-medium">{lbl}</span>: {cnt}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {validationResult.validation_issues?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-2">Warnings</h4>
                      <div className="space-y-2">
                        {validationResult.validation_issues.map((issue, i) => (
                          <div key={i} className={`p-3 border rounded text-xs ${issue.severity === 'error' ? 'border-red-200 bg-red-50 text-red-800' : 'border-orange-200 bg-orange-50 text-orange-800'}`}>
                            <p className="font-semibold mb-1">{issue.code.replace(/_/g, ' ')}</p>
                            <p>{issue.message}</p>
                            {issue.actual !== undefined && issue.required !== undefined && (
                              <p className="mt-1 opacity-80">Actual: {issue.actual} | Required: {issue.required}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {validationResult.leakage_warnings?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 mb-2">Leakage Warnings</h4>
                      <div className="space-y-2">
                        {validationResult.leakage_warnings.map((w, i) => (
                          <div key={i} className="p-2 border border-orange-200 bg-orange-50 rounded text-xs text-orange-800">
                            <span className="font-semibold">{w.feature}</span>: {w.evidence}
                            <br />Action: <span className="font-medium">{w.action_taken}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <button
                    onClick={handleTrain}
                    disabled={isTraining || !validationResult.can_train}
                    aria-disabled={isTraining || !validationResult.can_train}
                    className={`w-full mt-4 font-medium py-2 rounded-lg flex justify-center items-center gap-2 transition-colors ${isTraining || !validationResult.can_train
                      ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                      : 'bg-purple-600 text-white hover:bg-purple-700'
                      }`}
                  >
                    {isTraining && <Loader2 className="w-4 h-4 animate-spin" />}
                    Start Training
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!experiment && !isLoadingExperiment && history.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-500" />
              Experiment History
            </h3>
          </div>
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-600">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Task</th>
                  <th className="px-4 py-3">Best Model</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map(h => (
                  <tr key={h.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{formatColumnName(h.target_column)}</td>
                    <td className="px-4 py-3 capitalize">{h.task_type}</td>
                    <td className="px-4 py-3">{h.status === 'completed' ? h.best_model_name : <span className="text-orange-500">Failed</span>}</td>
                    <td className="px-4 py-3">
                      {h.status === 'completed' && h.test_metric ? (
                        <span className="font-medium">{h.test_metric.toFixed(4)} <span className="text-slate-400 text-xs font-normal">({h.primary_metric})</span></span>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{new Date(h.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleDeleteExperiment(h.id)}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        {h.status === 'completed' && (
                          <button
                            onClick={() => router.push(`/w/${encodeURIComponent(activeWorkspace.id)}/ml?dataset=${encodeURIComponent(selectedDatasetId!)}&experiment=${encodeURIComponent(h.id)}`)}
                            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-md transition-colors"
                          >
                            View
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="md:hidden divide-y divide-slate-100">
            {history.map(h => (
              <div key={h.id} className="p-4 flex flex-col gap-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium text-slate-900">{formatColumnName(h.target_column)}</h4>
                    <p className="text-xs text-slate-500 capitalize">{h.task_type} • {new Date(h.created_at).toLocaleDateString()}</p>
                  </div>
                  <button
                    onClick={() => handleDeleteExperiment(h.id)}
                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex justify-between items-end">
                  <div className="text-sm text-slate-600">
                    {h.status === 'completed' ? (
                      <>
                        <p><span className="text-slate-400">Model:</span> {h.best_model_name}</p>
                        <p><span className="text-slate-400">Score:</span> {h.test_metric?.toFixed(4)}</p>
                      </>
                    ) : (
                      <p className="text-orange-500">Failed</p>
                    )}
                  </div>
                  {h.status === 'completed' && (
                    <button
                      onClick={() => router.push(`/w/${encodeURIComponent(activeWorkspace.id)}/ml?dataset=${encodeURIComponent(selectedDatasetId!)}&experiment=${encodeURIComponent(h.id)}`)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-purple-700 bg-purple-50 rounded-md"
                    >
                      View
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {experiment && !isLoadingExperiment && (() => {
        const isClassification = experiment.task_type === "classification";
        const evalData = isClassification ? experiment.classification_evaluation : experiment.regression_evaluation;

        const hasCompleteFinalEvaluation = !!evalData;
        const hasValidPredictionSchema = experiment.prediction_schema && experiment.prediction_schema.length > 0;

        const isActuallyCompleted = experiment.status === "completed" &&
          experiment.artifact_available === true &&
          hasCompleteFinalEvaluation &&
          hasValidPredictionSchema;

        if (experiment.status === "failed" || (experiment.status === "completed" && !isActuallyCompleted)) {
          return (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-bold text-red-900 mb-2">
                  {experiment.status === "failed" ? "Experiment Failed" : "Incomplete experiment result"}
                </h3>
                <p className="text-red-700 mb-2">{experiment.error_message || "The experiment completed but is missing required evaluation data or artifacts."}</p>
                <div className="bg-red-100 p-3 rounded-md text-sm font-mono text-red-800 break-all">
                  Experiment ID: {experiment.id}
                </div>
              </div>
            </div>
          );
        }

        const summary = {
          datasetName: metadata?.dataset_name || "Unknown Dataset",
          view: experiment.dataset_view,
          target: experiment.target_column,
          task: experiment.task_type,
          bestModelName: experiment.best_model_name || "",
          status: experiment.status,
          trainingRowCount: experiment.training_row_count,
          testRowCount: experiment.test_row_count,
          createdAt: experiment.created_at,
          completedAt: experiment.completed_at,
          artifactAvailable: experiment.artifact_available
        };

        const baselineComparison = {
          baselineMetric: experiment.baseline_metric ?? null,
          candidateMetric: experiment.best_cv_metric ?? null,
          testMetric: experiment.test_metric ?? null,
          primaryMetricName: experiment.primary_metric || (isClassification ? "f1_weighted" : "rmse"),
          direction: isClassification ? "higher_is_better" as const : "lower_is_better" as const
        };

        const testMetrics = evalData || {};
        const baselineMetrics = evalData?.baseline || {};

        const featureImportance = experiment.feature_importance || [];
        const predictionSchema = experiment.prediction_schema || [];

        const viewModel = {
          summary,
          leaderboard: [], // We don't have candidate_results array saved inside experiment right now unless we fetch it or it's added. Let's pass empty for now.
          baselineComparison,
          testMetrics,
          baselineMetrics,
          featureImportance,
          predictionSchema,
          isClassification,
          isRestored,
          rawEvaluationJson: evalData,
          legacyPreprocessingWarnings: experiment.legacy_preprocessing_warnings
        };

        return (
          <MlResultDashboard
            viewModel={viewModel}
            workspaceId={activeWorkspace.id}
            experimentId={experiment.id}
            onNewExperiment={() => {
              setExperiment(null);
              router.push(`/w/${encodeURIComponent(activeWorkspace.id)}/ml?dataset=${encodeURIComponent(selectedDatasetId!)}`);
            }}
          />
        );
      })()}

      {isTraining && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-8 flex flex-col items-center text-center">
            <Loader2 className="w-12 h-12 text-purple-600 animate-spin mb-4" />
            <h3 className="text-xl font-bold text-slate-900 mb-2">Training Models</h3>
            <p className="text-sm text-slate-500">
              Training several models locally. This may take several seconds or longer depending on dataset size.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
