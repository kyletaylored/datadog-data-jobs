from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import os
import logging
import asyncio
from datetime import datetime

from app.api.routes import router as api_router
from app.db.database import engine, SessionLocal
from app.db import models, crud

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Datadog Data Pipeline Demo",
    description="A demo application for monitoring data pipelines with Datadog",
    version="1.0.0",
)

# Initialize database
models.Base.metadata.create_all(bind=engine)

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Add API router
app.include_router(api_router, prefix="/api")

# Dependency to get the database session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def initialize_prefect():
    """Initialize Prefect client on startup"""
    try:
        from prefect.client import get_client

        # Initialize the Prefect client
        client = get_client()

        # Make a simple API call to ensure connection
        try:
            deployments = await client.read_deployments()
            logger.info(
                f"Connected to Prefect server. Found {len(deployments)} deployments")
        except Exception as e:
            logger.warning(f"Could not fetch deployments: {e}")

        logger.info("Prefect client initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Prefect client: {e}")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """Serve the favicon"""
    favicon_path = os.path.join("app", "static", "img", "favicon.ico")
    return FileResponse(favicon_path)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db=Depends(get_db)):
    """
    Render the main dashboard page
    """
    pipelines = crud.get_pipelines(db)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "pipelines": pipelines,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )


@app.get("/pipeline/{pipeline_id}", response_class=HTMLResponse)
async def pipeline_detail(pipeline_id: int, request: Request, db=Depends(get_db)):
    """
    Render pipeline detail page
    """
    pipeline = crud.get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    stages = crud.get_pipeline_stages(db, pipeline_id)

    return templates.TemplateResponse(
        "pipeline.html",
        {
            "request": request,
            "pipeline": pipeline,
            "stages": stages,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )


@app.post("/trigger-pipeline")
async def trigger_pipeline(request: Request, db=Depends(get_db)):
    """
    Trigger a new pipeline execution and redirect to the detail page
    """
    try:
        # Create a new pipeline record
        pipeline = crud.create_pipeline(
            db,
            {
                "name": f"Pipeline Run {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "pending",
                "created_at": datetime.now()
            }
        )

        # Trigger the pipeline asynchronously
        asyncio.create_task(trigger_prefect_flow(pipeline.id))

        # Redirect to the pipeline detail page
        return RedirectResponse(url=f"/pipeline/{pipeline.id}", status_code=303)
    except Exception as e:
        logger.error(f"Error triggering pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Update the trigger_pipeline function in main.py
async def trigger_prefect_flow(pipeline_id: int):
    """
    Trigger a Prefect flow for the pipeline using the Prefect 3 API
    """
    try:
        # Import inside the function to avoid circular imports
        from prefect.client.orchestration import get_client

        # Get all available deployments
        client = get_client()

        logger.info("Fetching deployments from Prefect server...")
        deployments = await client.read_deployments()

        # Find our deployment
        deployment_id = None
        for deployment in deployments:
            logger.info(
                f"Found deployment: {deployment.name} (ID: {deployment.id})")
            if deployment.name == "data-pipeline-deployment":
                deployment_id = deployment.id
                break

        if not deployment_id:
            logger.error(
                "Could not find deployment 'data-pipeline-deployment'")

            # Try to create the deployment
            logger.info("Creating deployment...")
            try:
                from app.pipeline.flows import run_data_pipeline_flow
                source_path = str(Path(__file__).parent.parent)
                entrypoint = "app/pipeline/flows.py:run_data_pipeline_flow"

                deployment = await client.create_deployment(
                    name="data-pipeline-deployment",
                    flow_id=run_data_pipeline_flow._flow_id,
                    work_pool_name="default",
                    path=source_path,
                    entrypoint=entrypoint,
                )
                deployment_id = deployment.id
                logger.info(f"Created deployment with ID: {deployment_id}")
            except Exception as deploy_err:
                logger.error(f"Error creating deployment: {deploy_err}")
                # Fall back to direct flow execution
                from app.pipeline.flows import run_data_pipeline_flow
                result = await run_data_pipeline_flow(pipeline_id=pipeline_id, record_count=1000)
                return "direct-flow-run"

        # Create the flow run using the deployment
        logger.info(f"Creating flow run from deployment: {deployment_id}")
        flow_run = await client.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters={"pipeline_id": pipeline_id, "record_count": 1000}
        )

        logger.info(f"Triggered Prefect flow run: {flow_run.id}")

        # Update pipeline with flow run ID
        db = SessionLocal()
        try:
            crud.update_pipeline(
                db, pipeline_id, {"prefect_flow_run_id": str(flow_run.id)})
        finally:
            db.close()

        return flow_run.id

    except Exception as e:
        logger.error(f"Error in Prefect flow: {e}")

        # Update pipeline status to failed
        db = SessionLocal()
        try:
            crud.update_pipeline_status(db, pipeline_id, "failed", str(e))
        finally:
            db.close()

        # Re-raise the exception
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
