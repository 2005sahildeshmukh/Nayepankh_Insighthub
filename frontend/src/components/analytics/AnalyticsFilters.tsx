"use client";

import React, { useState } from "react";
import { AnalyticsFilter, AnalyticsMetadataResponse } from "@/lib/api/analytics";
import { Filter as FilterIcon, Plus, X } from "lucide-react";

interface AnalyticsFiltersProps {
  metadata: AnalyticsMetadataResponse | null;
  filters: AnalyticsFilter[];
  setFilters: (filters: AnalyticsFilter[]) => void;
  onApply: () => void;
}

export const AnalyticsFilters: React.FC<AnalyticsFiltersProps> = ({ metadata, filters, setFilters, onApply }) => {
  const [draftFilters, setDraftFilters] = useState<AnalyticsFilter[]>(filters);
  const [isExpanded, setIsExpanded] = useState(false);

  const [prevFilters, setPrevFilters] = useState<AnalyticsFilter[]>(filters);

  if (filters !== prevFilters) {
    setPrevFilters(filters);
    setDraftFilters(filters);
  }

  const addFilter = () => {
    if (!metadata || metadata.columns.length === 0) return;
    setDraftFilters([...draftFilters, { column: metadata.columns[0].name, operator: "equals", value: "" }]);
  };

  const updateFilter = (index: number, field: keyof AnalyticsFilter, value: unknown) => {
    const newFilters = [...draftFilters];
    
    if (field === "operator" && (value === "between" || value === "in")) {
       // Convert string to array for these operators if they are switching to them
       if (!Array.isArray(newFilters[index].value)) {
         newFilters[index].value = [newFilters[index].value, ""];
       }
    }
    
    newFilters[index] = { ...newFilters[index], [field]: value };
    setDraftFilters(newFilters);
  };

  const removeFilter = (index: number) => {
    setDraftFilters(draftFilters.filter((_, i) => i !== index));
  };

  const applyFilters = () => {
    setFilters(draftFilters);
    onApply();
  };

  const clearFilters = () => {
    setDraftFilters([]);
    setFilters([]);
    onApply(); // Immediate clear
  };

  const getOperatorsForRole = (role: string) => {
    switch (role) {
      case "integer":
      case "float":
        return [
          { value: "equals", label: "Equals" },
          { value: "not_equals", label: "Not Equals" },
          { value: "gt", label: ">" },
          { value: "gte", label: ">=" },
          { value: "lt", label: "<" },
          { value: "lte", label: "<=" },
          { value: "between", label: "Between" },
          { value: "is_missing", label: "Is Missing" },
          { value: "is_not_missing", label: "Is Not Missing" }
        ];
      case "datetime":
        return [
          { value: "on_or_after", label: "On or After" },
          { value: "on_or_before", label: "On or Before" },
          { value: "between", label: "Between" },
          { value: "is_missing", label: "Is Missing" },
          { value: "is_not_missing", label: "Is Not Missing" }
        ];
      default:
        return [
          { value: "equals", label: "Equals" },
          { value: "not_equals", label: "Not Equals" },
          { value: "in", label: "In (comma sep)" },
          { value: "contains", label: "Contains" },
          { value: "not_contains", label: "Not Contains" },
          { value: "is_missing", label: "Is Missing" },
          { value: "is_not_missing", label: "Is Not Missing" }
        ];
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 mb-6 overflow-hidden">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center text-slate-700 font-medium">
          <FilterIcon className="w-5 h-5 mr-2 text-indigo-500" />
          Data Filters
          {filters.length > 0 && (
            <span className="ml-3 bg-indigo-100 text-indigo-700 py-0.5 px-2 rounded-full text-xs">
              {filters.length} active
            </span>
          )}
        </div>
        <span className="text-sm text-slate-500">{isExpanded ? "Hide" : "Show"}</span>
      </button>

      {isExpanded && (
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          {draftFilters.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-sm bg-white rounded-lg border border-dashed border-slate-300">
              No filters applied. Add a filter to slice your data.
            </div>
          ) : (
            <div className="space-y-3 mb-4">
              {draftFilters.map((filter, index) => {
                const colMeta = metadata?.columns.find(c => c.name === filter.column);
                const role = colMeta?.role || "text";
                const operators = getOperatorsForRole(role);
                
                // Ensure valid operator is selected when column changes
                if (!operators.find(o => o.value === filter.operator)) {
                  filter.operator = operators[0].value as AnalyticsFilter["operator"];
                }

                const needsValue = !["is_missing", "is_not_missing"].includes(filter.operator);
                const isArrayInput = ["between", "in"].includes(filter.operator);

                return (
                  <div key={index} className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                    <select
                      value={filter.column}
                      onChange={(e) => updateFilter(index, "column", e.target.value)}
                      className="border-slate-300 rounded-md text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 min-w-[150px]"
                    >
                      {metadata?.columns.map(c => (
                        <option key={c.name} value={c.name}>{c.name}</option>
                      ))}
                    </select>

                    <select
                      value={filter.operator}
                      onChange={(e) => updateFilter(index, "operator", e.target.value)}
                      className="border-slate-300 rounded-md text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 min-w-[140px]"
                    >
                      {operators.map(op => (
                        <option key={op.value} value={op.value}>{op.label}</option>
                      ))}
                    </select>

                    {needsValue && !isArrayInput && (
                      <input
                        type={role === "datetime" ? "date" : role === "integer" || role === "float" ? "number" : "text"}
                        value={(filter.value as string | number) || ""}
                        onChange={(e) => updateFilter(index, "value", e.target.value)}
                        placeholder="Value..."
                        className="border-slate-300 rounded-md text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500 flex-1 min-w-[120px]"
                      />
                    )}
                    
                    {needsValue && isArrayInput && filter.operator === "between" && (
                      <div className="flex items-center space-x-2 flex-1">
                        <input
                          type={role === "datetime" ? "date" : "number"}
                          value={Array.isArray(filter.value) ? (filter.value[0] as string | number) : ""}
                          onChange={(e) => updateFilter(index, "value", [e.target.value, Array.isArray(filter.value) ? filter.value[1] : ""])}
                          placeholder="Min..."
                          className="border-slate-300 rounded-md text-sm shadow-sm w-full focus:border-indigo-500"
                        />
                        <span className="text-slate-500">to</span>
                        <input
                          type={role === "datetime" ? "date" : "number"}
                          value={Array.isArray(filter.value) ? (filter.value[1] as string | number) : ""}
                          onChange={(e) => updateFilter(index, "value", [Array.isArray(filter.value) ? filter.value[0] : "", e.target.value])}
                          placeholder="Max..."
                          className="border-slate-300 rounded-md text-sm shadow-sm w-full focus:border-indigo-500"
                        />
                      </div>
                    )}
                    
                    {needsValue && isArrayInput && filter.operator === "in" && (
                      <input
                        type="text"
                        value={Array.isArray(filter.value) ? filter.value.join(", ") : (filter.value as string) || ""}
                        onChange={(e) => updateFilter(index, "value", e.target.value.split(",").map(s => s.trim()).filter(Boolean))}
                        placeholder="Comma separated values..."
                        className="border-slate-300 rounded-md text-sm shadow-sm focus:border-indigo-500 flex-1 min-w-[150px]"
                      />
                    )}

                    <button
                      onClick={() => removeFilter(index)}
                      className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded transition-colors"
                      title="Remove filter"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex items-center justify-between">
            <button
              onClick={addFilter}
              className="inline-flex items-center px-3 py-1.5 border border-slate-300 shadow-sm text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Filter
            </button>
            <div className="flex space-x-3">
              <button
                onClick={clearFilters}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-slate-600 bg-slate-100 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500"
              >
                Clear All
              </button>
              <button
                onClick={applyFilters}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
