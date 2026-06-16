from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional, Literal, Union

# ----------------- FILTERS -----------------

FilterOperator = Literal[
    "equals", "not_equals", "in", 
    "gt", "gte", "lt", "lte", "between",
    "on_or_after", "on_or_before", 
    "is_missing", "is_not_missing",
    "contains", "not_contains"
]

class AnalyticsFilter(BaseModel):
    column: str = Field(..., description="The final mapped column name")
    operator: FilterOperator
    value: Any = None

    @model_validator(mode="after")
    def validate_list_operators(self):
        if self.operator in ("in", "between"):
            if not isinstance(self.value, list):
                raise ValueError(f"Operator '{self.operator}' requires an array/list value")
            if self.operator == "between" and len(self.value) != 2:
                raise ValueError("Operator 'between' requires an array/list of exactly 2 items")
        return self

# ----------------- KPI -----------------

class AnalyticsKPI(BaseModel):
    id: str
    title: str
    value: Any
    formatted_value: str
    source_column: Optional[str] = None
    aggregation: str
    description: Optional[str] = None

# ----------------- CHARTS -----------------

class ChartSeries(BaseModel):
    name: str
    dataKey: str
    color: Optional[str] = None

class ChartSpecification(BaseModel):
    id: str
    chart_type: Literal["bar", "horizontal_bar", "line", "area", "histogram", "scatter", "donut"]
    title: str
    description: Optional[str] = None
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    x_key: Optional[str] = None
    y_key: Optional[str] = None
    aggregation: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict) # e.g. {"x": "Category", "y": "Count"}
    series: List[ChartSeries] = Field(default_factory=list)
    data: List[Dict[str, Any]] = Field(default_factory=list)
    reason: Optional[str] = None
    warning: Optional[str] = None

# ----------------- INSIGHTS -----------------

class Insight(BaseModel):
    id: str
    type: Literal["dominant_category", "high_category", "trend", "change", "correlation", "concentration", "distribution", "limitation"]
    title: str
    statement: str
    evidence: str
    source_columns: List[str]
    reliability: Literal["High", "Medium", "Limited"]
    limitation: Optional[str] = None

# ----------------- CORRELATION -----------------

class CorrelationResponse(BaseModel):
    included_columns: List[str]
    labels: List[str]
    values: List[List[Optional[float]]]
    strongest_positive: Optional[Dict[str, Any]] = None
    strongest_negative: Optional[Dict[str, Any]] = None
    excluded_columns: Dict[str, str] = Field(default_factory=dict)
    limitation_note: str = "Correlation describes association, not causation."

# ----------------- REQUESTS & RESPONSES -----------------

class AnalyticsBaseRequest(BaseModel):
    view: Literal["mapped", "working"] = "mapped"
    filters: List[AnalyticsFilter] = Field(default_factory=list)
    top_n: Optional[int] = 10

class CustomChartRequest(AnalyticsBaseRequest):
    chart_type: Literal["bar", "horizontal_bar", "line", "area", "histogram", "scatter", "donut"]
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    aggregation: Optional[str] = None
    time_granularity: Optional[Literal["day", "week", "month", "quarter", "year"]] = None

class CustomChartResponse(BaseModel):
    specification: ChartSpecification
    warnings: List[str] = Field(default_factory=list)

class AnalyticsOverview(BaseModel):
    dataset_name: str
    view: Literal["mapped", "working"]
    row_count: int
    column_count: int
    numeric_count: int
    text_categorical_count: int
    datetime_count: int
    boolean_count: int
    missing_cells: int
    date_range: Optional[Dict[str, str]] = None
    has_cleaning_plan: bool

class AnalyticsDashboardResponse(BaseModel):
    overview: AnalyticsOverview
    filtered_row_count: int
    kpis: List[AnalyticsKPI]
    recommended_charts: List[ChartSpecification]
    insights: List[Insight]
    correlation_summary: Optional[CorrelationResponse] = None
    warnings: List[str] = Field(default_factory=list)

class AnalyticsMetadataResponse(BaseModel):
    columns: List[Dict[str, Any]]
    has_cleaning_plan: bool
