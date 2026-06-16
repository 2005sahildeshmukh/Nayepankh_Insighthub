"use client";

import React, { useEffect, useState } from "react";
import { Dataset } from "@/lib/api/datasets";

type MlDatasetSelectorProps = {
  workspaceId: string;
  selectedDatasetId: string | null;
  onDatasetSelect: (datasetId: string) => void;
};

export default function MlDatasetSelector({ workspaceId, selectedDatasetId, onDatasetSelect }: MlDatasetSelectorProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchDatasets() {
      setIsLoading(true);
      try {
        const res = await fetch(`/backend-api/api/v1/workspaces/${workspaceId}/datasets`);
        if (res.ok) {
          const data = await res.json();
          // Filter only ready datasets
          const readyDatasets = data.filter((d: Dataset) => d.status === "ready");
          if (cancelled) return;
          
          setDatasets(readyDatasets);
          
          if (!selectedDatasetId && readyDatasets.length > 0) {
            if (typeof onDatasetSelect !== "function") {
              console.error("MlDatasetSelector requires a valid onDatasetSelect callback.");
              return;
            }
            onDatasetSelect(readyDatasets[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to fetch datasets", err);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    
    if (workspaceId) {
      fetchDatasets();
    }

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]); // Removed selectedDatasetId and onDatasetSelect from deps to avoid render loop

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (typeof onDatasetSelect !== "function") {
      console.error("MlDatasetSelector requires a valid onDatasetSelect callback.");
      return;
    }
    onDatasetSelect(e.target.value);
  };

  if (isLoading) {
    return <div className="animate-pulse h-10 bg-slate-100 rounded-md w-64 border border-slate-200"></div>;
  }

  if (datasets.length === 0) {
    return <div className="text-sm text-slate-500 py-2">No ready datasets available in this workspace.</div>;
  }

  return (
    <div className="flex items-center space-x-3">
      <label htmlFor="ml-dataset-selector" className="text-sm font-medium text-slate-700">Select Dataset:</label>
      <select
        id="ml-dataset-selector"
        value={selectedDatasetId || ""}
        onChange={handleChange}
        className="block w-64 rounded-md border-slate-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 sm:text-sm py-2 px-3 border bg-white"
      >
        <option value="" disabled>-- Select a dataset --</option>
        {datasets.map((d) => (
          <option key={d.id} value={d.id}>{d.name}</option>
        ))}
      </select>
    </div>
  );
}
