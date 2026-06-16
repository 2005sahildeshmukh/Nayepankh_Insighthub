"use client";

import React from "react";
import { CorrelationResponse } from "@/lib/api/analytics";

interface CorrelationMatrixProps {
  data: CorrelationResponse;
}

export const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({ data }) => {
  if (!data.labels || data.labels.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center">
        <p className="text-slate-500 mb-2">Insufficient numerical data to calculate correlations.</p>
        {data.limitation_note && (
          <p className="text-sm text-slate-400">{data.limitation_note}</p>
        )}
      </div>
    );
  }

  const getColor = (value: number | null) => {
    if (value === null) return "bg-slate-100";
    if (value === 1) return "bg-indigo-900 text-white";
    if (value > 0.8) return "bg-indigo-700 text-white";
    if (value > 0.6) return "bg-indigo-500 text-white";
    if (value > 0.4) return "bg-indigo-400 text-white";
    if (value > 0.2) return "bg-indigo-200";
    if (value > 0) return "bg-indigo-50";
    if (value === -1) return "bg-rose-900 text-white";
    if (value < -0.8) return "bg-rose-700 text-white";
    if (value < -0.6) return "bg-rose-500 text-white";
    if (value < -0.4) return "bg-rose-400 text-white";
    if (value < -0.2) return "bg-rose-200";
    return "bg-rose-50";
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="mb-4">
        <h3 className="font-semibold text-slate-900 text-lg">Correlation Matrix</h3>
        <p className="text-sm text-slate-500">
          Pearson correlation coefficients between numeric variables.
        </p>
      </div>

      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider sticky left-0 bg-slate-50 border-r border-slate-200 z-10">
                Variables
              </th>
              {data.labels.map(label => (
                <th key={`head-${label}`} className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider whitespace-nowrap">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {data.labels.map((rowLabel, i) => (
              <tr key={`row-${rowLabel}`}>
                <td className="px-4 py-3 whitespace-nowrap font-medium text-slate-900 sticky left-0 bg-white border-r border-slate-200 z-10 shadow-[1px_0_0_0_#e2e8f0]">
                  {rowLabel}
                </td>
                {data.values[i].map((val, j) => (
                  <td key={`cell-${i}-${j}`} className={`px-4 py-3 text-center ${getColor(val)} transition-colors whitespace-nowrap`}>
                    {val !== null ? val.toFixed(2) : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.limitation_note && (
        <p className="mt-4 text-xs text-slate-400 text-center italic">
          {data.limitation_note}
        </p>
      )}

      {Object.keys(data.excluded_columns || {}).length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="text-xs font-medium text-slate-500 mb-2">Excluded columns:</p>
          <ul className="text-xs text-slate-400 space-y-1">
            {Object.entries(data.excluded_columns).map(([col, reason]) => (
              <li key={col}><span className="font-medium">{col}:</span> {reason as string}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
