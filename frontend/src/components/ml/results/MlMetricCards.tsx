import React from 'react';
import { Target, Activity, Zap, CheckCircle, Crosshair } from 'lucide-react';
import { MlClassificationMetrics, MlRegressionMetrics } from './types';
import { formatPercentage, formatMetric } from './formatters';

interface Props {
  isClassification: boolean;
  metrics: MlClassificationMetrics | MlRegressionMetrics;
}

export function MlMetricCards({ isClassification, metrics }: Props) {
  if (isClassification) {
    const classMetrics = metrics as MlClassificationMetrics;
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard 
          title="Accuracy" 
          value={formatPercentage(classMetrics.accuracy)} 
          icon={<Target className="w-4 h-4 text-purple-600" />} 
          tooltip="Overall proportion of correct predictions"
        />
        <MetricCard 
          title="Balanced Acc." 
          value={formatPercentage(classMetrics.balanced_accuracy)} 
          icon={<Activity className="w-4 h-4 text-purple-600" />} 
          tooltip="Accuracy adjusted for imbalanced classes"
        />
        <MetricCard 
          title="Precision (W)" 
          value={formatPercentage(classMetrics.precision_weighted)} 
          icon={<Crosshair className="w-4 h-4 text-purple-600" />} 
          tooltip="How often positive predictions are correct (weighted by class support)"
        />
        <MetricCard 
          title="Recall (W)" 
          value={formatPercentage(classMetrics.recall_weighted)} 
          icon={<Zap className="w-4 h-4 text-purple-600" />} 
          tooltip="How many actual positives were found (weighted by class support)"
        />
        <MetricCard 
          title="F1 Score (W)" 
          value={formatPercentage(classMetrics.f1_weighted)} 
          icon={<CheckCircle className="w-4 h-4 text-purple-600" />} 
          tooltip="Harmonic mean of precision and recall (weighted)"
        />
        <MetricCard 
          title="Log Loss" 
          value={formatMetric(classMetrics.log_loss)} 
          icon={<Activity className="w-4 h-4 text-purple-600" />} 
          tooltip="Penalty for false confidence. Lower is better."
        />
      </div>
    );
  }

  const regMetrics = metrics as MlRegressionMetrics;
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <MetricCard 
        title="RMSE" 
        value={formatMetric(regMetrics.rmse)} 
        icon={<Activity className="w-4 h-4 text-blue-600" />} 
        tooltip="Root Mean Squared Error. Lower is better."
      />
      <MetricCard 
        title="MAE" 
        value={formatMetric(regMetrics.mae)} 
        icon={<Target className="w-4 h-4 text-blue-600" />} 
        tooltip="Mean Absolute Error. Lower is better."
      />
      <MetricCard 
        title="R² Score" 
        value={formatMetric(regMetrics.r2)} 
        icon={<Crosshair className="w-4 h-4 text-blue-600" />} 
        tooltip="Proportion of variance explained by the model. Higher is better."
      />
      <MetricCard 
        title="MSE" 
        value={formatMetric(regMetrics.mse)} 
        icon={<Zap className="w-4 h-4 text-blue-600" />} 
        tooltip="Mean Squared Error. Lower is better."
      />
      <MetricCard 
        title="Expl. Variance" 
        value={formatMetric(regMetrics.explained_variance)} 
        icon={<CheckCircle className="w-4 h-4 text-blue-600" />} 
        tooltip="Explained Variance Score. Higher is better."
      />
    </div>
  );
}

function MetricCard({ title, value, icon, tooltip }: { title: string; value: string; icon: React.ReactNode; tooltip: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3 group relative">
      <div className="flex items-center gap-1.5 mb-2">
        {icon}
        <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider">{title}</h4>
      </div>
      <p className="text-xl font-bold text-slate-900">{value}</p>
      
      <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute z-10 bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-slate-800 text-white text-xs rounded shadow-lg pointer-events-none">
        {tooltip}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800"></div>
      </div>
    </div>
  );
}
