"use client";

import React from "react";
import { AnalyticsKPI } from "@/lib/api/analytics";

interface AnalyticsKpiCardProps {
  kpi: AnalyticsKPI;
}

export const AnalyticsKpiCard: React.FC<AnalyticsKpiCardProps> = ({ kpi }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 flex flex-col hover:shadow-md transition-shadow">
      <h3 className="text-sm font-medium text-slate-500 mb-1">{kpi.title}</h3>
      <div className="flex items-end justify-between">
        <div className="text-2xl font-bold text-slate-900 truncate" title={kpi.formatted_value}>
          {kpi.formatted_value}
        </div>
      </div>
      {kpi.description && (
        <p className="text-xs text-slate-400 mt-2">{kpi.description}</p>
      )}
    </div>
  );
};
