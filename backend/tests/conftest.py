import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_session
from app.services.workspace_service import create_default_workspace
import os
import shutil
from pathlib import Path
from app.models.base import Base
import app.services.file_storage_service as file_storage

# Configure temp upload dir
TEMP_UPLOAD_DIR = Path("backend/tests/data/temp_uploads")

@pytest.fixture(name="session")
def session_fixture():
    # Use an isolated in-memory SQLite database per test
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    
    file_storage.UPLOAD_DIR = TEMP_UPLOAD_DIR
    
    with Session(engine) as session:
        create_default_workspace(session)
        try:
            yield session
        finally:
            session.rollback()
            session.close()
            Base.metadata.drop_all(engine)
            engine.dispose()
            if TEMP_UPLOAD_DIR.exists():
                try:
                    shutil.rmtree(TEMP_UPLOAD_DIR)
                except Exception:
                    pass

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
