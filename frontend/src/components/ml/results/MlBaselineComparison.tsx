import React from 'react';
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { MlBaselineComparisonData, MlClassificationMetrics } from './types';
import { formatMetric } from './formatters';

interface Props {
  comparison: MlBaselineComparisonData;
  isClassification: boolean;
  metrics: MlClassificationMetrics | null;
  baselineMetrics: MlClassificationMetrics | null;
}

export function MlBaselineComparison({ comparison, isClassification, metrics, baselineMetrics }: Props) {
  const { baselineMetric, candidateMetric, testMetric, primaryMetricName, direction } = comparison;
  
  if (baselineMetric === null || candidateMetric === null) {
    return null;
  }
  
  const isBetter = direction === 'higher_is_better' 
    ? candidateMetric > baselineMetric 
    : candidateMetric < baselineMetric;
    
  const improvement = Math.abs(candidateMetric - baselineMetric);
  const relativeImprovement = baselineMetric !== 0 ? (improvement / Math.abs(baselineMetric)) * 100 : 0;
  
  // Log loss probability quality check
  let showLogLossWarning = false;
  if (isClassification && metrics?.log_loss !== undefined && baselineMetrics?.log_loss !== undefined) {
    // Only show if binary classification (can infer if roc_auc exists and not empty matrix)
    const isBinary = metrics.confusion_matrix?.labels?.length === 2;
    if (isBinary && metrics.log_loss > baselineMetrics.log_loss) {
      showLogLossWarning = true;
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col justify-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Baseline CV ({primaryMetricName})</p>
          <p className="text-2xl font-bold text-slate-700">{formatMetric(baselineMetric)}</p>
        </div>
        
        <div className={`border rounded-xl p-4 flex flex-col justify-center ${isBetter ? 'bg-green-50 border-green-200' : 'bg-orange-50 border-orange-200'}`}>
          <p className={`text-xs font-medium uppercase tracking-wider mb-1 ${isBetter ? 'text-green-700' : 'text-orange-700'}`}>
            Candidate CV ({primaryMetricName})
          </p>
          <div className="flex items-end gap-2">
            <p className={`text-2xl font-bold ${isBetter ? 'text-green-800' : 'text-orange-800'}`}>
              {formatMetric(candidateMetric)}
            </p>
            {isBetter ? (
              direction === 'lower_is_better' 
                ? <TrendingDown className="w-5 h-5 text-green-600 mb-1" />
                : <TrendingUp className="w-5 h-5 text-green-600 mb-1" />
            ) : (
              direction === 'lower_is_better'
                ? <TrendingUp className="w-5 h-5 text-orange-600 mb-1" />
                : <TrendingDown className="w-5 h-5 text-orange-600 mb-1" />
            )}
          </div>
        </div>
        
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col justify-center">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">
            {direction === 'lower_is_better' ? `${primaryMetricName} Reduction` : 'Improvement'}
          </p>
          <div className="flex items-center gap-1 text-slate-700">
            {isBetter ? '+' : '-'}{formatMetric(improvement)}
            {relativeImprovement > 0 && (
              <span className="text-xs font-medium text-slate-400 bg-slate-200 px-1.5 py-0.5 rounded ml-1">
                {direction === 'lower_is_better' ? 'Relative reduction: ' : ''}{formatMetric(relativeImprovement, 1)}%
              </span>
            )}
            {improvement === 0 && <Minus className="w-4 h-4 text-slate-400" />}
          </div>
          {direction === 'lower_is_better' && (
            <p className="text-xs text-slate-400 mt-1">Lower is better</p>
          )}
        </div>
        
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex flex-col justify-center">
          <p className="text-xs text-purple-700 font-medium uppercase tracking-wider mb-1">Final Test ({primaryMetricName})</p>
          <p className="text-2xl font-bold text-purple-800">{formatMetric(testMetric)}</p>
        </div>
      </div>
      
      {showLogLossWarning && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3 text-amber-800">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-amber-600" />
          <p className="text-sm">
            <strong>Probability Quality Warning:</strong> The selected model improves one or more class-decision metrics, but its probability estimates have worse log loss than the baseline. Treat probabilities cautiously.
          </p>
        </div>
      )}
    </div>
  );
}
