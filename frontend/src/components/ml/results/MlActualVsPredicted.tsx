import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { MlRegressionMetrics } from './types';

interface Props {
  metrics: MlRegressionMetrics;
}

export function MlActualVsPredicted({ metrics }: Props) {
  const data = metrics?.actual_vs_predicted || [];

  if (data.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col justify-center items-center text-slate-500 text-sm">
        <p>Actual vs Predicted data is not available.</p>
      </div>
    );
  }

  // Calculate the range to draw the perfect prediction line (y = x)
  const allValues = data.flatMap(d => [d.actual, d.predicted]);
  const minVal = Math.floor(Math.min(...allValues));
  const maxVal = Math.ceil(Math.max(...allValues));

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col">
      <h3 className="text-lg font-semibold text-slate-900 mb-6">Actual vs Predicted</h3>
      <div className="flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis 
              type="number" 
              dataKey="actual" 
              name="Actual" 
              domain={[minVal, maxVal]} 
              tick={{ fill: '#64748B', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
            />
            <YAxis 
              type="number" 
              dataKey="predicted" 
              name="Predicted" 
              domain={[minVal, maxVal]}
              tick={{ fill: '#64748B', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <ReferenceLine segment={[{ x: minVal, y: minVal }, { x: maxVal, y: maxVal }]} stroke="#94A3B8" strokeDasharray="3 3" />
            <Scatter name="Predictions" data={data} fill="#8B5CF6" fillOpacity={0.6} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
