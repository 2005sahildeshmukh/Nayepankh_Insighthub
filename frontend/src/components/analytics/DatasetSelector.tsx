"use client";

import React, { useEffect, useState } from "react";
import { Dataset } from "@/lib/api/datasets";

interface DatasetSelectorProps {
  workspaceId: string;
  selectedDatasetId: string | null;
  onDatasetSelect: (datasetId: string) => void;
}

export const DatasetSelector: React.FC<DatasetSelectorProps> = ({ workspaceId, selectedDatasetId, onDatasetSelect }) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDatasets = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`/backend-api/api/v1/workspaces/${workspaceId}/datasets`);
        if (res.ok) {
          const data = await res.json();
          // Filter only ready datasets
          const readyDatasets = data.filter((d: Dataset) => d.status === "ready");
          setDatasets(readyDatasets);
          
          if (!selectedDatasetId && readyDatasets.length > 0) {
            onDatasetSelect(readyDatasets[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to fetch datasets", err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchDatasets();
  }, [workspaceId, selectedDatasetId, onDatasetSelect]);

  if (isLoading) {
    return <div className="animate-pulse h-10 bg-slate-100 rounded-md w-64"></div>;
  }

  if (datasets.length === 0) {
    return <div className="text-sm text-slate-500 py-2">No ready datasets available in this workspace.</div>;
  }

  return (
    <div className="flex items-center space-x-3">
      <label htmlFor="dataset-selector" className="text-sm font-medium text-slate-700">Select Dataset:</label>
      <select
        id="dataset-selector"
        value={selectedDatasetId || ""}
        onChange={(e) => onDatasetSelect(e.target.value)}
        className="block w-64 rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border bg-white"
      >
        <option value="" disabled>-- Select a dataset --</option>
        {datasets.map((d) => (
          <option key={d.id} value={d.id}>{d.name}</option>
        ))}
      </select>
    </div>
  );
};
