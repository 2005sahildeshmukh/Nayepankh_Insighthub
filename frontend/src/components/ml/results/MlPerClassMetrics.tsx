import React from 'react';
import { MlClassificationMetrics } from './types';
import { formatPercentage } from './formatters';

interface Props {
  metrics: MlClassificationMetrics;
}

export function MlPerClassMetrics({ metrics }: Props) {
  const pcm = metrics.per_class_metrics;
  
  if (!pcm || Object.keys(pcm).length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col justify-center items-center text-slate-500 text-sm">
        <p>Per-class metrics unavailable.</p>
      </div>
    );
  }

  const classes = Object.keys(pcm);

  return (
    <div className="bg-white border border-slate-200 rounded-xl flex flex-col overflow-hidden h-full">
      <div className="p-4 border-b border-slate-200 bg-slate-50">
        <h3 className="text-sm font-semibold text-slate-900">Per-Class Metrics</h3>
      </div>
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm text-left text-slate-600">
          <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200 sticky top-0">
            <tr>
              <th className="px-4 py-3">Class</th>
              <th className="px-4 py-3">Precision</th>
              <th className="px-4 py-3">Recall</th>
              <th className="px-4 py-3">F1 Score</th>
              <th className="px-4 py-3 text-right">Support</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {classes.map(cls => (
              <tr key={cls} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{cls}</td>
                <td className="px-4 py-3">{formatPercentage(pcm[cls].precision)}</td>
                <td className="px-4 py-3">{formatPercentage(pcm[cls].recall)}</td>
                <td className="px-4 py-3 font-medium text-purple-700">{formatPercentage(pcm[cls].f1)}</td>
                <td className="px-4 py-3 text-right text-slate-500">{pcm[cls].support}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
