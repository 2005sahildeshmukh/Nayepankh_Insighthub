import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { MlClassificationMetrics } from './types';

interface Props {
  metrics: MlClassificationMetrics;
}

export function MlRocCurve({ metrics }: Props) {
  const roc = metrics.roc_curve_data;
  const isBinary = metrics.confusion_matrix?.labels?.length === 2;

  if (!isBinary || !roc || roc.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 h-[300px] flex flex-col justify-center items-center text-slate-500 text-sm">
        <p>ROC curve is unavailable for this experiment.</p>
      </div>
    );
  }

  const data = roc.map(pt => ({
    fpr: pt.fpr,
    tpr: pt.tpr,
    threshold: pt.threshold
  }));

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 h-[350px] flex flex-col">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">ROC Curve</h3>
      <div className="flex-1 w-full relative min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis 
              dataKey="fpr" 
              type="number" 
              domain={[0, 1]} 
              tickCount={6}
              tickFormatter={(val) => val.toFixed(1)}
              style={{ fontSize: '10px' }}
            />
            <YAxis 
              type="number" 
              domain={[0, 1]} 
              tickCount={6}
              tickFormatter={(val) => val.toFixed(1)}
              style={{ fontSize: '10px' }}
            />
            <Tooltip 
              formatter={(value: unknown, name: unknown) => [Number(value).toFixed(3), name === 'tpr' ? 'True Positive Rate' : 'False Positive Rate']}
              labelFormatter={(label: unknown) => `FPR: ${Number(label).toFixed(3)}`}
              contentStyle={{ fontSize: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
            />
            <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#94a3b8" strokeDasharray="3 3" />
            <Line 
              type="stepAfter" 
              dataKey="tpr" 
              stroke="#9333ea" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {metrics.roc_auc !== undefined && (
        <div className="text-center mt-2 text-sm text-slate-600">
          AUC = <span className="font-bold text-slate-900">{metrics.roc_auc.toFixed(4)}</span>
        </div>
      )}
    </div>
  );
}
