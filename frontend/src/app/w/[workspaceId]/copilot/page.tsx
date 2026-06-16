"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/providers/workspace-provider";
import { askCopilot, CopilotResponse } from "@/lib/api/intelligence";
import IntelligenceShell, { EvidenceList, LimitationsList, IntelligenceLoadingState } from "@/components/intelligence/IntelligenceShell";
import { Send, MessageSquare } from "lucide-react";

interface ChatMessage {
  question: string;
  response: CopilotResponse;
}

export default function CopilotPage() {
  const { activeWorkspace } = useWorkspace();
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const suggestedQuestions = [
    "Summarize this dataset.",
    "What are the biggest data-quality problems?",
    "What insights should management know?",
    "Explain the latest machine-learning model.",
    "What actions should the NGO take next?"
  ];

  const handleAsk = async (qText: string, datasetId: string, view: "mapped" | "working") => {
    if (!qText.trim() || !activeWorkspace?.id) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await askCopilot(activeWorkspace.id, datasetId, view, qText);
      setHistory((prev) => [...prev, { question: qText, response }]);
      setQuestion("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <IntelligenceShell
      title="AI Copilot"
      description="Conversational assistant and generative insights for your datasets."
    >
      {({ datasetId, view }) => (
        <div className="space-y-6">
          {/* Chat History Panel */}
          <div className="space-y-4 max-h-[400px] overflow-y-auto border border-slate-200 rounded-lg p-4 bg-slate-50 min-h-[150px] flex flex-col justify-end">
            {history.length === 0 ? (
              <div className="text-center text-slate-400 py-8 my-auto">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="text-sm font-medium">No conversation history yet. Ask a question below or choose a suggestion.</p>
              </div>
            ) : (
              <div className="space-y-6 overflow-y-auto">
                {history.map((msg, idx) => (
                  <div key={idx} className="space-y-3">
                    {/* User Prompt */}
                    <div className="flex justify-end">
                      <div className="bg-purple-600 text-white rounded-lg py-2 px-4 max-w-lg text-sm font-medium">
                        {msg.question}
                      </div>
                    </div>
                    {/* AI Answer */}
                    <div className="flex justify-start">
                      <div className="bg-white border border-slate-200 shadow-sm rounded-lg p-4 max-w-2xl w-full space-y-4">
                        <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap font-normal">
                          {msg.response.answer}
                        </div>
                        <EvidenceList items={msg.response.evidence} />
                        
                        {msg.response.recommended_actions.length > 0 && (
                          <div className="space-y-1.5">
                            <h5 className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Recommended Actions:</h5>
                            <ul className="list-disc pl-5 space-y-1">
                              {msg.response.recommended_actions.map((act, aIdx) => (
                                <li key={aIdx} className="text-xs text-slate-700">{act}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        <LimitationsList items={msg.response.limitations} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {isLoading && <IntelligenceLoadingState />}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-xs font-medium">
                Error loading insights: {error}
              </div>
            )}
          </div>

          {/* Quick Suggestions */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Suggested Questions:</h3>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((qText, sIdx) => (
                <button
                  key={sIdx}
                  type="button"
                  onClick={() => handleAsk(qText, datasetId, view)}
                  disabled={isLoading}
                  className="bg-purple-50 text-purple-700 border border-purple-200 rounded-full px-3 py-1 text-xs hover:bg-purple-100 transition disabled:opacity-50 font-medium"
                >
                  {qText}
                </button>
              ))}
            </div>
          </div>

          {/* Question Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleAsk(question, datasetId, view);
            }}
            className="flex items-center space-x-2 border border-slate-300 rounded-lg p-1.5 bg-white shadow-sm focus-within:border-purple-500 focus-within:ring-1 focus-within:ring-purple-500"
          >
            <input
              type="text"
              placeholder="Ask anything about this dataset..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isLoading}
              className="flex-1 border-0 focus:ring-0 outline-none text-sm px-3 py-2 text-slate-800"
            />
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg p-2.5 disabled:opacity-50 transition"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </IntelligenceShell>
  );
}
