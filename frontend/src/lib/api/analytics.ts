export interface AnalyticsFilter {
  column: string;
  operator: 'equals' | 'not_equals' | 'in' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'on_or_after' | 'on_or_before' | 'is_missing' | 'is_not_missing' | 'contains' | 'not_contains';
  value?: unknown;
}

export interface AnalyticsMetadataResponse {
  columns: {
    name: string;
    role: string;
    inferred_type: string;
    is_identifier_like: boolean;
  }[];
  has_cleaning_plan: boolean;
}

export interface AnalyticsKPI {
  id: string;
  title: string;
  value: unknown;
  formatted_value: string;
  source_column: string | null;
  aggregation: string;
  description: string | null;
}

export interface ChartSeries {
  name: string;
  dataKey: string;
  color?: string;
}

export interface ChartSpecification {
  id: string;
  chart_type: 'bar' | 'horizontal_bar' | 'line' | 'area' | 'histogram' | 'scatter' | 'donut';
  title: string;
  description: string | null;
  x_column: string | null;
  y_column: string | null;
  x_key: string | null;
  y_key: string | null;
  aggregation: string | null;
  labels: Record<string, string>;
  series: ChartSeries[];
  data: Record<string, unknown>[];
  reason: string | null;
  warning: string | null;
}

export interface Insight {
  id: string;
  type: string;
  title: string;
  statement: string;
  evidence: string;
  source_columns: string[];
  reliability: string;
  limitation: string | null;
}

export interface CorrelationResponse {
  included_columns: string[];
  labels: string[];
  values: (number | null)[][];
  strongest_positive: { cols: string[]; value: number } | null;
  strongest_negative: { cols: string[]; value: number } | null;
  excluded_columns: Record<string, string>;
  limitation_note: string | null;
}

export interface AnalyticsOverview {
  dataset_name: string;
  view: string;
  row_count: number;
  column_count: number;
  numeric_count: number;
  text_categorical_count: number;
  datetime_count: number;
  boolean_count: number;
  missing_cells: number;
  date_range: { start: string; end: string } | null;
  has_cleaning_plan: boolean;
}

export interface AnalyticsDashboardResponse {
  overview: AnalyticsOverview;
  filtered_row_count: number;
  kpis: AnalyticsKPI[];
  recommended_charts: ChartSpecification[];
  insights: Insight[];
  correlation_summary: CorrelationResponse;
  warnings: string[];
}

export interface CustomChartRequest {
  view: 'mapped' | 'working';
  filters: AnalyticsFilter[];
  chart_type: string;
  x_column?: string;
  y_column?: string;
  aggregation?: string;
  time_granularity?: string;
  top_n?: number;
}

export interface CustomChartResponse {
  specification: ChartSpecification;
  warnings: string[];
}

export const getAnalyticsMetadata = async (
  workspaceId: string,
  datasetId: string,
  view: 'mapped' | 'working' = 'mapped'
): Promise<AnalyticsMetadataResponse> => {
  const res = await fetch(`/backend-api/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/analytics/metadata?view=${view}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch analytics metadata');
  }
  return res.json();
};

export const getAnalyticsDashboard = async (
  workspaceId: string,
  datasetId: string,
  view: 'mapped' | 'working',
  filters: AnalyticsFilter[] = []
): Promise<AnalyticsDashboardResponse> => {
  const res = await fetch(`/backend-api/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/analytics/dashboard`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ view, filters })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch analytics dashboard');
  }
  return res.json();
};

export const getCustomChart = async (
  workspaceId: string,
  datasetId: string,
  request: CustomChartRequest
): Promise<CustomChartResponse> => {
  const res = await fetch(`/backend-api/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/analytics/custom-chart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch custom chart');
  }
  return res.json();
};

export const getCorrelation = async (
  workspaceId: string,
  datasetId: string,
  view: 'mapped' | 'working',
  filters: AnalyticsFilter[] = []
): Promise<CorrelationResponse> => {
  const res = await fetch(`/backend-api/api/v1/workspaces/${workspaceId}/datasets/${datasetId}/analytics/correlation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ view, filters })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch correlation matrix');
  }
  return res.json();
};
