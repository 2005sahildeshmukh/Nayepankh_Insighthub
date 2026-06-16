"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/providers/workspace-provider";
import { getReport, ReportResponse } from "@/lib/api/intelligence";
import IntelligenceShell, { IntelligenceLoadingState, IntelligenceEmptyState } from "@/components/intelligence/IntelligenceShell";

import { FileText, Printer, Copy, Check, RefreshCw } from "lucide-react";

export default function ReportsPage() {
  const { activeWorkspace } = useWorkspace();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchReport = async (datasetId: string, view: "mapped" | "working") => {
    if (!activeWorkspace?.id) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await getReport(activeWorkspace.id, datasetId, view);
      setReport(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleCopy = () => {
    if (!report) return;
    const summary = report.sections.map(s => `## ${s.heading}\n${s.content}`).join("\n\n");
    navigator.clipboard.writeText(`${report.title}\nGenerated at: ${report.generated_at}\n\n${summary}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <IntelligenceShell
      title="Reports"
      description="Create print-ready structured summaries of dataset health, profile metrics, and model insights."
    >
      {({ datasetId, view }) => (
        <div className="space-y-6">
          {/* Action Header */}
          <div className="flex justify-between items-center border-b border-slate-100 pb-4 print:hidden">
            <h2 className="text-base font-semibold text-slate-800 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-rose-600" />
              Document Sandbox
            </h2>
            <div className="flex space-x-2">
              {report && (
                <>
                  <button
                    onClick={handleCopy}
                    className="inline-flex items-center bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg px-3 py-2 text-xs font-medium transition"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 mr-1.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 mr-1.5" />}
                    {copied ? "Copied" : "Copy Summary"}
                  </button>
                  <button
                    onClick={handlePrint}
                    className="inline-flex items-center bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg px-3 py-2 text-xs font-medium transition"
                  >
                    <Printer className="w-3.5 h-3.5 mr-1.5" />
                    Print / PDF
                  </button>
                </>
              )}
              <button
                onClick={() => fetchReport(datasetId, view)}
                disabled={isLoading}
                className="inline-flex items-center bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-xs font-medium transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
                {report ? "Regenerate" : "Generate Report"}
              </button>
            </div>
          </div>

          {isLoading && <IntelligenceLoadingState />}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-xs font-medium print:hidden">
              Failed to build intelligence report: {error}
            </div>
          )}

          {!isLoading && !report && (
            <IntelligenceEmptyState message="Click 'Generate Report' to compile a structured HTML report." />
          )}

          {/* Structured Document Print area */}
          {!isLoading && report && (
            <article className="border border-slate-200 rounded-xl p-8 bg-white shadow-sm space-y-6 print:border-0 print:shadow-none print:p-0">
              <header className="border-b-2 border-slate-900 pb-4 flex justify-between items-end">
                <div>
                  <h1 className="text-2xl font-extrabold text-slate-900">{report.title}</h1>
                  <p className="text-xs text-slate-500 mt-1">NayePankh InsightHub Intelligence Module</p>
                </div>
                <div className="text-right text-xs text-slate-500">
                  <p className="font-semibold text-slate-800">Generated At:</p>
                  <p>{report.generated_at}</p>
                </div>
              </header>

              {/* Document Sections */}
              <div className="space-y-6">
                {report.sections.map((sect, idx) => (
                  <section key={idx} className="space-y-2">
                    <h2 className="text-sm font-extrabold text-slate-900 border-b border-slate-200 pb-1 uppercase tracking-wide">
                      {idx + 1}. {sect.heading}
                    </h2>
                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap font-normal">
                      {sect.content}
                    </p>
                  </section>
                ))}
              </div>

              {/* Limitations */}
              {report.limitations.length > 0 && (
                <footer className="border-t border-slate-200 pt-4 mt-6">
                  <h3 className="text-xs font-extrabold text-slate-800 uppercase mb-2">Risks & Document Limitations:</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {report.limitations.map((lim, lIdx) => (
                      <li key={lIdx} className="text-[10px] text-slate-500">{lim}</li>
                    ))}
                  </ul>
                </footer>
              )}
            </article>
          )}

          {/* Embedded Print CSS for clean paper styles */}
          <style jsx global>{`
            @media print {
              body * {
                visibility: hidden;
              }
              article, article * {
                visibility: visible;
              }
              article {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
              }
              .print\\:hidden {
                display: none !important;
              }
            }
          `}</style>
        </div>
      )}
    </IntelligenceShell>
  );
}
