import React from 'react';
import { Award, Target } from 'lucide-react';
import { MlLeaderboardRow } from './types';
import { formatMetric, formatDuration } from './formatters';

interface Props {
  leaderboard: MlLeaderboardRow[];
  primaryMetricName: string;
}

export function MlLeaderboard({ leaderboard, primaryMetricName }: Props) {
  if (!leaderboard || leaderboard.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden mt-6">
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
        <Target className="w-4 h-4 text-slate-500" />
        <h3 className="font-semibold text-slate-900">Candidate Leaderboard</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-600">
          <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3">Model Candidate</th>
              <th className="px-4 py-3">CV Mean ({primaryMetricName})</th>
              <th className="px-4 py-3">CV Range</th>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {leaderboard.map((row, i) => {
              const isTop = !row.is_baseline && row.status === 'completed' && i === leaderboard.findIndex(r => !r.is_baseline && r.status === 'completed');
              return (
                <tr key={row.id || row.display_name + i} className={isTop ? "bg-purple-50/30" : "hover:bg-slate-50"}>
                  <td className="px-4 py-3 font-medium text-slate-900 flex items-center gap-2">
                    {row.display_name}
                    {row.is_baseline && <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">Baseline</span>}
                    {isTop && <span title="Top Candidate"><Award className="w-4 h-4 text-purple-600" /></span>}
                  </td>
                  <td className={`px-4 py-3 ${isTop ? 'font-bold text-purple-700' : 'font-medium'}`}>
                    {formatMetric(row.cv_mean)}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {row.cv_min !== undefined && row.cv_max !== undefined ? (
                      `[${formatMetric(row.cv_min)} - ${formatMetric(row.cv_max)}]`
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {formatDuration(row.training_time_seconds)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${
                      row.status === 'completed' ? 'bg-green-100 text-green-800' :
                      row.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
