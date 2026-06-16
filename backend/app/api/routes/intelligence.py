from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.database import get_session
from app.schemas.intelligence import CopilotRequest, CopilotResponse, DecisionsResponse, ReportResponse, EvidenceItem, DecisionCard, ReportSection, IntelligenceRequest
from app.services.intelligence.context_service import IntelligenceContextBuilder
from app.services.intelligence.gemini_service import GeminiService
from app.services.intelligence.prompt_templates import PromptTemplates
from app.models.dataset import Dataset
from app.core.config import settings

router = APIRouter()

def validate_dataset(db: Session, workspace_id: str, dataset_id: str, view: str):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.workspace_id == workspace_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.status != "ready":
        raise HTTPException(status_code=422, detail="Dataset is not in ready status")
    if view not in ["mapped", "working"]:
        raise HTTPException(status_code=422, detail="Unsupported view. Only 'mapped' and 'working' are supported.")
    return dataset

def get_deterministic_decisions(context: dict) -> list[DecisionCard]:
    # Extract details to make decisions deterministic
    ds_name = context["dataset"]["name"]
    row_count = context["dataset"]["row_count"]
    completeness = context["quality"]["completeness_percent"]
    
    decisions = []
    
    # Decision 1: Data Completeness / Quality Improvement
    if completeness < 100:
        decisions.append(DecisionCard(
            priority="high",
            title=f"Address missing data points in {ds_name}",
            recommended_action="Review and execute imputations or global cleaning rules for missing columns.",
            evidence=[f"Dataset completeness is at {completeness}% with {context['quality']['missing_cells']} missing values."],
            expected_impact="Improved consistency for future ML modelling and reporting.",
            confidence="high",
            limitations=["Imputation choices can introduce systematic bias depending on the method used."]
        ))
    else:
        decisions.append(DecisionCard(
            priority="medium",
            title=f"Maintain data collection standard for {ds_name}",
            recommended_action="Establish continuous data profiling validation on input streams.",
            evidence=[f"Dataset is 100% complete with {row_count} rows."],
            expected_impact="Maintains pristine status for analytical dashboards.",
            confidence="high",
            limitations=["Observational data profiles do not capture workflow errors directly."]
        ))

    # Decision 2: Focus on Analytics & Correlation Finding
    corrs = context["analytics"]["correlations"]
    if corrs:
        top_corr = corrs[0]
        f1 = top_corr["feature1"]
        f2 = top_corr["feature2"]
        coef = round(top_corr["coefficient"], 3)
        decisions.append(DecisionCard(
            priority="medium",
            title=f"Investigate association between {f1} and {f2}",
            recommended_action=f"Deep-dive into the operational workflow connecting {f1} and {f2} to identify synergies.",
            evidence=[f"Observed correlation coefficient of {coef} between '{f1}' and '{f2}'."],
            expected_impact="Uncover hidden behavioral drivers for donor campaigns.",
            confidence="medium",
            limitations=["Correlation does not establish causality; external variables could confound the link."]
        ))
    else:
        decisions.append(DecisionCard(
            priority="low",
            title="Increase feature dimensionality",
            recommended_action="Collect additional campaign metrics to identify donor patterns.",
            evidence=[f"No significant linear correlations detected across the {context['dataset']['column_count']} columns."],
            expected_impact="Provides a richer feature space for target optimization.",
            confidence="medium",
            limitations=["Adding columns can increase noise and overfitting risk."]
        ))

    # Decision 3: Machine Learning Model Deployment / Baseline Optimization
    ml = context["ml"]
    if ml.get("available"):
        target = ml["target"]
        model = ml["model"]
        decisions.append(DecisionCard(
            priority="high",
            title=f"Leverage {model} model predictions for {target}",
            recommended_action=f"Utilize the sandbox to simulate donor actions and tailor campaign outreaches.",
            evidence=[f"Trained {model} experiment targeting '{target}' is available in this view."],
            expected_impact="Targeted allocation of limited NGO resources.",
            confidence="medium",
            limitations=["The model performance is based on historic data and might degrade under new campaigns."]
        ))
    else:
        decisions.append(DecisionCard(
            priority="medium",
            title="Initiate Predictive Modeling Lifecycle",
            recommended_action="Configure and run a machine learning experiment in ML Studio using a numeric or categorical target.",
            evidence=["No active ML experiment is currently trained for this view."],
            expected_impact="Transition from descriptive analytics to predictive decision support.",
            confidence="high",
            limitations=["Requires clean and aligned target variables before running experiments."]
        ))

    return decisions[:3]

@router.post("/workspaces/{workspace_id}/intelligence/copilot", response_model=CopilotResponse)
def get_copilot_insights(workspace_id: str, req: CopilotRequest, db: Session = Depends(get_session)):
    validate_dataset(db, workspace_id, req.dataset_id, req.view)
    
    # 1. Build unified context once
    context = IntelligenceContextBuilder.build_context(db, workspace_id, req.dataset_id, req.view)
    
    # 2. Extract deterministic values for fallback
    row_count = context["dataset"]["row_count"]
    completeness = context["quality"]["completeness_percent"]
    
    # 3. Call Gemini or Fallback
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        # Fallback response
        kpis_str = ", ".join([f"{k['title']}: {k['value']}" for k in context["analytics"]["kpis"]])
        answer = f"AI generation is temporarily unavailable. Showing deterministic insights from the dataset. Total records: {row_count}. Completeness: {completeness}%. KPIs: {kpis_str}."
        
        evidence = [EvidenceItem(label="Dataset Rows", value=str(row_count)), EvidenceItem(label="Completeness Percentage", value=f"{completeness}%")]
        recommended_actions = ["Review dataset quality metrics.", "Configure global cleaning rules if needed."]
        limitations = ["The fallback analysis only presents basic statistical aggregates."]
        return CopilotResponse(answer=answer, evidence=evidence, recommended_actions=recommended_actions, limitations=limitations)

    try:
        # Prompt and call
        prompt = PromptTemplates.COPILOT_PROMPT.format(question=req.question, context_json=context)
        res = GeminiService.call_gemini(PromptTemplates.SYSTEM_INSTRUCTION, prompt, CopilotResponse)
        return res
    except Exception as e:
        # Safe fallback on failure/timeout
        answer = f"AI generation is temporarily unavailable. Showing deterministic insights from the dataset. Request failed: {str(e)}"
        evidence = [EvidenceItem(label="Dataset Rows", value=str(row_count)), EvidenceItem(label="Completeness Percentage", value=f"{completeness}%")]
        recommended_actions = ["Check backend environment configuration.", "Validate Gemini key validity."]
        limitations = ["The fallback analysis only presents basic statistical aggregates."]
        return CopilotResponse(answer=answer, evidence=evidence, recommended_actions=recommended_actions, limitations=limitations)

@router.post("/workspaces/{workspace_id}/intelligence/decisions", response_model=DecisionsResponse)
def get_decision_intelligence(workspace_id: str, req: IntelligenceRequest, db: Session = Depends(get_session)):
    validate_dataset(db, workspace_id, req.dataset_id, req.view)
    context = IntelligenceContextBuilder.build_context(db, workspace_id, req.dataset_id, req.view)
    
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        return DecisionsResponse(decisions=get_deterministic_decisions(context))
        
    try:
        prompt = PromptTemplates.DECISIONS_PROMPT.format(context_json=context)
        res = GeminiService.call_gemini(PromptTemplates.SYSTEM_INSTRUCTION, prompt, DecisionsResponse)
        return res
    except Exception:
        return DecisionsResponse(decisions=get_deterministic_decisions(context))

@router.post("/workspaces/{workspace_id}/intelligence/report", response_model=ReportResponse)
def get_intelligence_report(workspace_id: str, req: IntelligenceRequest, db: Session = Depends(get_session)):
    dataset = validate_dataset(db, workspace_id, req.dataset_id, req.view)
    context = IntelligenceContextBuilder.build_context(db, workspace_id, req.dataset_id, req.view)
    
    # 1. Build deterministic report sections
    row_count = context["dataset"]["row_count"]
    completeness = context["quality"]["completeness_percent"]
    cols_count = context["dataset"]["column_count"]
    
    quality_issues_text = "; ".join([f"{i['title']} on {i['column']} ({i['severity']})" for i in context["quality"]["issues"]]) or "No major issues identified."
    cleaning_actions_text = ", ".join(context["cleaning"]["actions"]) or "None applied."
    
    kpis_text = "; ".join([f"{k['title']}: {k['value']}" for k in context["analytics"]["kpis"]])
    insights_text = " ".join(context["analytics"]["insights"])
    
    ml = context["ml"]
    if ml.get("available"):
        metrics = ml.get("metrics") or {}
        parts = [
            f"Model: {ml.get('model')}",
            f"Target: {ml.get('target')}"
        ]
        
        def fmt_val(v, is_pct=False):
            if v is None:
                return "N/A"
            try:
                val = float(v)
                if is_pct:
                    if 0.0 < val < 1.0:
                        val = val * 100.0
                    return f"{val:.2f}%"
                return f"{val:.4f}" if abs(val) < 1 else f"{val:.2f}"
            except (ValueError, TypeError):
                return str(v)

        if "mae" in metrics:
            parts.append(f"MAE: {fmt_val(metrics['mae'])}")
        if "mse" in metrics:
            parts.append(f"MSE: {fmt_val(metrics['mse'])}")
        if "rmse" in metrics:
            parts.append(f"RMSE: {fmt_val(metrics['rmse'])}")
        if "r2" in metrics:
            parts.append(f"R²: {fmt_val(metrics['r2'])}")
        if "explained_variance" in metrics:
            parts.append(f"Explained Variance: {fmt_val(metrics['explained_variance'])}")
        if "median_absolute_error" in metrics:
            parts.append(f"Median Absolute Error: {fmt_val(metrics['median_absolute_error'])}")
        if "mape" in metrics:
            parts.append(f"MAPE: {fmt_val(metrics['mape'], is_pct=True)}")
        if "baseline_mae" in metrics:
            parts.append(f"Baseline MAE: {fmt_val(metrics['baseline_mae'])}")
        if "baseline_rmse" in metrics:
            parts.append(f"Baseline RMSE: {fmt_val(metrics['baseline_rmse'])}")
        if "baseline_r2" in metrics:
            parts.append(f"Baseline R²: {fmt_val(metrics['baseline_r2'])}")
            
        ml_text = "\n".join(parts)
    else:
        ml_text = "No completed machine-learning experiment was available for this report."
        
    det_decisions = get_deterministic_decisions(context)
    decisions_text = "\n".join([f"- Priority {d.priority.upper()}: {d.title}. Action: {d.recommended_action}" for d in det_decisions])
    
    # Local timestamp
    gen_time = datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M:%S UTC")

    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        # Fallback Report
        title = "NayePankh Dataset Intelligence Report"
        sections = [
            ReportSection(
                heading="Executive Summary",
                content=f"AI generation is temporarily unavailable. Showing deterministic insights from the dataset. Dataset '{dataset.name}' consists of {row_count} rows and {cols_count} features."
            ),
            ReportSection(
                heading="Dataset Overview",
                content=f"The database view represents the '{req.view}' dataset state containing {row_count} entries across {cols_count} features."
            ),
            ReportSection(
                heading="Data Quality",
                content=f"Dataset completeness: {completeness}%. Identified issues: {quality_issues_text}."
            ),
            ReportSection(
                heading="Cleaning Performed",
                content=f"Cleaning strategies applied: {cleaning_actions_text}."
            ),
            ReportSection(
                heading="Key Analytics Findings",
                content=f"KPI Summary: {kpis_text}. Insights: {insights_text}."
            ),
            ReportSection(
                heading="Machine Learning Results",
                content=ml_text
            ),
            ReportSection(
                heading="Recommended Decisions",
                content=decisions_text
            ),
            ReportSection(
                heading="Risks and Limitations",
                content="Deterministic metrics are based entirely on observational datasets and should be reviewed before making critical decisions."
            ),
            ReportSection(
                heading="Next Actions",
                content="Address remaining data issues and configure targeted campaigns in accordance with observed findings."
            )
        ]
        return ReportResponse(title=title, generated_at=gen_time, sections=sections, limitations=["This report relies purely on static deterministic dataset summaries."])

    try:
        # Prompt and call Gemini for executive content enrichment
        prompt = PromptTemplates.REPORT_PROMPT.format(context_json=context, generated_at=gen_time)
        res = GeminiService.call_gemini(PromptTemplates.SYSTEM_INSTRUCTION, prompt, ReportResponse)
        
        # Build the final sections list, injecting the deterministic ones to ensure they are never missing
        sections_map = {s.heading: s.content for s in res.sections}
        
        final_sections = [
            ReportSection(heading="Executive Summary", content=sections_map.get("Executive Summary", "Summary unavailable.")),
            ReportSection(heading="Dataset Overview", content=f"The database view represents the '{req.view}' dataset state containing {row_count} entries across {cols_count} features."),
            ReportSection(heading="Data Quality", content=f"Dataset completeness is calculated at {completeness}%. Found {len(context['quality']['issues'])} issues: {quality_issues_text}."),
            ReportSection(heading="Cleaning Performed", content=f"Cleaning strategies applied: {cleaning_actions_text}."),
            ReportSection(heading="Key Analytics Findings", content=f"KPI Summary: {kpis_text}. Insights: {insights_text}."),
            ReportSection(heading="Machine Learning Results", content=ml_text),
            ReportSection(heading="Recommended Decisions", content=sections_map.get("Strategic Recommended Decisions", decisions_text)),
            ReportSection(heading="Risks and Limitations", content=sections_map.get("Risks and Limitations", "Observational metrics only; no causal verification.")),
            ReportSection(heading="Next Actions", content=sections_map.get("Next Actions", "Address remaining data quality anomalies and review campaign outcomes."))
        ]
        
        return ReportResponse(title=res.title, generated_at=res.generated_at, sections=final_sections, limitations=res.limitations)
        
    except Exception:
        # If Gemini fails, fallback gracefully
        sections = [
            ReportSection(heading="Executive Summary", content=f"AI generation is temporarily unavailable. Showing deterministic insights from the dataset. Dataset '{dataset.name}' consists of {row_count} rows and {cols_count} features."),
            ReportSection(heading="Dataset Overview", content=f"The database view represents the '{req.view}' dataset state containing {row_count} entries across {cols_count} features."),
            ReportSection(heading="Data Quality", content=f"Dataset completeness: {completeness}%. Identified issues: {quality_issues_text}."),
            ReportSection(heading="Cleaning Performed", content=f"Cleaning strategies applied: {cleaning_actions_text}."),
            ReportSection(heading="Key Analytics Findings", content=f"KPI Summary: {kpis_text}. Insights: {insights_text}."),
            ReportSection(heading="Machine Learning Results", content=ml_text),
            ReportSection(heading="Recommended Decisions", content=decisions_text),
            ReportSection(heading="Risks and Limitations", content="Deterministic metrics are based entirely on observational datasets and should be reviewed before making critical decisions."),
            ReportSection(heading="Next Actions", content="Address remaining data issues and configure targeted campaigns in accordance with observed findings.")
        ]
        return ReportResponse(title="NayePankh Dataset Intelligence Report", generated_at=gen_time, sections=sections, limitations=["This report relies purely on static deterministic dataset summaries."])
