from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.workspace import utc_now, generate_uuid

class MLExperiment(Base):
    __tablename__ = "ml_experiment"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String, ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_view = Column(String(50), nullable=False) # working or mapped
    target_column = Column(String(200), nullable=False)
    task_type = Column(String(50), nullable=False) # classification, regression
    
    selected_features = Column(JSON, nullable=False)
    excluded_features = Column(JSON, nullable=False)
    
    status = Column(String(50), nullable=False, default="pending") # pending, running, completed, failed
    primary_metric = Column(String(100), nullable=True)
    best_model_name = Column(String(200), nullable=True)
    baseline_metric = Column(String(50), nullable=True)
    best_cv_metric = Column(String(50), nullable=True)
    test_metric = Column(String(50), nullable=True)
    
    metrics_json = Column(JSON, nullable=True)
    feature_importance_json = Column(JSON, nullable=True)
    configuration_json = Column(JSON, nullable=True)
    prediction_schema = Column(JSON, nullable=True)
    
    artifact_path = Column(String(1000), nullable=True)
    
    row_count = Column(Integer, nullable=True)
    training_row_count = Column(Integer, nullable=True)
    test_row_count = Column(Integer, nullable=True)
    random_seed = Column(Integer, nullable=True, default=42)
    
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="ml_experiments")
    dataset = relationship("Dataset", back_populates="ml_experiments")
