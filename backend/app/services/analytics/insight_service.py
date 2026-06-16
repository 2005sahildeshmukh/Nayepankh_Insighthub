import pandas as pd
from typing import List, Dict, Any
from app.schemas.analytics import Insight, ChartSpecification, CorrelationResponse

class AnalyticsInsightService:
    @classmethod
    def generate_deterministic_insights(cls, df: pd.DataFrame, roles: Dict[str, Dict[str, Any]], charts: List[ChartSpecification], corr: CorrelationResponse) -> List[Insight]:
        insights = []
        row_count = len(df)
        if row_count == 0:
            return insights

        # Correlation Insights
        if corr.strongest_positive and corr.strongest_positive["value"] > 0.6:
            cols = corr.strongest_positive["cols"]
            insights.append(Insight(
                id=f"insight_corr_pos_{cols[0]}_{cols[1]}",
                type="correlation",
                title="Strong Positive Relationship",
                statement=f"There is a strong positive correlation ({corr.strongest_positive['value']:.2f}) between {cols[0]} and {cols[1]}.",
                evidence=f"Calculated Pearson correlation coefficient is {corr.strongest_positive['value']:.2f}.",
                source_columns=cols,
                reliability="Medium" if row_count > 30 else "Limited",
                limitation="Correlation describes association, not causation."
            ))
            
        # Limitation Insight
        valid_dates = [c for c, m in roles.items() if m["role"] == "datetime" and c in df.columns]
        if valid_dates:
            s_date = pd.to_datetime(df[valid_dates[0]], errors='coerce').dropna()
            if 0 < len(s_date) < 10:
                insights.append(Insight(
                    id="insight_limit_dates",
                    type="limitation",
                    title="Limited Time Data",
                    statement="Only a few valid dates are available.",
                    evidence=f"Found {len(s_date)} valid dates in '{valid_dates[0]}'.",
                    source_columns=[valid_dates[0]],
                    reliability="High"
                ))
                
        # Dominant Category Insight
        categoricals = [c for c, m in roles.items() if m["role"] == "categorical" and c in df.columns]
        for cat in categoricals:
            if len(insights) >= 8: break
            val_counts = df[cat].value_counts(dropna=True)
            if len(val_counts) > 0:
                top_val = val_counts.index[0]
                top_count = val_counts.iloc[0]
                pct = (top_count / row_count) * 100
                if pct > 40:
                    insights.append(Insight(
                        id=f"insight_dom_{cat}",
                        type="dominant_category",
                        title="Dominant Category",
                        statement=f"'{top_val}' represents {pct:.1f}% of records in {cat.replace('_', ' ').title()}.",
                        evidence=f"Found {top_count} records out of {row_count}.",
                        source_columns=[cat],
                        reliability="High" if row_count > 30 else "Medium"
                    ))
                    
        return insights[:8]
