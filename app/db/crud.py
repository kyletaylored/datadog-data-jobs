from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.db.models import Pipeline, PipelineStage

# Pipeline CRUD operations


def get_pipeline(db: Session, pipeline_id: int) -> Optional[Pipeline]:
    """Get a pipeline by ID"""
    return db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()


def get_pipelines(db: Session, skip: int = 0, limit: int = 100) -> List[Pipeline]:
    """Get all pipelines with pagination"""
    return db.query(Pipeline).order_by(Pipeline.created_at.desc()).offset(skip).limit(limit).all()


def create_pipeline(db: Session, pipeline_data: Dict[str, Any]) -> Pipeline:
    """Create a new pipeline"""
    db_pipeline = Pipeline(**pipeline_data)
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)

    # Create default stages
    stages = [
        "Data Generation",
        "Data Ingestion",
        "Spark Processing",
        "DBT Transformation",
        "Data Export"
    ]

    for stage_name in stages:
        db_stage = PipelineStage(
            pipeline_id=db_pipeline.id,
            name=stage_name,
            description=f"Pipeline stage: {stage_name}",
            status="pending"
        )
        db.add(db_stage)

    db.commit()
    return db_pipeline


def update_pipeline(db: Session, pipeline_id: int, pipeline_data: Dict[str, Any]) -> Optional[Pipeline]:
    """Update a pipeline"""
    db_pipeline = get_pipeline(db, pipeline_id)
    if not db_pipeline:
        return None

    for key, value in pipeline_data.items():
        setattr(db_pipeline, key, value)

    db_pipeline.updated_at = datetime.now()
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


def update_pipeline_status(db: Session, pipeline_id: int, status: str, error_message: Optional[str] = None) -> Optional[Pipeline]:
    """Update pipeline status"""
    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message
    return update_pipeline(db, pipeline_id, update_data)


def delete_pipeline(db: Session, pipeline_id: int) -> bool:
    """Delete a pipeline"""
    db_pipeline = get_pipeline(db, pipeline_id)
    if not db_pipeline:
        return False

    db.delete(db_pipeline)
    db.commit()
    return True

# PipelineStage CRUD operations


def get_pipeline_stage(db: Session, stage_id: int) -> Optional[PipelineStage]:
    """Get a pipeline stage by ID"""
    return db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()


def get_pipeline_stages(db: Session, pipeline_id: int) -> List[PipelineStage]:
    """Get all stages for a pipeline"""
    return db.query(PipelineStage).filter(PipelineStage.pipeline_id == pipeline_id).order_by(PipelineStage.id).all()


def create_pipeline_stage(db: Session, stage_data: Dict[str, Any]) -> PipelineStage:
    """Create a new pipeline stage"""
    db_stage = PipelineStage(**stage_data)
    db.add(db_stage)
    db.commit()
    db.refresh(db_stage)
    return db_stage


def update_pipeline_stage(db: Session, stage_id: int, stage_data: Dict[str, Any]) -> Optional[PipelineStage]:
    """Update a pipeline stage"""
    db_stage = get_pipeline_stage(db, stage_id)
    if not db_stage:
        return None

    for key, value in stage_data.items():
        setattr(db_stage, key, value)

    db.commit()
    db.refresh(db_stage)
    return db_stage


def update_stage_status(
    db: Session,
    pipeline_id: int,
    stage_name: str,
    status: str,
    error_message: Optional[str] = None
) -> Optional[PipelineStage]:
    """Update a stage's status by pipeline ID and stage name"""
    db_stage = db.query(PipelineStage).filter(
        PipelineStage.pipeline_id == pipeline_id,
        PipelineStage.name == stage_name
    ).first()

    if not db_stage:
        return None

    update_data = {"status": status}

    if status == "running" and not db_stage.started_at:
        update_data["started_at"] = datetime.now()

    if status == "completed" and not db_stage.completed_at:
        update_data["completed_at"] = datetime.now()
        if db_stage.started_at:
            execution_time = (
                datetime.now() - db_stage.started_at).total_seconds()
            update_data["execution_time_seconds"] = execution_time

    if error_message:
        update_data["error_message"] = error_message

    return update_pipeline_stage(db, db_stage.id, update_data)
