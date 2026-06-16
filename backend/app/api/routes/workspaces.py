from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_session
from app.schemas.workspace import WorkspaceResponse, WorkspaceCreate, WorkspaceUpdate
from app.services import workspace_service

router = APIRouter()

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(session: Session = Depends(get_session)):
    return workspace_service.get_workspaces(session)

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(workspace_in: WorkspaceCreate, session: Session = Depends(get_session)):
    return workspace_service.create_workspace(session, workspace_in)

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: str, session: Session = Depends(get_session)):
    workspace = workspace_service.get_workspace_by_id(session, workspace_id)
    if not workspace:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(workspace_id: str, workspace_in: WorkspaceUpdate, session: Session = Depends(get_session)):
    return workspace_service.update_workspace(session, workspace_id, workspace_in)

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: str, session: Session = Depends(get_session)):
    workspace_service.delete_workspace(session, workspace_id)
