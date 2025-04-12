from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.models import (
    PipelineCreate,
    PipelineResponse,
    PipelineStageResponse,
    StatusUpdate
)
from app.db.database import SessionLocal
from app.db import crud

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    tags=["pipelines"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get the database session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/pipelines/", response_model=List[PipelineResponse])
def get_pipelines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all pipelines"""
    pipelines = crud.get_pipelines(db, skip=skip, limit=limit)
    return pipelines


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    """Get a pipeline by ID"""
    pipeline = crud.get_pipeline(db, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.post("/pipelines/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
def create_pipeline(pipeline: PipelineCreate, db: Session = Depends(get_db)):
    """Create a new pipeline"""
    return crud.create_pipeline(db, pipeline.dict())


@router.get("/pipelines/{pipeline_id}/stages", response_model=List[PipelineStageResponse])
def get_pipeline_stages(pipeline_id: int, db: Session = Depends(get_db)):
    """Get all stages for a pipeline"""
    pipeline = crud.get_pipeline(db, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    stages = crud.get_pipeline_stages(db, pipeline_id)
    return stages


@router.post("/status-update/")
def update_status(status_update: StatusUpdate, db: Session = Depends(get_db)):
    """Update the status of a pipeline or stage"""
    pipeline_id = status_update.pipeline_id
    pipeline = crud.get_pipeline(db, pipeline_id)

    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if status_update.stage_name:
        # Update a specific stage
        stage = crud.update_stage_status(
            db,
            pipeline_id,
            status_update.stage_name,
            status_update.status,
            status_update.error_message
        )

        if stage is None:
            raise HTTPException(
                status_code=404,
                detail=f"Stage '{status_update.stage_name}' not found"
            )

        # Check if we need to update the pipeline status based on stage status
        if status_update.status == "completed":
            # Check if all stages are complete
            all_stages = crud.get_pipeline_stages(db, pipeline_id)
            all_completed = all(s.status == "completed" for s in all_stages)

            if all_completed:
                crud.update_pipeline_status(db, pipeline_id, "completed")

        elif status_update.status == "failed":
            # If any stage fails, mark the pipeline as failed
            crud.update_pipeline_status(
                db,
                pipeline_id,
                "failed",
                status_update.error_message
            )
    else:
        # Update the entire pipeline
        crud.update_pipeline_status(
            db,
            pipeline_id,
            status_update.status,
            status_update.error_message
        )

        # If records_processed was provided, update that as well
        if status_update.records_processed is not None:
            crud.update_pipeline(
                db,
                pipeline_id,
                {"records_processed": status_update.records_processed}
            )

    return {"success": True}


@router.post("/trigger/{pipeline_id}")
async def trigger_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    """Trigger a specific pipeline"""
    pipeline = crud.get_pipeline(db, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Trigger the pipeline flow
    from app.main import trigger_prefect_flow
    import asyncio

    # Update pipeline status to running
    crud.update_pipeline_status(db, pipeline_id, "running")

    # Trigger the flow asynchronously
    asyncio.create_task(trigger_prefect_flow(pipeline_id))

    return {"success": True, "message": f"Pipeline {pipeline_id} triggered"}
