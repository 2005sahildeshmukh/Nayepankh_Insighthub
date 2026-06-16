"use client";

import React, { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useWorkspace } from "@/providers/workspace-provider";
import MlDatasetSelector from "@/components/ml/MlDatasetSelector";
import { Loader2, AlertTriangle, Info } from "lucide-react";

export interface EvidenceItem {
  label: string;
  value: string;
}

export function EvidenceList({ items }: { items?: EvidenceItem[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-4">
      <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center">
        <Info className="w-4 h-4 mr-1.5 text-blue-500" /> Grounding Evidence
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {items.map((item, index) => (
          <div key={index} className="flex justify-between items-center py-1.5 border-b border-slate-100 last:border-0">
            <span className="text-sm text-slate-500">{item.label}</span>
            <span className="text-sm font-medium text-slate-800">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function LimitationsList({ items }: { items?: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
      <h4 className="text-sm font-semibold text-amber-800 mb-2 flex items-center">
        <AlertTriangle className="w-4 h-4 mr-1.5 text-amber-600" /> Strategic Limitations
      </h4>
      <ul className="list-disc pl-5 space-y-1">
        {items.map((lim, index) => (
          <li key={index} className="text-xs text-amber-700">{lim}</li>
        ))}
      </ul>
    </div>
  );
}

export function IntelligenceLoadingState() {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <Loader2 className="w-8 h-8 animate-spin text-purple-600 mb-3" />
      <p className="text-sm text-slate-500 font-medium">Analyzing dataset with Gemini...</p>
    </div>
  );
}

export function IntelligenceEmptyState({ message = "Please select a dataset to begin." }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-25">
      <Info className="w-8 h-8 text-slate-400 mb-2" />
      <p className="text-sm text-slate-500 font-medium">{message}</p>
    </div>
  );
}

type IntelligenceShellProps = {
  title: string;
  description: string;
  children: (props: {
    datasetId: string;
    view: "mapped" | "working";
  }) => React.ReactNode;
};

export default function IntelligenceShell({ title, description, children }: IntelligenceShellProps) {
  const { activeWorkspace, isLoading } = useWorkspace();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const queryDatasetId = searchParams.get("dataset");
  const [localDatasetId, setLocalDatasetId] = useState<string | null>(null);
  const selectedDatasetId = queryDatasetId || localDatasetId;
  const [view, setView] = useState<"mapped" | "working">("working");

  const handleDatasetSelect = (datasetId: string) => {
    setLocalDatasetId(datasetId);
    if (activeWorkspace?.id) {
      const currentPath = window.location.pathname;
      router.replace(`${currentPath}?dataset=${encodeURIComponent(datasetId)}`);
    }
  };


  if (isLoading || !activeWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto p-2">
      {/* Header and Controls */}
      <div className="bg-white shadow-sm border border-slate-200 rounded-xl p-5 flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{title}</h1>
          <p className="text-sm text-slate-500 mt-1">{description}</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-4">
          <MlDatasetSelector
            workspaceId={activeWorkspace.id}
            selectedDatasetId={selectedDatasetId}
            onDatasetSelect={handleDatasetSelect}
          />
          
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-slate-700">View:</span>
            <div className="inline-flex rounded-md shadow-sm" role="group">
              <button
                type="button"
                onClick={() => setView("working")}
                className={`px-3 py-1.5 text-xs font-medium rounded-l-md border ${
                  view === "working"
                    ? "bg-purple-50 text-purple-700 border-purple-300 ring-1 ring-purple-300"
                    : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                }`}
              >
                Working
              </button>
              <button
                type="button"
                onClick={() => setView("mapped")}
                className={`px-3 py-1.5 text-xs font-medium rounded-r-md border-t border-b border-r ${
                  view === "mapped"
                    ? "bg-purple-50 text-purple-700 border-purple-300 ring-1 ring-purple-300"
                    : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                }`}
              >
                Mapped
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {selectedDatasetId ? (
        <div className="bg-white shadow-sm border border-slate-200 rounded-xl p-6">
          {children({ datasetId: selectedDatasetId, view })}
        </div>
      ) : (
        <IntelligenceEmptyState />
      )}
    </div>
  );
}
