from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.workspace import utc_now, generate_uuid

class DatasetCleaningPlan(Base):
    __tablename__ = "dataset_cleaning_plan"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    configuration = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    dataset = relationship("Dataset", back_populates="cleaning_plan")
