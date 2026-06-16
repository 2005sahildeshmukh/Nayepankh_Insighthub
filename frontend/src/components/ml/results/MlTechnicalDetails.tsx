import React from 'react';

interface Props {
  json: Record<string, unknown> | undefined;
}

export function MlTechnicalDetails({ json }: Props) {
  if (!json) return null;

  return (
    <details className="bg-slate-50 border border-slate-200 rounded-xl mt-6 group">
      <summary className="cursor-pointer p-4 font-medium text-slate-700 hover:bg-slate-100 transition-colors list-none flex items-center justify-between">
        View Technical JSON
        <span className="text-slate-400 group-open:rotate-180 transition-transform">
          ▼
        </span>
      </summary>
      <div className="p-4 border-t border-slate-200 max-h-96 overflow-auto">
        <pre className="text-xs text-slate-600 font-mono">
          {JSON.stringify(json, null, 2)}
        </pre>
      </div>
    </details>
  );
}
