import React from 'react';
import { MlFeatureImportanceItem, MlPredictionSchemaItem } from './types';

interface Props {
  featureImportance: MlFeatureImportanceItem[];
  predictionSchema?: MlPredictionSchemaItem[];
}

export function MlFeatureImportance({ featureImportance, predictionSchema }: Props) {
  if (!featureImportance || featureImportance.length === 0) {
    return null;
  }

  // Sort and take top 10
  const sorted = [...featureImportance]
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 10);
    
  if (sorted.length === 0) return null;
  
  const maxImportance = sorted[0].importance;

  const formatFeatureName = (feature: string) => {
    if (!predictionSchema) return feature;
    
    // First, try exact match
    const exactMatch = predictionSchema.find(s => s.name === feature);
    if (exactMatch && exactMatch.display_name) return exactMatch.display_name;

    // Then try prefix match for one-hot encoded categories (e.g., plan_type_Basic)
    for (const item of predictionSchema) {
      const prefix = `${item.name}_`;
      if (feature.startsWith(prefix)) {
        const category = feature.slice(prefix.length);
        return `${item.display_name || item.name}: ${category}`;
      }
    }
    
    return feature;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 h-full flex flex-col">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">Top Feature Importance</h3>
      <div className="flex-1 overflow-auto space-y-3">
        {sorted.map(fi => {
          // Calculate width relative to the max importance, but cap at 100% just in case
          const pct = Math.min((fi.importance / (maxImportance || 1)) * 100, 100);
          const displayName = formatFeatureName(fi.feature);
          return (
            <div key={fi.feature}>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="font-medium text-slate-700 truncate mr-2" title={displayName}>{displayName}</span>
                <span className="text-slate-500 font-mono">{fi.importance.toFixed(4)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-purple-500 h-full rounded-full transition-all duration-500" 
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
