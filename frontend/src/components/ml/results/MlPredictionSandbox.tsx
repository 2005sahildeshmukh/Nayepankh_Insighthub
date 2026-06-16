import React, { useState } from 'react';
import { Loader2, AlertTriangle, Info, Brain } from 'lucide-react';
import { MlPredictionSchemaItem } from './types';
import { MLService } from '@/lib/api/ml';

interface Props {
  schema: MlPredictionSchemaItem[];
  workspaceId: string;
  experimentId: string;
}

export function MlPredictionSandbox({ schema, workspaceId, experimentId }: Props) {
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [predictionResult, setPredictionResult] = useState<any | null>(null);

  // Validate the schema
  const isSchemaMissing = !schema || schema.length === 0;
  const hasMissingCategories = schema?.some(item => item.input_type === 'select' && (!item.categories || item.categories.length === 0));
  const invalidField = schema?.find(item => !item.name || typeof item.name !== 'string' || item.name.trim() === '');
  const isValidSchema = !isSchemaMissing && !hasMissingCategories && !invalidField;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 mt-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Prediction Sandbox</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Side: Form */}
        <div className="space-y-4">
          {!isValidSchema && (
            <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg text-orange-800 text-sm mb-4 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <p>
                {isSchemaMissing 
                  ? "Prediction schema is missing. Prediction is disabled."
                  : hasMissingCategories 
                  ? "One or more categorical fields are missing their category options. Prediction is disabled." 
                  : `One prediction field could not be restored: ${invalidField?.name || 'Unknown'}. Prediction is disabled.`}
              </p>
            </div>
          )}
          
          {predictionError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm mb-4">
              {predictionError}
            </div>
          )}
          
          {schema?.map(f => {
            const isSelect = f.input_type === 'select';
            const hasCategories = Array.isArray(f.categories) && f.categories.length > 0;
            const isDate = f.input_type === 'date';
            const isNumeric = f.input_type === 'integer' || f.input_type === 'decimal';
            const isBool = f.input_type === 'boolean';
            
            // Skip rendering unnamed controls
            if (!f.name || !f.display_name) return null;

            return (
              <div key={`predict:${f.name}`}>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  {f.display_name} <span className="text-slate-400 text-xs ml-1">({f.input_type})</span>
                </label>
                {isSelect ? (
                  <select
                    id={`predict_${f.name}`}
                    className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-purple-500 focus:border-purple-500 bg-white disabled:opacity-50"
                    defaultValue=""
                    disabled={!hasCategories}
                  >
                    <option value="" disabled>Select {f.display_name}...</option>
                    {hasCategories && f.categories!.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                ) : isBool ? (
                  <select
                    id={`predict_${f.name}`}
                    className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-purple-500 focus:border-purple-500 bg-white"
                    defaultValue=""
                  >
                    <option value="" disabled>Select {f.display_name}...</option>
                    <option value="true">True</option>
                    <option value="false">False</option>
                  </select>
                ) : isDate ? (
                  <input 
                    type="date"
                    className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-purple-500 focus:border-purple-500"
                    id={`predict_${f.name}`}
                  />
                ) : (
                  <input 
                    type={isNumeric ? 'number' : 'text'}
                    step={f.step ?? (f.input_type === 'integer' ? "1" : "any")}
                    min={f.minimum ?? undefined}
                    max={f.maximum ?? undefined}
                    className="w-full rounded-lg border-slate-300 border p-2 text-sm focus:ring-purple-500 focus:border-purple-500"
                    placeholder={`Enter ${f.display_name}`}
                    id={`predict_${f.name}`}
                  />
                )}
              </div>
            );
          })}
          
          <button 
            onClick={async () => {
              setPredictionError(null);
              setIsPredicting(true);
              
              const features: Record<string, unknown> = {};
              let hasError = false;
              
              schema?.forEach(f => {
                if (!f.name) return;
                const el = document.getElementById(`predict_${f.name}`) as HTMLInputElement | HTMLSelectElement;
                if (el && el.value) {
                  if (f.input_type === 'integer' || f.input_type === 'decimal') {
                     const val = Number(el.value);
                     if (isNaN(val)) {
                       setPredictionError(`Invalid number for ${f.display_name}`);
                       hasError = true;
                     }
                     features[f.name] = val;
                  } else if (f.input_type === 'boolean') {
                     features[f.name] = el.value === 'true';
                  } else {
                     features[f.name] = el.value;
                  }
                }
              });
              
              if (hasError) {
                setIsPredicting(false);
                return;
              }
              
              try {
                const res = await MLService.predict(workspaceId, experimentId, features);
                setPredictionResult(res);
              } catch (e: unknown) {
                setPredictionError("Prediction failed: " + (e instanceof Error ? e.message : String(e)));
              } finally {
                setIsPredicting(false);
              }
            }}
            disabled={isPredicting || !isValidSchema}
            className="w-full bg-slate-900 text-white font-medium py-2 rounded-lg hover:bg-slate-800 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isPredicting && <Loader2 className="w-4 h-4 animate-spin" />}
            Predict
          </button>
        </div>
        
        {/* Right Side: Result Panel */}
        <div className="bg-slate-50 border border-slate-100 rounded-lg p-6 flex flex-col h-full">
          {predictionResult ? (
            <div className="flex-1 flex flex-col">
               <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Prediction</h4>
               <div className="text-3xl font-bold text-slate-900 mb-6">
                  {String(predictionResult.prediction)}
               </div>
               
               {predictionResult.probabilities && predictionResult.probabilities.length > 0 && (
                 <div className="mb-6">
                   <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Class Probabilities</h4>
                   <div className="space-y-3">
                     {predictionResult.probabilities.map((p: { label: string, probability: number }) => (
                       <div key={p.label}>
                         <div className="flex justify-between text-sm mb-1">
                           <span className="font-medium text-slate-700">{p.label}</span>
                           <span className="text-slate-600 font-medium">{(p.probability * 100).toFixed(1)}%</span>
                         </div>
                         <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                           <div className="bg-purple-500 h-full" style={{ width: `${p.probability * 100}%` }} />
                         </div>
                       </div>
                     ))}
                   </div>
                 </div>
               )}
               
               {predictionResult.low_confidence && (
                 <div className="mb-6 p-3 bg-orange-50 border border-orange-200 rounded-lg flex gap-2 text-orange-800 text-sm">
                   <AlertTriangle className="w-5 h-5 shrink-0" />
                   <div>
                     <p className="font-semibold">Low Confidence</p>
                     <p>{predictionResult.confidence_message}</p>
                   </div>
                 </div>
               )}
               
               {predictionResult.input_validation_warnings?.length > 0 && (
                 <div className="mb-6">
                   <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Input Warnings</h4>
                   <div className="space-y-2">
                     {predictionResult.input_validation_warnings.map((w: string, i: number) => (
                       <div key={i} className="text-xs text-orange-700 bg-orange-50 border border-orange-100 p-2 rounded">
                         {w}
                       </div>
                     ))}
                   </div>
                 </div>
               )}
               
               <div className="mt-auto pt-4 border-t border-slate-200">
                 <p className="text-xs text-slate-500 flex items-start gap-1">
                   <Info className="w-4 h-4 shrink-0" />
                   {predictionResult.disclaimer || predictionResult.limitation || "This prediction is a model estimate and is not a guaranteed decision."}
                 </p>
               </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Brain className="w-12 h-12 text-slate-300 mb-4" />
              <p className="text-slate-500">Enter feature values and click Predict to see the model&apos;s output.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
