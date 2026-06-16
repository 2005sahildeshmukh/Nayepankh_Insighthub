"use client";

import React, { useState } from "react";
import { AnalyticsMetadataResponse, CustomChartRequest } from "@/lib/api/analytics";
import { Plus, BarChart2 } from "lucide-react";

interface CustomChartBuilderProps {
  metadata: AnalyticsMetadataResponse | null;
  onGenerate: (req: Omit<CustomChartRequest, "view" | "filters">) => void;
  isLoading: boolean;
}

export const CustomChartBuilder: React.FC<CustomChartBuilderProps> = ({ metadata, onGenerate, isLoading }) => {
  const [chartType, setChartType] = useState<string>("bar");
  const [xCol, setXCol] = useState<string>("");
  const [yCol, setYCol] = useState<string>("");
  const [agg, setAgg] = useState<string>("count");
  const [timeGran, setTimeGran] = useState<string>("month");

  if (!metadata) return null;

  const measures = metadata.columns.filter(c => ["integer", "float"].includes(c.role) && !c.is_identifier_like);
  const categoricals = metadata.columns.filter(c => c.role === "categorical");
  const datetimes = metadata.columns.filter(c => c.role === "datetime");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate({
      chart_type: chartType,
      x_column: xCol || undefined,
      y_column: yCol || undefined,
      aggregation: agg,
      time_granularity: timeGran,
      top_n: 10
    });
  };

  return (
    <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 mt-8">
      <div className="flex items-center mb-4">
        <div className="w-8 h-8 bg-indigo-100 text-indigo-600 rounded-lg flex items-center justify-center mr-3">
          <BarChart2 className="w-4 h-4" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900">Custom Chart Builder</h3>
          <p className="text-sm text-slate-500">Create your own specific visualizations.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Chart Type</label>
          <select 
            value={chartType} 
            onChange={e => setChartType(e.target.value)}
            className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border"
          >
            <option value="bar">Bar Chart</option>
            <option value="horizontal_bar">Horizontal Bar</option>
            <option value="line">Line Chart</option>
            <option value="area">Area Chart</option>
            <option value="scatter">Scatter Plot</option>
            <option value="histogram">Histogram</option>
            <option value="donut">Donut Chart</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">X-Axis (Dimension)</label>
          <select 
            value={xCol} 
            onChange={e => setXCol(e.target.value)}
            required
            className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border"
          >
            <option value="">-- Select --</option>
            {chartType === "scatter" && measures.map(c => <option key={c.name} value={c.name}>{c.name} (Measure)</option>)}
            {chartType === "histogram" && measures.map(c => <option key={c.name} value={c.name}>{c.name} (Measure)</option>)}
            {(chartType === "line" || chartType === "area") && datetimes.map(c => <option key={c.name} value={c.name}>{c.name} (Date)</option>)}
            {["bar", "horizontal_bar", "donut"].includes(chartType) && categoricals.map(c => <option key={c.name} value={c.name}>{c.name} (Category)</option>)}
            {["bar", "horizontal_bar"].includes(chartType) && datetimes.map(c => <option key={c.name} value={c.name}>{c.name} (Date)</option>)}
          </select>
        </div>

        {chartType !== "histogram" && chartType !== "donut" && (
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Y-Axis (Measure)</label>
            <select 
              value={yCol} 
              onChange={e => setYCol(e.target.value)}
              required={chartType === "scatter"}
              className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border"
            >
              <option value="">{chartType === "scatter" ? "-- Select --" : "Record Count (Default)"}</option>
              {measures.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
        )}

        {(chartType === "line" || chartType === "area") && (
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Time Granularity</label>
            <select 
              value={timeGran} 
              onChange={e => setTimeGran(e.target.value)}
              className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border"
            >
              <option value="day">Daily</option>
              <option value="week">Weekly</option>
              <option value="month">Monthly</option>
              <option value="quarter">Quarterly</option>
              <option value="year">Yearly</option>
            </select>
          </div>
        )}

        {yCol && yCol !== "" && chartType !== "scatter" && (
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Aggregation</label>
            <select 
              value={agg} 
              onChange={e => setAgg(e.target.value)}
              className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border"
            >
              <option value="sum">Sum</option>
              <option value="mean">Average</option>
              <option value="max">Maximum</option>
              <option value="min">Minimum</option>
              <option value="count">Count Valid</option>
            </select>
          </div>
        )}

        <div className={chartType === "histogram" || chartType === "donut" ? "lg:col-span-3" : ""}>
          <button
            type="submit"
            disabled={isLoading || !xCol || (chartType === "scatter" && !yCol)}
            className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed h-10"
          >
            {isLoading ? "Generating..." : <><Plus className="w-4 h-4 mr-2" /> Generate Chart</>}
          </button>
        </div>
      </form>
    </div>
  );
};
