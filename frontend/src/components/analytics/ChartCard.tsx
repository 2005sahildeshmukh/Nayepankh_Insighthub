"use client";

import React, { useMemo } from "react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, ScatterChart, Scatter, PieChart, Pie, Cell, AreaChart, Area
} from "recharts";
import { ChartSpecification } from "@/lib/api/analytics";
import { Info, AlertCircle } from "lucide-react";

interface ChartCardProps {
  spec: ChartSpecification;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899'];

export const ChartCard: React.FC<ChartCardProps> = ({ spec }) => {
  const validationResult = useMemo(() => {
    if (!spec.data || spec.data.length === 0) return { valid: false, error: "Empty data array", missingKeys: [] };
    if (!spec.x_key) return { valid: false, error: "Missing x_key in specification", missingKeys: ["x_key"] };
    
    const missingKeys: string[] = [];
    const firstRow = spec.data[0] as Record<string, unknown>;
    
    if (!(spec.x_key in firstRow)) {
      missingKeys.push(spec.x_key);
    }
    
    let hasValidNumeric = false;
    spec.series.forEach(s => {
      if (!s.dataKey) {
        missingKeys.push("series.dataKey");
      } else {
        if (!(s.dataKey in firstRow)) {
          missingKeys.push(s.dataKey);
        }
        const hasNum = spec.data.some(row => {
          const v = (row as Record<string, unknown>)[s.dataKey];
          return typeof v === 'number' && Number.isFinite(v);
        });
        if (hasNum) hasValidNumeric = true;
      }
    });
    
    if (missingKeys.length > 0) {
      if (process.env.NODE_ENV === "development") {
        console.warn(`[Chart Render Warning] Chart ID: ${spec.id}, Type: ${spec.chart_type}, Missing keys: ${missingKeys.join(", ")}`);
      }
      return { valid: false, error: "Chart data could not be rendered because its data keys do not match the chart specification.", missingKeys };
    }
    
    if (!hasValidNumeric && spec.chart_type !== 'scatter') {
      return { valid: false, error: "Chart data could not be rendered because its data keys do not match the chart specification.", missingKeys: [] };
    }
    
    return { valid: true, error: "", missingKeys: [] };
  }, [spec]);

  const renderChart = () => {
    if (!validationResult.valid) {
      return (
        <div className="flex h-[300px] flex-col items-center justify-center text-amber-600 bg-amber-50 rounded-lg border border-amber-200 p-6 text-center">
          <AlertCircle className="w-6 h-6 mb-2" />
          <p className="text-sm font-medium">{validationResult.error}</p>
        </div>
      );
    }

    const xKey = spec.x_key!;

    switch (spec.chart_type) {
      case "bar":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={spec.data} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip cursor={{ fill: '#f1f5f9' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {spec.series.map((s, idx) => (
                <Bar key={s.dataKey} dataKey={s.dataKey} name={s.name} fill={s.color || COLORS[idx % COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      case "horizontal_bar":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart layout="vertical" data={spec.data} margin={{ top: 10, right: 30, left: 40, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
              <YAxis dataKey={xKey} type="category" tick={{ fontSize: 12 }} width={120} />
              <Tooltip cursor={{ fill: '#f1f5f9' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {spec.series.map((s, idx) => (
                <Bar key={s.dataKey} dataKey={s.dataKey} name={s.name} fill={s.color || COLORS[idx % COLORS.length]} radius={[0, 4, 4, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      case "line":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={spec.data} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {spec.series.map((s, idx) => (
                <Line key={s.dataKey} type="monotone" dataKey={s.dataKey} name={s.name} stroke={s.color || COLORS[idx % COLORS.length]} strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
      case "area":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={spec.data} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {spec.series.map((s, idx) => (
                <Area key={s.dataKey} type="monotone" dataKey={s.dataKey} name={s.name} fill={s.color || COLORS[idx % COLORS.length]} stroke={s.color || COLORS[idx % COLORS.length]} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );
      case "histogram":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={spec.data} margin={{ top: 10, right: 30, left: 0, bottom: 30 }} barCategoryGap={0}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xKey} tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip cursor={{ fill: '#f1f5f9' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {spec.series.map((s, idx) => (
                <Bar key={s.dataKey} dataKey={s.dataKey} name={s.name} fill={s.color || COLORS[idx % COLORS.length]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      case "scatter":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid />
              <XAxis type="number" dataKey={xKey} name={spec.labels?.x || "X"} tick={{ fontSize: 12 }} />
              <YAxis type="number" dataKey={spec.series[0]?.dataKey || "y"} name={spec.labels?.y || "Y"} tick={{ fontSize: 12 }} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {spec.series.map((s, idx) => (
                <Scatter key={s.dataKey} name={s.name} data={spec.data} fill={s.color || COLORS[idx % COLORS.length]} />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        );
      case "donut":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={spec.data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey={spec.series[0]?.dataKey || "value"}
                nameKey={xKey}
              >
                {spec.data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend layout="horizontal" verticalAlign="bottom" align="center" wrapperStyle={{ fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        );
      default:
        return (
          <div className="flex h-[300px] items-center justify-center text-slate-500 bg-slate-50 rounded-lg border border-slate-200">
            <AlertCircle className="w-5 h-5 mr-2" /> Unsupported chart type: {spec.chart_type}
          </div>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="mb-6">
        <h3 className="font-semibold text-slate-900 text-lg mb-1">{spec.title}</h3>
        {spec.description && <p className="text-sm text-slate-500">{spec.description}</p>}
        {spec.reason && (
          <div className="mt-2 text-xs flex items-start text-slate-400">
            <Info className="w-3.5 h-3.5 mr-1.5 mt-0.5 shrink-0" />
            <span>{spec.reason}</span>
          </div>
        )}
        {spec.warning && (
          <div className="mt-2 text-xs flex items-start text-amber-600 bg-amber-50 p-2 rounded border border-amber-100">
            <AlertCircle className="w-3.5 h-3.5 mr-1.5 shrink-0" />
            <span>{spec.warning}</span>
          </div>
        )}
      </div>
      <div className="-ml-4 -mr-2">
        {renderChart()}
      </div>
    </div>
  );
};
