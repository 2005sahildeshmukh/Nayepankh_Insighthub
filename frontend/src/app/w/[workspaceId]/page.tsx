'use client';

import React, { useEffect, useState } from 'react';
import { useWorkspace } from '@/providers/workspace-provider';
import { getDatasets, Dataset } from '@/lib/api/datasets';
import { MLService, MLExperimentSummary } from '@/lib/api/ml';
import { cleaningApi } from '@/lib/api/cleaning';
import { formatDate, formatFileSize } from '@/lib/formatters';
import Link from 'next/link';
import {
  Database,
  CheckCircle,
  Wand2,
  Brain,
  PlusCircle,
  ArrowRight,
  Loader2,
  AlertCircle,
  BarChart,
  Sparkles,
  Lightbulb,
  FileText,
  ArrowUpRight
} from 'lucide-react';

export default function WorkspaceDashboard() {
  const { activeWorkspace, isLoading: isWorkspaceLoading } = useWorkspace();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [experiments, setExperiments] = useState<MLExperimentSummary[]>([]);
  const [cleaningPlanCount, setCleaningPlanCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState<number>(0);

  const triggerRetry = () => {
    setRetryCount((prev) => prev + 1);
  };

  useEffect(() => {
    if (isWorkspaceLoading || !activeWorkspace) return;

    let active = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError(null);

    async function fetchData() {
      try {
        const workspaceId = activeWorkspace!.id;
        
        // 1. Fetch datasets and experiments in parallel
        const [fetchedDatasets, fetchedExperiments] = await Promise.all([
          getDatasets(workspaceId),
          MLService.listExperiments(workspaceId)
        ]);

        if (!active) return;

        // 2. Fetch cleaning plans in parallel using Promise.allSettled for ready datasets
        const readyDatasets = fetchedDatasets.filter((d) => d.status === 'ready');
        let plansCount = 0;

        if (readyDatasets.length > 0) {
          const planPromises = readyDatasets.map((d) =>
            cleaningApi.getPlan(workspaceId, d.id)
          );
          
          const planResults = await Promise.allSettled(planPromises);
          
          planResults.forEach((result) => {
            if (result.status === 'fulfilled' && result.value?.has_plan) {
              plansCount += 1;
            }
          });
        }

        if (!active) return;

        setDatasets(fetchedDatasets);
        setExperiments(fetchedExperiments);
        setCleaningPlanCount(plansCount);
        setLoading(false);
      } catch (err) {
        if (!active) return;
        console.error('Failed to load dashboard metrics:', err);
        setError('Failed to load workspace dashboard data. Please try again.');
        setLoading(false);
      }
    }

    fetchData();

    return () => {
      active = false;
    };
  }, [activeWorkspace, isWorkspaceLoading, retryCount]);

  const workspaceLoading = isWorkspaceLoading || loading;

  if (workspaceLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="flex justify-between items-center">
          <div className="space-y-2">
            <div className="h-8 bg-slate-200 rounded w-48"></div>
            <div className="h-4 bg-slate-200 rounded w-64"></div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-xl border border-slate-200/50"></div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-96 bg-slate-200 rounded-xl border border-slate-200/50"></div>
          <div className="h-96 bg-slate-200 rounded-xl border border-slate-200/50"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-xl bg-red-50 border border-red-200 max-w-xl mx-auto text-center space-y-4 my-12">
        <AlertCircle className="h-12 w-12 text-red-600 mx-auto" />
        <h3 className="text-lg font-semibold text-slate-900">Connection Failure</h3>
        <p className="text-sm text-slate-600">{error}</p>
        <button
          onClick={triggerRetry}
          className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow transition-all"
        >
          <Loader2 className="h-4 w-4 mr-2 animate-spin hidden" />
          Retry Connection
        </button>
      </div>
    );
  }

  if (!activeWorkspace) return null;

  const totalDatasets = datasets.length;
  const readyDatasets = datasets.filter((d) => d.status === 'ready').length;
  const completedExperiments = experiments.filter((e) => e.status === 'completed').length;

  if (totalDatasets === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Overview of {activeWorkspace.name}</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center max-w-2xl mx-auto my-8">
          <div className="mx-auto h-16 w-16 text-slate-400 mb-6 flex items-center justify-center rounded-full bg-slate-50 border border-slate-200/60">
            <Database className="w-8 h-8 text-indigo-500" />
          </div>
          <h3 className="text-xl font-bold text-slate-900">No datasets yet</h3>
          <p className="text-slate-500 mt-3 max-w-md mx-auto leading-relaxed">
            Upload your first dataset to begin profiling, cleaning, analytics and machine learning.
          </p>
          <div className="mt-8">
            <Link
              href={`/w/${activeWorkspace.id}/datasets/upload`}
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-100 transition-all"
            >
              <PlusCircle className="mr-2 h-5 w-5" />
              Upload Dataset
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Sort datasets by updated_at descending, take top 5
  const recentDatasets = [...datasets]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Overview of {activeWorkspace.name}</p>
        </div>
        <Link
          href={`/w/${activeWorkspace.id}/datasets/upload`}
          className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm hover:shadow transition-all self-start sm:self-auto"
        >
          <PlusCircle className="mr-2 h-4 w-4" />
          Upload Dataset
        </Link>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Datasets */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-start justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Total Datasets</h3>
            <p className="text-3xl font-extrabold text-slate-900 mt-2">{totalDatasets}</p>
          </div>
          <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-600">
            <Database className="h-6 w-6" />
          </div>
        </div>

        {/* Ready Datasets */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-start justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Ready Datasets</h3>
            <p className="text-3xl font-extrabold text-slate-900 mt-2">{readyDatasets}</p>
          </div>
          <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl text-emerald-600">
            <CheckCircle className="h-6 w-6" />
          </div>
        </div>

        {/* Saved Cleaning Plans */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-start justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Saved Cleaning Plans</h3>
            <p className="text-3xl font-extrabold text-slate-900 mt-2">{cleaningPlanCount}</p>
          </div>
          <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl text-amber-600">
            <Wand2 className="h-6 w-6" />
          </div>
        </div>

        {/* Completed AutoML Experiments */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-start justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Completed AutoML Experiments</h3>
            <p className="text-3xl font-extrabold text-slate-900 mt-2">{completedExperiments}</p>
          </div>
          <div className="p-3 bg-purple-50 border border-purple-100 rounded-xl text-purple-600">
            <Brain className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Main Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Datasets Table */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-slate-900">Recent Datasets</h2>
              <Link
                href={`/w/${activeWorkspace.id}/datasets`}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center"
              >
                View All Datasets
                <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto -mx-6">
              <div className="inline-block min-w-full align-middle px-6">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead>
                    <tr className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      <th className="pb-3">Dataset Name</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3 text-right">Dimensions</th>
                      <th className="pb-3 text-right">Size</th>
                      <th className="pb-3 text-right">Last Updated</th>
                      <th className="pb-3 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                    {recentDatasets.map((dataset) => {
                      const isReady = dataset.status === 'ready';
                      return (
                        <tr key={dataset.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="py-4 font-semibold text-slate-900 max-w-[160px] truncate">
                            {dataset.name}
                          </td>
                          <td className="py-4">
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                                isReady
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                                  : dataset.status === 'failed'
                                  ? 'bg-red-50 text-red-700 border border-red-100'
                                  : 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                              }`}
                            >
                              {dataset.status === 'ready'
                                ? 'Ready'
                                : dataset.status === 'failed'
                                ? 'Failed'
                                : dataset.status === 'mapping_pending'
                                ? 'Mapping Pending'
                                : 'Uploaded'}
                            </span>
                          </td>
                          <td className="py-4 text-right text-slate-500 font-medium tabular-nums">
                            {dataset.row_count.toLocaleString()} x {dataset.column_count}
                          </td>
                          <td className="py-4 text-right text-slate-500 font-medium tabular-nums">
                            {formatFileSize(dataset.file_size_bytes)}
                          </td>
                          <td className="py-4 text-right text-slate-400 text-xs font-medium">
                            {formatDate(dataset.updated_at)}
                          </td>
                          <td className="py-4 text-center">
                            <div className="inline-flex items-center gap-2">
                              {isReady ? (
                                <>
                                  <Link
                                    href={`/w/${activeWorkspace.id}/datasets/${dataset.id}/analytics`}
                                    title="Open Analytics"
                                    className="p-1 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded transition-colors"
                                  >
                                    <BarChart className="h-4 w-4" />
                                  </Link>
                                  <Link
                                    href={`/w/${activeWorkspace.id}/datasets/${dataset.id}/cleaning`}
                                    title="Clean Data"
                                    className="p-1 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded transition-colors"
                                  >
                                    <Wand2 className="h-4 w-4" />
                                  </Link>
                                  <Link
                                    href={`/w/${activeWorkspace.id}/ml?dataset=${dataset.id}`}
                                    title="Open ML Studio"
                                    className="p-1 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded transition-colors"
                                  >
                                    <Brain className="h-4 w-4" />
                                  </Link>
                                </>
                              ) : (
                                <Link
                                  href={`/w/${activeWorkspace.id}/datasets/${dataset.id}/mapping`}
                                  className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-1 rounded"
                                >
                                  Complete Mapping
                                </Link>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        {/* Shortcuts Panel */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Workspace Shortcuts</h2>
            <p className="text-xs text-slate-500 mt-1">Direct access to core capability modules.</p>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {[
              {
                label: 'Upload Dataset',
                route: `/w/${activeWorkspace.id}/datasets/upload`,
                icon: Database,
                color: 'text-indigo-600 bg-indigo-50 border-indigo-100'
              },
              {
                label: 'Interactive Analytics',
                route: `/w/${activeWorkspace.id}/analytics`,
                icon: BarChart,
                color: 'text-emerald-600 bg-emerald-50 border-emerald-100'
              },
              {
                label: 'AutoML Studio',
                route: `/w/${activeWorkspace.id}/ml`,
                icon: Brain,
                color: 'text-purple-600 bg-purple-50 border-purple-100'
              },
              {
                label: 'AI Copilot',
                route: `/w/${activeWorkspace.id}/copilot`,
                icon: Sparkles,
                color: 'text-pink-600 bg-pink-50 border-pink-100'
              },
              {
                label: 'Decision Intelligence',
                route: `/w/${activeWorkspace.id}/decision`,
                icon: Lightbulb,
                color: 'text-amber-600 bg-amber-50 border-amber-100'
              },
              {
                label: 'Executive Reports',
                route: `/w/${activeWorkspace.id}/reports`,
                icon: FileText,
                color: 'text-blue-600 bg-blue-50 border-blue-100'
              }
            ].map((shortcut) => {
              const Icon = shortcut.icon;
              return (
                <Link
                  key={shortcut.label}
                  href={shortcut.route}
                  className="flex items-center justify-between p-3.5 border border-slate-200 rounded-xl hover:border-slate-300 hover:bg-slate-50/50 transition-all group"
                >
                  <div className="flex items-center space-x-3.5">
                    <div className={`p-2 border rounded-lg ${shortcut.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-semibold text-slate-800 group-hover:text-slate-950 transition-colors">
                      {shortcut.label}
                    </span>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-slate-400 group-hover:text-slate-600 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
