from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Pipeline models


class PipelineBase(BaseModel):
    """Base Pipeline model with common attributes"""
    name: str
    description: Optional[str] = None
    status: str = "pending"


class PipelineCreate(PipelineBase):
    """Model for creating a pipeline"""
    pass


class PipelineStageBase(BaseModel):
    """Base Pipeline Stage model with common attributes"""
    name: str
    description: Optional[str] = None
    status: str = "pending"


class PipelineStageCreate(PipelineStageBase):
    """Model for creating a pipeline stage"""
    pipeline_id: int


class PipelineStageResponse(PipelineStageBase):
    """Response model for pipeline stages"""
    id: int
    pipeline_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True


class PipelineResponse(PipelineBase):
    """Response model for pipelines"""
    id: int
    created_at: datetime
    updated_at: datetime
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    prefect_flow_run_id: Optional[str] = None
    records_processed: int = 0
    error_message: Optional[str] = None
    stages: List[PipelineStageResponse] = []

    class Config:
        orm_mode = True

# Status update model


class StatusUpdate(BaseModel):
    """Model for updating pipeline or stage status"""
    pipeline_id: int
    stage_name: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    records_processed: Optional[int] = None
