"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useWorkspace } from "@/providers/workspace-provider";
import { profilingApi } from "@/lib/api/profiling";
import { DatasetTabs } from "@/components/workspace/datasets/DatasetTabs";
import { ArrowLeft, Loader2, AlertCircle, CheckCircle2, ShieldAlert, AlertTriangle, Info } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { formatOptionalNumber, formatPercentage, formatDate } from "@/lib/formatters";

export default function ProfilePage() {
  const params = useParams();
  const { activeWorkspace } = useWorkspace();
  const datasetId = params.datasetId as string;

  const [view, setView] = useState<'mapped' | 'working'>('mapped');

  const { data: profile, isLoading: isProfileLoading, error: profileError } = useQuery({
    queryKey: ['dataset_profile', activeWorkspace?.id, datasetId, view],
    queryFn: () => profilingApi.getProfile(activeWorkspace!.id, datasetId, view),
    enabled: !!activeWorkspace && !!datasetId,
  });

  const { data: quality, isLoading: isQualityLoading } = useQuery({
    queryKey: ['dataset_quality', activeWorkspace?.id, datasetId, view],
    queryFn: () => profilingApi.getQualityReport(activeWorkspace!.id, datasetId, view),
    enabled: !!activeWorkspace && !!datasetId,
  });

  const [severityFilter, setSeverityFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');
  const [searchFilter, setSearchFilter] = useState('');

  const filteredIssues = quality?.issues.filter(issue => {
    if (severityFilter !== 'all' && issue.severity !== severityFilter) return false;
    if (searchFilter) {
      const searchLower = searchFilter.toLowerCase();
      const colMatch = issue.column?.toLowerCase().includes(searchLower);
      const titleMatch = issue.title.toLowerCase().includes(searchLower);
      if (!colMatch && !titleMatch) return false;
    }
    return true;
  }) || [];

  if (!activeWorkspace || isProfileLoading || isQualityLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (profileError || !profile || !quality || !profile.dataset || !profile.columns || !quality.summary || !quality.issues) {
    return (
      <div className="p-4 rounded-md bg-destructive/10 text-destructive flex flex-col items-center gap-3 border border-destructive/20 max-w-6xl mx-auto mt-6">
        <AlertCircle className="h-8 w-8" />
        <p className="font-semibold">Profile data could not be displayed because the server returned an unexpected response.</p>
        <button onClick={() => window.location.reload()} className="mt-2 bg-destructive text-destructive-foreground px-4 py-2 rounded-md hover:bg-destructive/90 text-sm">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-20">
      <div className="flex items-center justify-between py-4 border-b">
        <div className="flex items-center gap-4">
          <Link 
            href={`/w/${activeWorkspace.id}/datasets`}
            className="p-2 rounded-md hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Profile & Quality</h1>
            <p className="text-sm text-muted-foreground">Analyze statistics and data quality issues.</p>
          </div>
        </div>
        
        <div className="flex items-center bg-muted p-1 rounded-md">
          <button
            onClick={() => setView('mapped')}
            className={`px-4 py-1.5 text-sm font-medium rounded-sm transition-colors ${view === 'mapped' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Mapped Data
          </button>
          <button
            onClick={() => setView('working')}
            className={`px-4 py-1.5 text-sm font-medium rounded-sm transition-colors ${view === 'working' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Working Data (Cleaned)
          </button>
        </div>
      </div>

      <DatasetTabs workspaceId={activeWorkspace.id} datasetId={datasetId} />

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Row Count</h3>
          <p className="text-3xl font-bold text-slate-900">{formatOptionalNumber(profile.dataset.row_count)}</p>
        </div>
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Completeness</h3>
          <p className="text-3xl font-bold text-slate-900">{formatPercentage(quality.summary.completeness_percentage, 1)}</p>
          <p className="text-xs text-muted-foreground mt-1">{formatOptionalNumber(profile.dataset.missing_cells)} missing cells</p>
        </div>
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Quality Issues</h3>
          <p className="text-3xl font-bold text-slate-900">{formatOptionalNumber(quality.summary.total_issues)}</p>
          <div className="flex gap-3 mt-2 flex-wrap">
            {quality.summary.critical_issues > 0 && <span className="px-2 py-1 bg-red-50 text-red-700 border border-red-100 rounded-md text-xs font-semibold">{quality.summary.critical_issues} Critical</span>}
            {quality.summary.warning_issues > 0 && <span className="px-2 py-1 bg-amber-50 text-amber-700 border border-amber-100 rounded-md text-xs font-semibold">{quality.summary.warning_issues} Warnings</span>}
            {quality.summary.info_issues > 0 && <span className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-100 rounded-md text-xs font-semibold">{quality.summary.info_issues} Info</span>}
            {quality.summary.total_issues === 0 && <span className="px-2 py-1 bg-green-50 text-green-700 border border-green-100 rounded-md text-xs font-semibold">All good</span>}
          </div>
        </div>
        <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Complete Rows</h3>
          <p className="text-3xl font-bold text-slate-900">{formatOptionalNumber(profile.dataset.complete_rows)}</p>
          <p className="text-xs text-muted-foreground mt-1">{formatPercentage(profile.dataset.complete_rows_percentage, 1)} of dataset</p>
        </div>
      </div>

      {/* Quality Issues List */}
      <div className="rounded-xl border bg-card text-card-foreground shadow overflow-hidden">
        <div className="p-6 border-b flex flex-col md:flex-row md:items-center justify-between bg-slate-50 gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg text-slate-900 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-indigo-600" />
              Detected Quality Issues
            </h3>
            {quality.summary.total_issues === 0 && (
              <div className="text-sm text-green-600 flex items-center gap-1 font-medium ml-4">
                <CheckCircle2 className="h-4 w-4" /> No issues found
              </div>
            )}
          </div>
          
          {quality.issues.length > 0 && (
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Search column or title..."
                value={searchFilter}
                onChange={e => setSearchFilter(e.target.value)}
                className="text-sm rounded-md border border-slate-300 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-full sm:w-48"
              />
              <div className="flex bg-white rounded-md border border-slate-300 p-0.5 shadow-sm text-sm">
                <button onClick={() => setSeverityFilter('all')} className={`px-3 py-1 rounded-sm transition-colors ${severityFilter === 'all' ? 'bg-slate-100 font-medium shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}>All</button>
                <button onClick={() => setSeverityFilter('critical')} className={`px-3 py-1 rounded-sm transition-colors ${severityFilter === 'critical' ? 'bg-red-50 text-red-700 font-medium shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}>Critical</button>
                <button onClick={() => setSeverityFilter('warning')} className={`px-3 py-1 rounded-sm transition-colors ${severityFilter === 'warning' ? 'bg-amber-50 text-amber-700 font-medium shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}>Warning</button>
                <button onClick={() => setSeverityFilter('info')} className={`px-3 py-1 rounded-sm transition-colors ${severityFilter === 'info' ? 'bg-blue-50 text-blue-700 font-medium shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}>Info</button>
              </div>
            </div>
          )}
        </div>
        
        {quality.issues.length > 0 ? (
          filteredIssues.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {filteredIssues.map((issue, idx) => (
              <div key={idx} className="p-6 flex flex-col sm:flex-row gap-6 hover:bg-slate-50 transition-colors">
                <div className="sm:w-1/4">
                  <div className="flex items-center gap-2 mb-2">
                    {issue.severity === 'critical' ? (
                      <AlertCircle className="h-5 w-5 text-red-600" />
                    ) : issue.severity === 'warning' ? (
                      <AlertTriangle className="h-5 w-5 text-amber-500" />
                    ) : (
                      <Info className="h-5 w-5 text-blue-500" />
                    )}
                    <span className={`text-sm font-semibold uppercase tracking-wider ${
                      issue.severity === 'critical' ? 'text-red-700' : 
                      issue.severity === 'warning' ? 'text-amber-700' : 'text-blue-700'
                    }`}>
                      {issue.severity}
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-900">{issue.title}</h4>
                  {issue.column && (
                    <span className="inline-block mt-2 px-2 py-1 bg-slate-100 text-slate-700 rounded-md text-xs font-mono border border-slate-200">
                      col: {issue.column}
                    </span>
                  )}
                </div>
                
                <div className="sm:w-2/4">
                  <p className="text-slate-700 text-sm mb-3">{issue.explanation}</p>
                  <div className="bg-white border border-slate-200 rounded-md p-3">
                    <p className="text-xs font-medium text-slate-500 mb-1 uppercase tracking-wider">Suggested Action</p>
                    <p className="text-sm font-medium text-slate-900">{issue.suggested_action}</p>
                  </div>
                </div>
                
                <div className="sm:w-1/4 flex flex-col justify-center bg-slate-50 rounded-lg p-4 border border-slate-100">
                  <div className="text-3xl font-bold text-slate-900">{issue.affected_count.toLocaleString()}</div>
                  <div className="text-sm text-slate-500 font-medium">affected rows ({issue.affected_percentage}%)</div>
                </div>
              </div>
            ))}
          </div>
          ) : (
            <div className="p-12 text-center text-slate-500">
              <p className="text-lg font-medium text-slate-900 mb-2">No matching issues</p>
              <button onClick={() => { setSeverityFilter('all'); setSearchFilter(''); }} className="text-indigo-600 text-sm hover:underline">Clear filters</button>
            </div>
          )
        ) : (
          <div className="p-12 text-center text-slate-500">
            <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium text-slate-900 mb-1">Your data looks pristine!</p>
            <p>No quality issues were detected during the profiling scan.</p>
          </div>
        )}
      </div>

      {/* Column Profiles */}
      <h3 className="font-semibold text-xl text-slate-900 pt-4 border-b pb-4">Column Details</h3>
      <div className="grid gap-6">
        {profile.columns.map((col) => (
          <div key={col.final_name} className="rounded-xl border bg-card text-card-foreground shadow p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
              
              <div className="md:w-1/3">
                <h4 className="font-bold text-lg text-slate-900 mb-1">{col.final_name}</h4>
                {col.original_name !== col.final_name && (
                  <p className="text-xs text-muted-foreground mb-2">
                    Source: {col.original_name}
                  </p>
                )}
                <div className="flex gap-2 flex-wrap mb-4">
                  <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded-md text-xs font-medium border border-slate-200">
                    {col.inferred_type}
                  </span>
                  {col.mapping_status === 'mapped' && col.standard_field && (
                    <span className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-md text-xs font-medium border border-indigo-100">
                      Mapped
                    </span>
                  )}
                  {col.mapping_status === 'keep' && (
                    <span className="px-2 py-1 bg-slate-50 text-slate-600 rounded-md text-xs font-medium border border-slate-200">
                      Kept
                    </span>
                  )}
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between border-b pb-1 border-slate-100">
                    <span className="text-slate-500">Missing</span>
                    <span className="font-medium text-slate-900">{formatOptionalNumber(col.missing_count)} ({formatPercentage(col.missing_percentage, 1)})</span>
                  </div>
                  <div className="flex justify-between border-b pb-1 border-slate-100">
                    <span className="text-slate-500">Unique</span>
                    <span className="font-medium text-slate-900">{formatOptionalNumber(col.unique_count)} ({formatPercentage(col.unique_percentage, 1)})</span>
                  </div>
                  {col.inferred_type === 'identifier' && (
                    <div className="flex justify-between border-b pb-1 border-slate-100">
                      <span className="text-slate-500">Duplicates</span>
                      <span className="font-medium text-red-600">{formatOptionalNumber(col.duplicate_identifier_count)}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="md:w-2/3 grid gap-4 grid-cols-2">
                {/* Numeric Stats */}
                {(col.inferred_type === 'integer' || col.inferred_type === 'float') && (
                  <>
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Distribution</p>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between"><span className="text-slate-500">Min:</span> <span className="font-mono text-slate-900">{col.min !== null && col.min !== undefined ? String(col.min) : '—'}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Max:</span> <span className="font-mono text-slate-900">{col.max !== null && col.max !== undefined ? String(col.max) : '—'}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Mean:</span> <span className="font-mono text-slate-900">{formatOptionalNumber(col.mean, 2)}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Median:</span> <span className="font-mono text-slate-900">{formatOptionalNumber(col.median, 2)}</span></div>
                      </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Metrics</p>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between"><span className="text-slate-500">Std Dev:</span> <span className="font-medium text-slate-900">{formatOptionalNumber(col.std, 2)}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Q1 / Q3:</span> <span className="font-medium text-slate-900">{formatOptionalNumber(col.q1, 2)} / {formatOptionalNumber(col.q3, 2)}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Outliers:</span> <span className="font-medium text-amber-600">{formatOptionalNumber(col.outlier_count)} ({formatPercentage(col.outlier_percentage, 1)})</span></div>
                      </div>
                    </div>
                  </>
                )}

                {/* Categorical / Text Stats */}
                {(col.inferred_type === 'text' || col.inferred_type === 'categorical' || col.inferred_type === 'identifier') && (
                  <>
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-100 col-span-2 sm:col-span-1">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Top Values</p>
                      <div className="space-y-2 text-sm">
                        {col.top_values?.map((tv, i) => (
                          <div key={i} className="flex justify-between items-center group">
                            <span className="font-mono text-slate-900 truncate max-w-[120px]" title={String(tv.value)}>
                              {tv.value !== null && tv.value !== "" ? String(tv.value) : <span className="italic text-slate-400">Empty</span>}
                            </span>
                            <span className="text-slate-500 text-xs bg-slate-200 px-2 py-0.5 rounded-full">{formatOptionalNumber(tv.count)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    {(col.inferred_type === 'text' || col.inferred_type === 'categorical') && (
                      <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Text Lengths</p>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between"><span className="text-slate-500">Average:</span> <span className="font-medium text-slate-900">{formatOptionalNumber(col.average_text_length, 1)}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Shortest:</span> <span className="font-medium text-slate-900">{formatOptionalNumber(col.min_text_length)}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Longest:</span> <span className="font-medium text-slate-900">{formatOptionalNumber(col.max_text_length)}</span></div>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Datetime Stats */}
                {col.inferred_type === 'datetime' && (
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-100 col-span-2">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Timeline</p>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500 block mb-1">Earliest</span>
                        <span className="font-medium text-slate-900">{formatDate(col.earliest_date)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block mb-1">Latest</span>
                        <span className="font-medium text-slate-900">{formatDate(col.latest_date)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block mb-1">Range</span>
                        <span className="font-medium text-slate-900">{formatOptionalNumber(col.date_range_days)} days</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Boolean Stats */}
                {col.inferred_type === 'boolean' && (
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-100 col-span-2">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Distribution</p>
                    <div className="flex gap-6 text-sm">
                      <div className="flex flex-col items-center">
                        <span className="text-slate-500 mb-1">True</span>
                        <span className="font-medium text-slate-900 text-xl">{formatOptionalNumber(col.true_count)}</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-slate-500 mb-1">False</span>
                        <span className="font-medium text-slate-900 text-xl">{formatOptionalNumber(col.false_count)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
