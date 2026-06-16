import React from 'react';
import { Database, LayoutGrid, Target, Activity, Clock, Award, Box, AlertTriangle } from 'lucide-react';
import { MlModelSummaryData } from './types';

interface Props {
  summary: MlModelSummaryData;
  isRestored: boolean;
}

export function MlModelSummary({ summary, isRestored }: Props) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          {isRestored ? (
            <>
              <Clock className="w-5 h-5 text-purple-600" />
              Loaded Saved Experiment
            </>
          ) : summary.status === 'completed' ? (
            <>
              <Activity className="w-5 h-5 text-green-600" />
              Training Complete
            </>
          ) : (
            <>
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Experiment Incomplete
            </>
          )}
        </h2>
        
        <div className="mt-4 grid grid-cols-2 md:flex md:flex-row gap-x-6 gap-y-2 text-sm text-slate-600">
          <div className="flex items-center gap-1.5">
            <Database className="w-4 h-4 text-slate-400" />
            <span className="font-medium text-slate-900">{summary.datasetName}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <LayoutGrid className="w-4 h-4 text-slate-400" />
            <span className="capitalize">{summary.view} View</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Target className="w-4 h-4 text-slate-400" />
            <span>Target: <span className="font-medium text-slate-900">{summary.target}</span></span>
          </div>
          <div className="flex items-center gap-1.5 capitalize">
            {summary.task}
          </div>
        </div>
      </div>
      
      <div className="flex flex-col items-end gap-2 border-t md:border-t-0 md:border-l border-slate-200 pt-4 md:pt-0 md:pl-6 w-full md:w-auto">
        <div className="flex items-center gap-2 text-sm">
          <Award className="w-4 h-4 text-purple-600" />
          <span className="text-slate-600">Selected Model:</span>
          <span className="font-bold text-slate-900">{summary.bestModelName || 'None'}</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <Box className={`w-3.5 h-3.5 ${summary.artifactAvailable ? 'text-green-500' : 'text-slate-400'}`} />
          <span className={summary.artifactAvailable ? 'text-slate-600' : 'text-slate-400'}>
            {summary.artifactAvailable ? 'Artifact available' : 'Artifact unavailable'}
          </span>
        </div>
        <div className="text-xs text-slate-500 mt-1">
          {new Date(summary.createdAt).toLocaleString()}
        </div>
      </div>
    </div>
  );
}
