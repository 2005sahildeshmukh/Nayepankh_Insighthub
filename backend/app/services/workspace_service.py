from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate

def get_workspaces(session: Session) -> List[Workspace]:
    return session.execute(select(Workspace).order_by(Workspace.updated_at.desc())).scalars().all()

def get_workspace_by_id(session: Session, workspace_id: str) -> Optional[Workspace]:
    return session.get(Workspace, workspace_id)

def create_workspace(session: Session, workspace_in: WorkspaceCreate) -> Workspace:
    # Check duplicate
    existing = session.execute(select(Workspace).where(Workspace.name.ilike(workspace_in.name))).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Workspace name already exists")
    
    workspace = Workspace(**workspace_in.model_dump())
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace

def update_workspace(session: Session, workspace_id: str, workspace_update: WorkspaceUpdate) -> Workspace:
    workspace = get_workspace_by_id(session, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if workspace_update.name is not None and workspace_update.name != workspace.name:
        existing = session.execute(select(Workspace).where(Workspace.name.ilike(workspace_update.name))).scalars().first()
        if existing and existing.id != workspace_id:
            raise HTTPException(status_code=409, detail="Workspace name already exists")
    
    update_data = workspace_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workspace, key, value)
        
    workspace.updated_at = datetime.now(timezone.utc)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace

def delete_workspace(db: Session, workspace_id: str) -> None:
    # 1. Confirm workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # 2. Check whether it contains datasets
    from app.models.dataset import Dataset
    dataset_count = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).count()
    if dataset_count > 0:
        raise HTTPException(status_code=409, detail="This workspace contains datasets and cannot be deleted.")
        
    # 3. Check whether it is the final remaining workspace
    if db.query(Workspace).count() <= 1:
        raise HTTPException(status_code=409, detail="The final remaining workspace cannot be deleted.")
        
    # 4. Delete only when both checks pass
    db.delete(workspace)
    db.commit()

def create_default_workspace(session: Session) -> None:
    existing = session.execute(select(Workspace)).scalars().first()
    if not existing:
        workspace = Workspace(
            name="NayePankh Foundation",
            description="Primary workspace for NGO data analysis, machine learning, and AI-powered insights."
        )
        session.add(workspace)
        session.commit()
