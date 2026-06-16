from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.workspace import utc_now, generate_uuid

class Dataset(Base):
    __tablename__ = "dataset"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspace.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False, unique=True)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(10), nullable=False) # csv or xlsx
    file_size_bytes = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="uploaded") # uploaded, mapping_pending, ready, failed
    upload_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    workspace = relationship("Workspace", back_populates="datasets")
    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    cleaning_plan = relationship("DatasetCleaningPlan", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
    ml_experiments = relationship("MLExperiment", back_populates="dataset", cascade="all, delete-orphan")

class DatasetColumn(Base):
    __tablename__ = "dataset_column"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = Column(String(200), nullable=False)
    normalized_name = Column(String(200), nullable=False)
    position = Column(Integer, nullable=False)
    inferred_type = Column(String(50), nullable=False) # integer, float, boolean, datetime, categorical, text, identifier, unknown
    nullable = Column(Boolean, nullable=False, default=True)
    unique_count = Column(Integer, nullable=True)
    missing_count = Column(Integer, nullable=True)
    sample_values = Column(JSON, nullable=True)
    mapping_status = Column(String(50), nullable=False) # mapped, keep, exclude
    standard_field = Column(String(100), nullable=True)
    custom_display_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    dataset = relationship("Dataset", back_populates="columns")
