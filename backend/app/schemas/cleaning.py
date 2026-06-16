from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal
from datetime import datetime

class MissingValueRule(BaseModel):
    column: str
    strategy: Literal["keep", "drop", "mean", "median", "zero", "mode", "custom", "unknown_label", "true", "false", "earliest", "latest"]
    value: Optional[Any] = None

class CaseRule(BaseModel):
    column: str
    strategy: Literal["none", "lower", "upper", "title"]

class OutlierRule(BaseModel):
    column: str
    strategy: Literal["keep", "cap_iqr", "remove"]
    iqr_multiplier: float = 1.5

class CleaningConfiguration(BaseModel):
    version: int = 1
    convert_empty_strings_to_null: bool = True
    trim_whitespace: bool = True
    remove_exact_duplicates: bool = False
    missing_value_rules: List[MissingValueRule] = Field(default_factory=list)
    case_rules: List[CaseRule] = Field(default_factory=list)
    outlier_rules: List[OutlierRule] = Field(default_factory=list)

class CleaningPlanResponse(BaseModel):
    id: str
    dataset_id: str
    configuration: CleaningConfiguration
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CleaningPreviewRequest(BaseModel):
    configuration: CleaningConfiguration

class CleaningPreviewResponse(BaseModel):
    rows_before: int
    rows_after: int
    missing_cells_before: int
    missing_cells_after: int
    duplicates_removed: int
    outliers_affected: int
    warnings: List[str]
    preview_data: List[dict]
    columns: List[str]

class CleaningSaveResponse(BaseModel):
    plan: CleaningPlanResponse
    rows: int
    columns: int
    missing_cells: int
