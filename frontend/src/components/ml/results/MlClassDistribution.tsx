import React from 'react';
import { MlClassificationMetrics } from './types';

interface Props {
  metrics: MlClassificationMetrics;
}

export function MlClassDistribution({ metrics }: Props) {
  const dist = metrics.class_distribution;
  if (!dist || dist.length === 0) return null;

  const total = dist.reduce((acc, curr) => acc + curr.count, 0);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">Test Set Distribution</h3>
      <div className="flex-1 space-y-3">
        {dist.map(d => {
          const pct = total > 0 ? (d.count / total) * 100 : 0;
          return (
            <div key={d.label}>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-medium text-slate-700">{d.label}</span>
                <span className="text-slate-500">{d.count} ({pct.toFixed(1)}%)</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-blue-500 h-full rounded-full" 
                  style={{ width: `${pct}%` }} 
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
