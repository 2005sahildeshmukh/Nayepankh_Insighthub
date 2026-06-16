"use client";

import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

export const AnalyticsErrorState = ({ message, onRetry }: { message: string, onRetry?: () => void }) => (
  <div className="bg-rose-50 border border-rose-200 rounded-xl p-8 text-center flex flex-col items-center justify-center min-h-[300px]">
    <AlertCircle className="w-12 h-12 text-rose-500 mb-4" />
    <h3 className="text-lg font-bold text-rose-900 mb-2">Failed to load analytics</h3>
    <p className="text-rose-700 max-w-md mx-auto mb-6">{message}</p>
    {onRetry && (
      <button 
        onClick={onRetry}
        className="inline-flex items-center px-4 py-2 bg-rose-100 text-rose-700 hover:bg-rose-200 rounded-md text-sm font-medium transition-colors"
      >
        <RefreshCw className="w-4 h-4 mr-2" />
        Try Again
      </button>
    )}
  </div>
);

export const AnalyticsEmptyState = ({ title, message, action }: { title: string, message: string, action?: React.ReactNode }) => (
  <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 text-center flex flex-col items-center justify-center min-h-[300px]">
    <div className="w-12 h-12 bg-indigo-50 text-indigo-500 rounded-full flex items-center justify-center mb-4 border border-indigo-100">
      <AlertCircle className="w-6 h-6" />
    </div>
    <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
    <p className="text-slate-500 max-w-md mx-auto mb-6">{message}</p>
    {action}
  </div>
);

export const AnalyticsViewSelector = ({ view, setView, hasCleaningPlan }: { view: 'mapped' | 'working', setView: (v: 'mapped' | 'working') => void, hasCleaningPlan: boolean }) => (
  <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200 w-fit">
    <button
      onClick={() => setView("mapped")}
      className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
        view === "mapped" 
          ? "bg-white text-indigo-700 shadow-sm border border-slate-200/50" 
          : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
      }`}
    >
      Mapped View
    </button>
    <button
      onClick={() => hasCleaningPlan && setView("working")}
      disabled={!hasCleaningPlan}
      title={!hasCleaningPlan ? "Create a cleaning plan first to use the Working view" : "View cleaned data"}
      className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
        view === "working" 
          ? "bg-white text-indigo-700 shadow-sm border border-slate-200/50" 
          : !hasCleaningPlan
            ? "text-slate-400 cursor-not-allowed"
            : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
      }`}
    >
      Working View
    </button>
  </div>
);
