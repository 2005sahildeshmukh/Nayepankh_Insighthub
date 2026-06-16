"use client";

import React, { useState, useEffect } from "react";
import { 
  getAnalyticsMetadata, getAnalyticsDashboard, getCorrelation, getCustomChart,
  AnalyticsMetadataResponse, AnalyticsDashboardResponse, CorrelationResponse,
  AnalyticsFilter, CustomChartRequest, ChartSpecification
} from "@/lib/api/analytics";
import { AnalyticsErrorState, AnalyticsEmptyState, AnalyticsViewSelector } from "./AnalyticsStates";
import { DatasetSelector } from "./DatasetSelector";
import { AnalyticsFilters } from "./AnalyticsFilters";
import { AnalyticsKpiCard } from "./AnalyticsKpiCard";
import { ChartCard } from "./ChartCard";
import { InsightCard } from "./InsightCard";
import { CorrelationMatrix } from "./CorrelationMatrix";
import { CustomChartBuilder } from "./CustomChartBuilder";
import { Loader2 } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";

interface AnalyticsDashboardProps {
  workspaceId: string;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ workspaceId }) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams.get("dataset");

  const [view, setView] = useState<'mapped' | 'working'>('mapped');
  const [filters, setFilters] = useState<AnalyticsFilter[]>([]);
  
  const [metadata, setMetadata] = useState<AnalyticsMetadataResponse | null>(null);
  const [dashboard, setDashboard] = useState<AnalyticsDashboardResponse | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationResponse | null>(null);
  const [customCharts, setCustomCharts] = useState<ChartSpecification[]>([]);
  
  const [isLoadingMeta, setIsLoadingMeta] = useState(false);
  const [isLoadingDash, setIsLoadingDash] = useState(false);
  const [isGeneratingCustom, setIsGeneratingCustom] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load Metadata when dataset changes
  useEffect(() => {
    if (!workspaceId || !datasetId) {
      setTimeout(() => {
        setMetadata(null);
        setDashboard(null);
        setCorrelation(null);
        setCustomCharts([]);
        setFilters([]);
        setView('mapped');
      }, 0);
      return;
    }

    const loadMeta = async () => {
      setIsLoadingMeta(true);
      setError(null);
      try {
        const meta = await getAnalyticsMetadata(workspaceId, datasetId, "mapped");
        setMetadata(meta);
        // If view is working but no plan, revert to mapped
        if (view === 'working' && !meta.has_cleaning_plan) {
          setView('mapped');
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : String(err) || "Failed to load dataset metadata");
      } finally {
        setIsLoadingMeta(false);
      }
    };
    loadMeta();
  }, [workspaceId, datasetId, view]);

  // Load Dashboard when dataset, view, or filters change
  useEffect(() => {
    if (!workspaceId || !datasetId || !metadata) return;

    const loadDashboard = async () => {
      setIsLoadingDash(true);
      setError(null);
      try {
        const [dashRes, corrRes] = await Promise.all([
          getAnalyticsDashboard(workspaceId, datasetId, view, filters),
          getCorrelation(workspaceId, datasetId, view, filters)
        ]);
        setDashboard(dashRes);
        setCorrelation(corrRes);
        setCustomCharts([]); // clear custom charts on view/filter change
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : String(err) || "Failed to load analytics dashboard");
      } finally {
        setIsLoadingDash(false);
      }
    };
    loadDashboard();
  }, [workspaceId, datasetId, view, filters, metadata]);

  const handleDatasetSelect = (id: string) => {
    if (!workspaceId) return;
    router.push(`/w/${encodeURIComponent(workspaceId)}/analytics?dataset=${encodeURIComponent(id)}`);
  };

  const handleGenerateCustomChart = async (req: Omit<CustomChartRequest, "view" | "filters">) => {
    if (!workspaceId || !datasetId) return;
    setIsGeneratingCustom(true);
    try {
      const res = await getCustomChart(workspaceId, datasetId, {
        ...req,
        view,
        filters
      });
      // Prepend the new custom chart
      setCustomCharts(prev => [{ ...res.specification, id: `custom_${Date.now()}` }, ...prev]);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err) || "Failed to generate custom chart");
    } finally {
      setIsGeneratingCustom(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <DatasetSelector 
          workspaceId={workspaceId} 
          selectedDatasetId={datasetId} 
          onDatasetSelect={handleDatasetSelect} 
        />
        
        {datasetId && metadata && (
          <AnalyticsViewSelector 
            view={view} 
            setView={setView} 
            hasCleaningPlan={metadata.has_cleaning_plan} 
          />
        )}
      </div>

      {!datasetId && (
        <AnalyticsEmptyState 
          title="Select a Dataset" 
          message="Please select a ready dataset from the dropdown above to view analytics." 
        />
      )}

      {datasetId && isLoadingMeta && !metadata && (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      )}

      {error && !isLoadingMeta && !isLoadingDash && (
        <AnalyticsErrorState message={error} />
      )}

      {datasetId && metadata && !error && (
        <>
          <AnalyticsFilters 
            metadata={metadata} 
            filters={filters} 
            setFilters={setFilters} 
            onApply={() => {}} 
          />

          {isLoadingDash && !dashboard ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            </div>
          ) : dashboard ? (
            <div className="space-y-8 animate-in fade-in duration-500">
              {/* Overview text */}
              <div className="flex items-center justify-between">
                <p className="text-slate-600 text-sm">
                  Showing analytics for <span className="font-semibold text-slate-800">{dashboard.overview.dataset_name}</span>. 
                  ({dashboard.overview.row_count.toLocaleString()} rows, {dashboard.overview.column_count} columns)
                  {filters.length > 0 && ` • Filtered to ${dashboard.filtered_row_count.toLocaleString()} rows.`}
                </p>
              </div>

              {/* KPIs */}
              {dashboard.kpis.length > 0 && (
                <div>
                  <h2 className="text-xl font-bold text-slate-900 mb-4">Key Metrics</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {dashboard.kpis.map(kpi => (
                      <AnalyticsKpiCard key={kpi.id} kpi={kpi} />
                    ))}
                  </div>
                </div>
              )}

              {/* Insights */}
              {dashboard.insights.length > 0 && (
                <div>
                  <h2 className="text-xl font-bold text-slate-900 mb-4">Deterministic Insights</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {dashboard.insights.map(insight => (
                      <InsightCard key={insight.id} insight={insight} />
                    ))}
                  </div>
                </div>
              )}

              {/* Custom Charts */}
              {customCharts.length > 0 && (
                <div className="border-t border-slate-200 pt-8 mt-8">
                  <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center">
                    <span className="bg-indigo-100 text-indigo-700 text-xs py-1 px-2 rounded mr-2">Custom</span>
                    Your Charts
                  </h2>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {customCharts.map(chart => (
                      <ChartCard key={chart.id} spec={chart} />
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Charts */}
              {dashboard.recommended_charts.length > 0 && (
                <div className="border-t border-slate-200 pt-8 mt-8">
                  <h2 className="text-xl font-bold text-slate-900 mb-4">Recommended Charts</h2>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {dashboard.recommended_charts.map(chart => (
                      <ChartCard key={chart.id} spec={chart} />
                    ))}
                  </div>
                </div>
              )}

              {/* Correlation Matrix */}
              {correlation && (
                <div className="border-t border-slate-200 pt-8 mt-8">
                  <CorrelationMatrix data={correlation} />
                </div>
              )}

              {/* Custom Chart Builder */}
              <div className="border-t border-slate-200 pt-8 mt-8 pb-12">
                <CustomChartBuilder 
                  metadata={metadata} 
                  onGenerate={handleGenerateCustomChart} 
                  isLoading={isGeneratingCustom} 
                />
              </div>

            </div>
          ) : null}
        </>
      )}
    </div>
  );
};
