from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from pathlib import Path
import os

from app.core.config import settings
from app.core.database import engine, get_session
from app.api.router import api_router
from app.api.routes import health
from app.services.workspace_service import create_default_workspace
from app.models.base import Base
from sqlalchemy.orm import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure configured storage paths exist safely
    data_root_path = settings.data_root_dir
    data_root_path.mkdir(parents=True, exist_ok=True)
    
    # Ensure subdirectory structures are ready
    (data_root_path / "uploads").mkdir(parents=True, exist_ok=True)
    (data_root_path / "artifacts" / "models").mkdir(parents=True, exist_ok=True)


    Base.metadata.create_all(engine)
    with Session(engine) as session:
        create_default_workspace(session)
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
