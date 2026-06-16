import pandas as pd
import numpy as np
import math
from typing import List, Dict, Any

from app.schemas.analytics import ChartSpecification, ChartSeries, CustomChartRequest, CustomChartResponse

class AnalyticsChartService:
    @staticmethod
    def _sanitize_for_json(val: Any) -> Any:
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (np.integer, int)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            if math.isnan(val) or math.isinf(val):
                return None
            return float(val)
        if isinstance(val, (np.bool_, bool)):
            return bool(val)
        if isinstance(val, pd.Timestamp):
            return val.isoformat()
        return str(val)

    @classmethod
    def generate_chart_recommendations(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]]) -> List[ChartSpecification]:
        charts = []
        
        measures = [c for c, m in roles.items() if m["role"] in ["integer", "float"] and not m["is_identifier_like"] and c in df.columns]
        categoricals = []
        for c, m in roles.items():
            if c not in df.columns: continue
            if m["is_identifier_like"]: continue
            if m["role"] == "categorical":
                categoricals.append(c)
            elif m["role"] == "text":
                if df[c].nunique(dropna=True) <= 20:
                    name_lower = str(c).lower()
                    if not any(k in name_lower for k in ["note", "comment", "desc", "detail"]):
                        categoricals.append(c)
                        
        datetimes = [c for c, m in roles.items() if m["role"] == "datetime" and c in df.columns]
        # 1. Bar Chart (Categorical distribution)
        for cat in categoricals[:2]: # max 2 bar charts from categoricals
            if len(charts) >= 8: break
            
            value_counts = df[cat].value_counts(dropna=True)
            if len(value_counts) == 0: continue
            
            top_10 = value_counts.head(10)
            other = value_counts.iloc[10:].sum()
            
            data = [{"category": str(k), "value": int(v)} for k, v in top_10.items()]
            if other > 0:
                data.append({"category": "Other", "value": int(other)})
                
            charts.append(ChartSpecification(
                id=f"chart_bar_{cat}",
                chart_type="horizontal_bar" if any(len(str(k)) > 15 for k in top_10.keys()) else "bar",
                title=f"Distribution of {cat.replace('_', ' ').title()}",
                description=f"Count of records by {cat}.",
                x_column=cat,
                y_column=None,
                x_key="category",
                y_key="value",
                aggregation="count",
                labels={"x": cat, "y": "Record Count"},
                series=[ChartSeries(name="Record Count", dataKey="value", color="#6366f1")],
                data=data,
                reason="Categorical dimension suitable for bar charts."
            ))

        # 2. Donut Chart (Low cardinality)
        for cat in categoricals:
            if len(charts) >= 8: break
            value_counts = df[cat].value_counts(dropna=True)
            if 0 < len(value_counts) <= 5:
                data = [{"category": str(k), "value": int(v)} for k, v in value_counts.items()]
                charts.append(ChartSpecification(
                    id=f"chart_donut_{cat}",
                    chart_type="donut",
                    title=f"{cat.replace('_', ' ').title()} Share",
                    description=f"Proportion of records by {cat}.",
                    x_column=cat,
                    y_column=None,
                    x_key="category",
                    y_key="value",
                    aggregation="count",
                    labels={"x": cat, "y": "Count"},
                    series=[ChartSeries(name="Count", dataKey="value", color="#8b5cf6")],
                    data=data,
                    reason="Low-cardinality categorical dimension suitable for donut chart."
                ))
                break # Just 1 donut chart

        # 3. Histogram (Numeric distribution)
        for num in measures[:2]:
            if len(charts) >= 8: break
            series = pd.to_numeric(df[num], errors='coerce').dropna()
            if len(series) > 1:
                counts, bin_edges = np.histogram(series, bins=min(20, len(series.unique())))
                data = []
                for i in range(len(counts)):
                    # Formatting bin label
                    label = f"{cls._sanitize_for_json(bin_edges[i])} - {cls._sanitize_for_json(bin_edges[i+1])}"
                    data.append({"bin": label, "count": int(counts[i])})
                charts.append(ChartSpecification(
                    id=f"chart_hist_{num}",
                    chart_type="histogram",
                    title=f"Distribution of {num.replace('_', ' ').title()}",
                    description=f"Frequency distribution of {num}.",
                    x_column=num,
                    y_column=None,
                    x_key="bin",
                    y_key="count",
                    aggregation="count",
                    labels={"x": num, "y": "Frequency"},
                    series=[ChartSeries(name="Frequency", dataKey="count", color="#3b82f6")],
                    data=data,
                    reason="Numeric measure distribution."
                ))

        # 4. Line Chart (Time series)
        if datetimes and len(charts) < 8:
            dt_col = datetimes[0]
            s_date = pd.to_datetime(df[dt_col], errors='coerce')
            valid_dates = df.loc[s_date.notna()].copy()
            if not valid_dates.empty:
                valid_dates[dt_col] = pd.to_datetime(valid_dates[dt_col])
                
                # Check range to pick granularity
                min_dt = valid_dates[dt_col].min()
                max_dt = valid_dates[dt_col].max()
                days_diff = (max_dt - min_dt).days
                
                freq = 'ME' if days_diff > 90 else 'W' if days_diff > 30 else 'D'
                
                if measures:
                    y_col = measures[0]
                    valid_dates[y_col] = pd.to_numeric(valid_dates[y_col], errors='coerce')
                    grouped = valid_dates.set_index(dt_col).groupby(pd.Grouper(freq=freq))[y_col].sum()
                    agg_name = "Sum"
                else:
                    y_col = "Record Count"
                    grouped = valid_dates.set_index(dt_col).groupby(pd.Grouper(freq=freq)).size()
                    agg_name = "Count"
                    
                grouped = grouped.dropna()
                if not grouped.empty:
                    data = [{"date": k.strftime('%Y-%m-%d'), "value": cls._sanitize_for_json(v)} for k, v in grouped.items()]
                    charts.append(ChartSpecification(
                        id=f"chart_line_{dt_col}_{y_col}",
                        chart_type="line",
                        title=f"{y_col.replace('_', ' ').title()} Over Time",
                        description=f"Trend by {dt_col}.",
                        x_column=dt_col,
                        y_column=y_col if y_col in df.columns else None,
                        x_key="date",
                        y_key="value",
                        aggregation=agg_name.lower(),
                        labels={"x": "Date", "y": agg_name},
                        series=[ChartSeries(name=y_col.replace('_', ' ').title(), dataKey="value", color="#10b981")],
                        data=data,
                        reason="Time-series analysis."
                    ))

        # 5. Scatter Plot
        if len(measures) >= 2 and len(charts) < 8:
            m1, m2 = measures[0], measures[1]
            valid_pairs = df[[m1, m2]].apply(pd.to_numeric, errors='coerce').dropna()
            if not valid_pairs.empty:
                # Subsample if too large
                if len(valid_pairs) > 500:
                    valid_pairs = valid_pairs.sample(500, random_state=42)
                data = [{"x": cls._sanitize_for_json(row[m1]), "y": cls._sanitize_for_json(row[m2])} for _, row in valid_pairs.iterrows()]
                charts.append(ChartSpecification(
                    id=f"chart_scatter_{m1}_{m2}",
                    chart_type="scatter",
                    title=f"{m1.replace('_', ' ').title()} vs {m2.replace('_', ' ').title()}",
                    description=f"Relationship between {m1} and {m2}.",
                    x_column=m1,
                    y_column=m2,
                    x_key="x",
                    y_key="y",
                    aggregation="none",
                    labels={"x": m1, "y": m2},
                    series=[ChartSeries(name="Observation", dataKey="y", color="#f59e0b")],
                    data=data,
                    reason="Scatter plot to show relationship between measures."
                ))
                
        return charts

    @classmethod
    def generate_custom_chart(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]], req: CustomChartRequest) -> CustomChartResponse:
        warnings = []
        data = []
        chart_type = req.chart_type
        x_col = req.x_column
        y_col = req.y_column
        agg = req.aggregation or "count"
        top_n = req.top_n or 10

        if x_col and x_col not in df.columns:
            raise ValueError(f"Column '{x_col}' not found in dataframe.")
        if y_col and y_col not in df.columns:
            raise ValueError(f"Column '{y_col}' not found in dataframe.")

        if chart_type in ["bar", "horizontal_bar"]:
            if not x_col:
                raise ValueError("X column (dimension) is required for Bar charts.")
            if y_col:
                df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                pd_agg = "mean" if agg == "avg" else ("size" if agg == "count" else agg)
                grouped = df.groupby(x_col)[y_col].agg(pd_agg).dropna()
            else:
                grouped = df[x_col].value_counts(dropna=True)
                y_col = "Record Count"
                agg = "count"
                
            grouped = grouped.sort_values(ascending=False)
            top = grouped.head(top_n)
            other = grouped.iloc[top_n:].sum()
            
            data = [{"x": str(k), "y": cls._sanitize_for_json(v)} for k, v in top.items()]
            if other > 0 and y_col == "Record Count":
                data.append({"x": "Other", "y": cls._sanitize_for_json(other)})
                
            spec = ChartSpecification(
                id="custom_bar",
                chart_type=chart_type,
                title=f"{y_col} by {x_col}",
                x_column=x_col,
                y_column=y_col,
                x_key="x",
                y_key="y",
                aggregation=agg,
                labels={"x": x_col, "y": y_col},
                series=[ChartSeries(name=y_col, dataKey="y", color="#6366f1")],
                data=data
            )
            
        elif chart_type == "line" or chart_type == "area":
            if not x_col:
                raise ValueError("X column (datetime dimension) is required for Line/Area charts.")
            
            df[x_col] = pd.to_datetime(df[x_col], errors='coerce')
            valid_df = df.dropna(subset=[x_col]).copy()
            
            freq = {"day": "D", "week": "W", "month": "ME", "quarter": "QE", "year": "YE"}.get(req.time_granularity, "ME")
            
            if y_col:
                valid_df[y_col] = pd.to_numeric(valid_df[y_col], errors='coerce')
                pd_agg = "mean" if agg == "avg" else ("size" if agg == "count" else agg)
                grouped = valid_df.set_index(x_col).groupby(pd.Grouper(freq=freq))[y_col].agg(pd_agg)
            else:
                y_col = "Record Count"
                agg = "count"
                grouped = valid_df.set_index(x_col).groupby(pd.Grouper(freq=freq)).size()
                
            grouped = grouped.dropna()
            data = [{"x": k.strftime('%Y-%m-%d'), "y": cls._sanitize_for_json(v)} for k, v in grouped.items()]
            
            spec = ChartSpecification(
                id="custom_line",
                chart_type=chart_type,
                title=f"{y_col} Over Time",
                x_column=x_col,
                y_column=y_col,
                x_key="x",
                y_key="y",
                aggregation=agg,
                labels={"x": "Date", "y": y_col},
                series=[ChartSeries(name=y_col, dataKey="y", color="#10b981")],
                data=data
            )
            
        elif chart_type == "histogram":
            if not x_col:
                raise ValueError("X column (numeric measure) is required for Histogram.")
            series = pd.to_numeric(df[x_col], errors='coerce').dropna()
            if len(series) < 2:
                raise ValueError("Not enough valid numbers for a histogram.")
            
            counts, bin_edges = np.histogram(series, bins=min(20, len(series.unique())))
            for i in range(len(counts)):
                label = f"{cls._sanitize_for_json(bin_edges[i])} - {cls._sanitize_for_json(bin_edges[i+1])}"
                data.append({"bin": label, "count": int(counts[i])})
                
            spec = ChartSpecification(
                id="custom_hist",
                chart_type="histogram",
                title=f"Distribution of {x_col}",
                x_column=x_col,
                labels={"x": x_col, "y": "Frequency"},
                series=[ChartSeries(name="Frequency", dataKey="count", color="#3b82f6")],
                data=data
            )
            
        elif chart_type == "scatter":
            if not x_col or not y_col:
                raise ValueError("Both X and Y columns (numeric measures) are required for Scatter charts.")
            x_role = roles.get(x_col, {}).get("role")
            y_role = roles.get(y_col, {}).get("role")
            if x_role not in ["integer", "float"] or y_role not in ["integer", "float"]:
                raise ValueError("Both X and Y columns must be numeric measures. This is required for Scatter charts.")
            valid_pairs = df[[x_col, y_col]].apply(pd.to_numeric, errors='coerce').dropna()
            if len(valid_pairs) > 1000:
                warnings.append("Data sampled to 1000 points for scatter plot performance.")
                valid_pairs = valid_pairs.sample(1000, random_state=42)
                
            data = [{"x": cls._sanitize_for_json(row[x_col]), "y": cls._sanitize_for_json(row[y_col])} for _, row in valid_pairs.iterrows()]
            spec = ChartSpecification(
                id="custom_scatter",
                chart_type="scatter",
                title=f"{x_col} vs {y_col}",
                x_column=x_col,
                y_column=y_col,
                labels={"x": x_col, "y": y_col},
                series=[ChartSeries(name="Observation", dataKey="y", color="#f59e0b")],
                data=data
            )
            
        elif chart_type == "donut":
            if not x_col:
                raise ValueError("X column (categorical dimension) is required for Donut charts.")
            grouped = df[x_col].value_counts(dropna=True)
            if len(grouped) > 20:
                warnings.append("High cardinality category for a donut chart. Consider a bar chart.")
                
            top = grouped.head(top_n)
            other = grouped.iloc[top_n:].sum()
            data = [{"category": str(k), "value": int(v)} for k, v in top.items()]
            if other > 0:
                data.append({"category": "Other", "value": int(other)})
                
            spec = ChartSpecification(
                id="custom_donut",
                chart_type="donut",
                title=f"Share of {x_col}",
                x_column=x_col,
                y_column=y_col,
                x_key="category",
                y_key="value",
                aggregation="count",
                labels={"x": x_col, "y": "Record Count"},
                series=[ChartSeries(name="Record Count", dataKey="value", color="#8b5cf6")],
                data=data
            )
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        return CustomChartResponse(specification=spec, warnings=warnings)
