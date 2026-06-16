from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EvidenceItem(BaseModel):
    label: str
    value: str

class CopilotResponse(BaseModel):
    answer: str
    evidence: List[EvidenceItem]
    recommended_actions: List[str]
    limitations: List[str]

class DecisionCard(BaseModel):
    priority: str = Field(description="Must be high, medium, or low")
    title: str
    recommended_action: str
    evidence: List[str]
    expected_impact: str
    confidence: str = Field(description="Must be high, medium, or low")
    limitations: List[str]

class DecisionsResponse(BaseModel):
    decisions: List[DecisionCard]

class ReportSection(BaseModel):
    heading: str
    content: str

class ReportResponse(BaseModel):
    title: str
    generated_at: str
    sections: List[ReportSection]
    limitations: List[str]

class IntelligenceRequest(BaseModel):
    dataset_id: str
    view: str

class CopilotRequest(IntelligenceRequest):
    question: str
