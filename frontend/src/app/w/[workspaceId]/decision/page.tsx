"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/providers/workspace-provider";
import { getDecisions, DecisionCard } from "@/lib/api/intelligence";
import IntelligenceShell, { IntelligenceLoadingState, IntelligenceEmptyState } from "@/components/intelligence/IntelligenceShell";
import { RefreshCw, Lightbulb, ShieldAlert } from "lucide-react";


export default function DecisionPage() {
  const { activeWorkspace } = useWorkspace();
  const [decisions, setDecisions] = useState<DecisionCard[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDecisions = async (datasetId: string, view: "mapped" | "working") => {
    if (!activeWorkspace?.id) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await getDecisions(activeWorkspace.id, datasetId, view);
      setDecisions(res.decisions);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityBadgeColor = (prio: string) => {
    const p = prio.toLowerCase();
    if (p === "high") return "bg-red-50 text-red-700 border-red-200";
    if (p === "medium") return "bg-amber-50 text-amber-700 border-amber-200";
    return "bg-slate-50 text-slate-700 border-slate-200";
  };

  return (
    <IntelligenceShell
      title="Decision Intelligence"
      description="Strategic actions and optimized insights built specifically for NGO operations."
    >
      {({ datasetId, view }) => (
        <div className="space-y-6">
          {/* Top Trigger Action */}
          <div className="flex justify-between items-center border-b border-slate-100 pb-4">
            <h2 className="text-base font-semibold text-slate-800 flex items-center">
              <Lightbulb className="w-5 h-5 mr-2 text-emerald-600" />
              Strategic Recommendations ({decisions ? "Generated" : "Pending"})
            </h2>
            <button
              onClick={() => fetchDecisions(datasetId, view)}
              disabled={isLoading}
              className="inline-flex items-center bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              {decisions ? "Regenerate Actions" : "Generate Decisions"}
            </button>
          </div>

          {isLoading && <IntelligenceLoadingState />}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-xs font-medium">
              Failed to build decisions: {error}
            </div>
          )}

          {!isLoading && !decisions && (
            <IntelligenceEmptyState message="Click 'Generate Decisions' to compile strategic actions." />
          )}

          {/* Cards list */}
          {!isLoading && decisions && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {decisions.map((card, index) => (
                <div key={index} className="flex flex-col bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition space-y-4">
                  {/* Badges row */}
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded border ${getPriorityBadgeColor(card.priority)}`}>
                      Priority: {card.priority}
                    </span>
                    <span className="text-xs font-medium text-slate-500">
                      Confidence: <span className="font-semibold text-slate-700">{card.confidence}</span>
                    </span>
                  </div>

                  {/* Title & Action */}
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-slate-900 leading-tight">{card.title}</h3>
                    <p className="text-xs text-slate-500">Recommended Action:</p>
                    <div className="bg-slate-50 border border-slate-100 rounded p-2.5 text-xs text-slate-700 font-medium">
                      {card.recommended_action}
                    </div>
                  </div>

                  {/* Evidence & Expected Impact */}
                  <div className="text-xs space-y-2 border-t border-slate-100 pt-3 flex-1">
                    <div>
                      <span className="font-semibold text-slate-600">Evidence:</span>
                      <ul className="list-disc pl-4 mt-1 space-y-0.5 text-slate-500">
                        {card.evidence.map((ev, evIdx) => (
                          <li key={evIdx}>{ev}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <span className="font-semibold text-slate-600">Expected Impact:</span>
                      <p className="text-slate-500 mt-0.5">{card.expected_impact}</p>
                    </div>
                  </div>

                  {/* Limitations */}
                  {card.limitations.length > 0 && (
                    <div className="border-t border-slate-100 pt-3 text-[10px] text-amber-700 bg-amber-50/50 p-2 rounded">
                      <span className="font-semibold flex items-center mb-0.5">
                        <ShieldAlert className="w-3 h-3 mr-1 text-amber-600" /> Recommendation Limit
                      </span>
                      {card.limitations.join(" ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </IntelligenceShell>
  );
}
