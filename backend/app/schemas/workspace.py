from pydantic import BaseModel, Field, constr, ConfigDict
from typing import Optional
from datetime import datetime

class WorkspaceCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=100)
    description: Optional[constr(max_length=500)] = None

class WorkspaceUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, min_length=1, max_length=100)] = None
    description: Optional[constr(max_length=500)] = None

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    dataset_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)
