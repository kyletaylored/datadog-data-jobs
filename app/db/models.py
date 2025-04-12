from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Pipeline(Base):
    """
    Model to track pipelines that have been run
    """
    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # pending, running, completed, failed
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    input_file = Column(String(255), nullable=True)
    output_file = Column(String(255), nullable=True)
    prefect_flow_run_id = Column(String(255), nullable=True)
    records_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Relationship to stages
    stages = relationship(
        "PipelineStage", back_populates="pipeline", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pipeline {self.id}: {self.name} ({self.status})>"


class PipelineStage(Base):
    """
    Model to track individual stages of a pipeline
    """
    __tablename__ = "pipeline_stages"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # pending, running, completed, failed
    status = Column(String(20), default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationship to pipeline
    pipeline = relationship("Pipeline", back_populates="stages")

    def __repr__(self):
        return f"<PipelineStage {self.id}: {self.name} ({self.status})>"
