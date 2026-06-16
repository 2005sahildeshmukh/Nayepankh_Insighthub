"use client";

import React from "react";
import { Insight } from "@/lib/api/analytics";
import { AlertCircle, BarChart2, Info, Activity } from "lucide-react";

interface InsightCardProps {
  insight: Insight;
}

export const InsightCard: React.FC<InsightCardProps> = ({ insight }) => {
  const getIcon = () => {
    switch (insight.type) {
      case "correlation": return <Activity className="w-5 h-5 text-indigo-500" />;
      case "dominant_category": return <BarChart2 className="w-5 h-5 text-emerald-500" />;
      case "limitation": return <AlertCircle className="w-5 h-5 text-amber-500" />;
      default: return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBorderColor = () => {
    switch (insight.type) {
      case "correlation": return "border-l-indigo-500";
      case "dominant_category": return "border-l-emerald-500";
      case "limitation": return "border-l-amber-500";
      default: return "border-l-blue-500";
    }
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-100 border-l-4 ${getBorderColor()} p-5`}>
      <div className="flex items-start">
        <div className="bg-slate-50 p-2 rounded-lg mr-4 border border-slate-100 shrink-0">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-slate-900 mb-1">{insight.title}</h4>
          <p className="text-slate-700 text-sm mb-3">{insight.statement}</p>
          
          <div className="bg-slate-50 rounded p-3 text-xs border border-slate-100">
            <span className="font-medium text-slate-700 block mb-1">Evidence:</span>
            <span className="text-slate-600">{insight.evidence}</span>
          </div>

          {(insight.limitation || insight.reliability) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {insight.reliability && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 uppercase tracking-wider">
                  Reliability: {insight.reliability}
                </span>
              )}
              {insight.limitation && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-600 border border-amber-200">
                  Limitation: {insight.limitation}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
