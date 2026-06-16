import React from 'react';
import { MlClassificationMetrics } from './types';

interface Props {
  metrics: MlClassificationMetrics;
}

export function MlConfusionMatrix({ metrics }: Props) {
  const cm = metrics.confusion_matrix;
  if (!cm || !cm.labels || !cm.matrix || !cm.normalized_matrix) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col justify-center items-center text-slate-500">
        <p>Confusion matrix unavailable for this experiment.</p>
      </div>
    );
  }

  const { labels, matrix, normalized_matrix } = cm;

  if (labels.length !== matrix.length) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col justify-center items-center text-slate-500 text-sm">
        <p>Malformed confusion matrix data.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Confusion Matrix</h3>
      <div className="flex-1 overflow-auto">
        <div className="inline-block min-w-full">
          <table className="w-full text-sm text-center border-collapse">
            <thead>
              <tr>
                <th className="p-2 border-b-2 border-r-2 border-slate-200 font-medium text-slate-500 bg-slate-50 sticky top-0 left-0 z-20">
                  Actual \ Predicted
                </th>
                {labels.map(label => (
                  <th key={`pred_${label}`} className="p-2 border-b-2 border-slate-200 font-semibold text-slate-700 min-w-[80px] sticky top-0 bg-white z-10">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {labels.map((actualLabel, i) => (
                <tr key={`actual_${actualLabel}`}>
                  <th className="p-2 border-r-2 border-slate-200 font-semibold text-slate-700 text-right sticky left-0 bg-white z-10 whitespace-nowrap">
                    {actualLabel}
                  </th>
                  {labels.map((_, j) => {
                    const count = matrix[i][j];
                    const percent = normalized_matrix[i][j];
                    const intensity = percent; // 0 to 1
                    
                    // Style scale: Light purple to dark purple based on normalized value
                    const isDiagonal = i === j;
                    
                    const backgroundColor = `rgba(147, 51, 234, ${Math.max(0.05, intensity * 0.8)})`;
                    const textColor = intensity > 0.5 ? 'text-white' : 'text-slate-900';
                    const borderColor = isDiagonal ? 'border-purple-300' : 'border-slate-100';

                    return (
                      <td key={`cell_${i}_${j}`} className={`p-3 border ${borderColor} transition-colors duration-200 hover:ring-2 hover:ring-purple-400 hover:ring-inset relative group`} style={{ backgroundColor }}>
                        <div className={`font-bold ${textColor}`}>{count}</div>
                        <div className={`text-xs ${intensity > 0.5 ? 'text-purple-100' : 'text-slate-500'}`}>
                          {(percent * 100).toFixed(1)}%
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
