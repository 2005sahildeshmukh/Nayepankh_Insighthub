import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { MlRegressionMetrics } from './types';
import { formatMetric } from './formatters';

interface Props {
  metrics: MlRegressionMetrics;
}

export function MlResidualPlot({ metrics }: Props) {
  const data = metrics?.residuals || [];
  const summary = metrics?.residual_summary;

  if (data.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col justify-center items-center text-slate-500 text-sm">
        <p>Residual data is not available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col">
      <div className="flex justify-between items-start mb-6">
        <h3 className="text-lg font-semibold text-slate-900">Residual Plot</h3>
        {summary && (
          <div className="text-right">
            <p className="text-xs text-slate-500">Mean Residual</p>
            <p className="text-sm font-medium text-slate-900">{formatMetric(summary.mean_residual)}</p>
          </div>
        )}
      </div>
      
      <div className="flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis 
              type="number" 
              dataKey="predicted" 
              name="Predicted" 
              tick={{ fill: '#64748B', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
            />
            <YAxis 
              type="number" 
              dataKey="residual" 
              name="Residual" 
              tick={{ fill: '#64748B', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{ borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <ReferenceLine y={0} stroke="#94A3B8" strokeDasharray="3 3" />
            <Scatter name="Residuals" data={data} fill="#EC4899" fillOpacity={0.6} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
