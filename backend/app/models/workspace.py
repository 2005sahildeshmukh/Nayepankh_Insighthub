from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.models.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Workspace(Base):
    __tablename__ = "workspace"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), index=True, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

    # Relationships
    datasets = relationship("Dataset", back_populates="workspace")
    ml_experiments = relationship("MLExperiment", back_populates="workspace", cascade="all, delete-orphan")
