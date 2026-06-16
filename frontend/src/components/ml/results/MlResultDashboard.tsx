import React from 'react';
import { MlExperimentViewModel, MlClassificationMetrics, MlRegressionMetrics } from './types';
import { MlModelSummary } from './MlModelSummary';
import { MlBaselineComparison } from './MlBaselineComparison';
import { MlMetricCards } from './MlMetricCards';
import { MlConfusionMatrix } from './MlConfusionMatrix';
import { MlPerClassMetrics } from './MlPerClassMetrics';
import { MlRocCurve } from './MlRocCurve';
import { MlClassDistribution } from './MlClassDistribution';
import { MlFeatureImportance } from './MlFeatureImportance';
import { MlLeaderboard } from './MlLeaderboard';
import { MlPredictionSandbox } from './MlPredictionSandbox';
import { MlActualVsPredicted } from './MlActualVsPredicted';
import { MlResidualPlot } from './MlResidualPlot';
import { MlTechnicalDetails } from './MlTechnicalDetails';

interface Props {
  viewModel: MlExperimentViewModel;
  workspaceId: string;
  experimentId: string;
  onNewExperiment: () => void;
}

export function MlResultDashboard({ viewModel, workspaceId, experimentId, onNewExperiment }: Props) {
  const { summary, leaderboard, baselineComparison, testMetrics, baselineMetrics, featureImportance, predictionSchema, isClassification, isRestored, rawEvaluationJson, legacyPreprocessingWarnings } = viewModel;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <MlModelSummary summary={summary} isRestored={isRestored} />
        </div>
        <button 
          onClick={onNewExperiment}
          className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg whitespace-nowrap"
        >
          New Experiment
        </button>
      </div>

      {legacyPreprocessingWarnings && legacyPreprocessingWarnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <div className="text-amber-600 mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-amber-800 mb-1">Legacy preprocessing warning</h4>
              <ul className="text-sm text-amber-700 space-y-1">
                {legacyPreprocessingWarnings.map((w, i) => (
                  <li key={i}>{w.message}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <MlBaselineComparison 
        comparison={baselineComparison} 
        isClassification={isClassification}
        metrics={isClassification ? testMetrics as unknown as MlClassificationMetrics : null}
        baselineMetrics={isClassification ? baselineMetrics as unknown as MlClassificationMetrics : null}
      />

      <MlMetricCards isClassification={isClassification} metrics={testMetrics} />

      {isClassification ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MlConfusionMatrix metrics={testMetrics as unknown as MlClassificationMetrics} />
          <div className="flex flex-col gap-6">
            <MlPerClassMetrics metrics={testMetrics as unknown as MlClassificationMetrics} />
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {isClassification ? (
          <MlRocCurve metrics={testMetrics as unknown as MlClassificationMetrics} />
        ) : (
          <MlActualVsPredicted metrics={testMetrics as unknown as MlRegressionMetrics} />
        )}
        <MlFeatureImportance featureImportance={featureImportance} predictionSchema={predictionSchema} />
      </div>

      {!isClassification && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MlResidualPlot metrics={testMetrics as unknown as MlRegressionMetrics} />
        </div>
      )}

      {isClassification && (testMetrics as unknown as MlClassificationMetrics).class_distribution && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MlClassDistribution metrics={testMetrics as unknown as MlClassificationMetrics} />
        </div>
      )}

      <MlLeaderboard leaderboard={leaderboard} primaryMetricName={baselineComparison.primaryMetricName} />

      <MlPredictionSandbox schema={predictionSchema} workspaceId={workspaceId} experimentId={experimentId} />

      <MlTechnicalDetails json={rawEvaluationJson} />
    </div>
  );
}
