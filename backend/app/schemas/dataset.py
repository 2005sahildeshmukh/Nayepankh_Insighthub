from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class DatasetColumnSchema(BaseModel):
    id: str
    original_name: str
    normalized_name: str
    position: int
    inferred_type: str
    nullable: bool
    unique_count: Optional[int] = None
    missing_count: Optional[int] = None
    sample_values: Optional[List[Any]] = None
    mapping_status: str
    standard_field: Optional[str] = None
    custom_display_name: Optional[str] = None

class DatasetResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    row_count: int
    column_count: int
    status: str
    upload_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DatasetDetailResponse(DatasetResponse):
    columns: List[DatasetColumnSchema]

class ColumnMappingUpdate(BaseModel):
    id: str
    mapping_status: str # mapped, keep, exclude
    standard_field: Optional[str] = None
    custom_display_name: Optional[str] = None

class BulkMappingUpdate(BaseModel):
    columns: List[ColumnMappingUpdate]
