import os
import sys
import json
import time
import random
import asyncio
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Import Prefect
from prefect import flow, task, get_run_logger
from prefect.context import get_run_context

# Configure logging
logger = logging.getLogger(__name__)

# Helper function to update pipeline status


async def update_pipeline_status(
    pipeline_id: int,
    stage_name: Optional[str] = None,
    status: Optional[str] = None,
    message: Optional[str] = None,
    records_processed: Optional[int] = None
):
    """
    Helper function to update pipeline and stage status via API
    """
    import httpx

    try:
        api_url = "http://localhost:8000/api/status-update/"

        payload = {
            "pipeline_id": pipeline_id,
            "status": status
        }

        if stage_name:
            payload["stage_name"] = stage_name

        if message:
            payload["error_message"] = message

        if records_processed is not None:
            payload["records_processed"] = records_processed

        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload)
            response.raise_for_status()

        return True
    except Exception as e:
        logger.error(f"Error updating pipeline status: {e}")
        return False


@task(name="generate_data", retries=2)
async def generate_data(pipeline_id: int, records: int = 1000) -> str:
    """
    Generate a sample dataset for processing
    """
    logger = get_run_logger()
    logger.info(f"Generating {records} records of sample data")

    await update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Data Generation",
        status="running"
    )

    try:
        # Create data directory if it doesn't exist
        data_dir = "/app/data/input"
        os.makedirs(data_dir, exist_ok=True)

        # Generate filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_data_{timestamp}.json"
        filepath = os.path.join(data_dir, filename)

        # Generate random data
        data = []
        for i in range(records):
            data.append({
                "id": i,
                "name": f"Item {i}",
                "category": random.choice(["A", "B", "C", "D"]),
                "value": round(random.uniform(10, 1000), 2),
                "quantity": random.randint(1, 100),
                "is_active": random.choice([True, False]),
                "created_at": (
                    datetime.datetime.now() -
                    datetime.timedelta(days=random.randint(0, 30))
                ).isoformat()
            })

        # Write data to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Generated data file: {filepath}")

        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Generation",
            status="completed",
            message=f"Generated {records} records to {filename}"
        )

        return filepath

    except Exception as e:
        logger.error(f"Error generating data: {e}")
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Generation",
            status="failed",
            message=f"Error generating data: {str(e)}"
        )
        raise


@task(name="ingest_data", retries=3)
async def ingest_data(pipeline_id: int, input_file: str) -> List[Dict[str, Any]]:
    """
    Ingest data from the input file
    """
    logger = get_run_logger()
    logger.info(f"Ingesting data from {input_file}")

    await update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Data Ingestion",
        status="running",
        message=f"Ingesting data from {input_file}"
    )

    try:
        # Read data from file
        with open(input_file, 'r') as f:
            data = json.load(f)

        # Update pipeline with input file information
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            status="running",
            message=f"Ingested {len(data)} records"
        )

        # Simulate processing time
        time.sleep(1)

        logger.info(f"Ingested {len(data)} records")

        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Ingestion",
            status="completed",
            message=f"Successfully ingested {len(data)} records"
        )

        return data

    except Exception as e:
        logger.error(f"Error ingesting data: {e}")
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Ingestion",
            status="failed",
            message=f"Error ingesting data: {str(e)}"
        )
        raise


@task(name="process_with_spark")
async def process_with_spark(pipeline_id: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process data using PySpark

    In a real scenario, this would use a PySpark cluster to process the data.
    For this demo, we'll simulate the processing.
    """
    logger = get_run_logger()
    logger.info(f"Processing {len(data)} records with PySpark")

    await update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Spark Processing",
        status="running",
        message=f"Processing {len(data)} records with PySpark"
    )

    try:
        # In a real scenario, we would use PySpark to process the data
        # For this demo, we'll just simulate it

        # Simulate PySpark processing time - scaled based on data size
        # Scale with data size, max 3 seconds
        processing_time = min(len(data) * 0.01, 3)
        time.sleep(processing_time)

        # Transform data (simple transformation)
        processed_data = []
        for record in data:
            # Add calculated fields
            processed_record = record.copy()
            processed_record["total_value"] = record["value"] * \
                record["quantity"]
            processed_record["processed_by"] = "spark"
            processed_record["processed_at"] = datetime.datetime.now(
            ).isoformat()
            processed_data.append(processed_record)

        # Log statistics
        num_records = len(processed_data)
        avg_value = sum(r["total_value"] for r in processed_data) / \
            num_records if num_records > 0 else 0
        logger.info(
            f"Processed {num_records} records with average value: {avg_value:.2f}")

        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Spark Processing",
            status="completed",
            message=f"Successfully processed {num_records} records"
        )

        return processed_data

    except Exception as e:
        logger.error(f"Error processing data with Spark: {e}")
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Spark Processing",
            status="failed",
            message=f"Error processing data: {str(e)}"
        )
        raise


@task(name="transform_with_dbt")
async def transform_with_dbt(pipeline_id: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform data using dbt

    In a real scenario, this would use dbt to transform data in the database.
    For this demo, we'll simulate the transformation.
    """
    logger = get_run_logger()
    logger.info(f"Transforming data with dbt")

    await update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="DBT Transformation",
        status="running",
        message=f"Transforming data with dbt-core"
    )

    try:
        # In a real scenario, we would use dbt to transform data in the database
        # For this demo, we'll simulate the process

        # Simulate dbt processing time
        time.sleep(2)

        # Simulate dbt transformations
        transformed_data = []
        categories = {}

        for record in data:
            # Group by category for aggregation
            category = record["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(record)

            # Apply transformations to individual records
            transformed_record = record.copy()
            transformed_record["is_high_value"] = record["total_value"] > 5000
            transformed_record["tier"] = (
                "premium" if record["total_value"] > 5000
                else "standard" if record["total_value"] > 1000
                else "basic"
            )
            transformed_record["transformed_by"] = "dbt"
            transformed_record["transformed_at"] = datetime.datetime.now(
            ).isoformat()
            transformed_data.append(transformed_record)

        # Add category aggregates
        for category, records in categories.items():
            avg_value = sum(r["total_value"] for r in records) / len(records)
            for record in transformed_data:
                if record["category"] == category:
                    record["category_avg_value"] = avg_value

        # Log statistics
        logger.info(
            f"Transformed {len(transformed_data)} records across {len(categories)} categories")

        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="DBT Transformation",
            status="completed",
            message=f"Successfully transformed {len(transformed_data)} records"
        )

        return transformed_data

    except Exception as e:
        logger.error(f"Error transforming data with dbt: {e}")
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="DBT Transformation",
            status="failed",
            message=f"Error transforming data: {str(e)}"
        )
        raise


@task(name="export_results")
async def export_results(pipeline_id: int, data: List[Dict[str, Any]]) -> str:
    """
    Export the transformed data
    """
    logger = get_run_logger()
    logger.info(f"Exporting {len(data)} records")

    await update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Data Export",
        status="running",
        message=f"Exporting {len(data)} records"
    )

    try:
        # Create output directory if it doesn't exist
        output_dir = "/app/data/output"
        os.makedirs(output_dir, exist_ok=True)

        # Generate output filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            output_dir, f"pipeline_{pipeline_id}_results_{timestamp}.json")

        # Export data
        with open(output_file, 'w') as f:
            output_data = {
                "pipeline_id": pipeline_id,
                "generated_at": datetime.datetime.now().isoformat(),
                "record_count": len(data),
                "data": data
            }
            json.dump(output_data, f, indent=2)

        logger.info(f"Data exported to {output_file}")

        # Update pipeline status
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Export",
            status="completed",
            message=f"Data exported to {os.path.basename(output_file)}",
            records_processed=len(data)
        )

        # Update the overall pipeline status with file info
        # Using update_pipeline_status function to update the complete pipeline
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            status="completed",
            records_processed=len(data)
        )

        return output_file

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Export",
            status="failed",
            message=f"Error exporting data: {str(e)}"
        )
        raise


@flow(name="Data Pipeline", log_prints=True)
async def run_data_pipeline_flow(pipeline_id: int, record_count: int = 1000):
    """
    Main flow that orchestrates the entire data pipeline
    """
    logger = get_run_logger()
    logger.info(
        f"Starting data pipeline {pipeline_id} with {record_count} records")
    print(f"Starting data pipeline {pipeline_id} with {record_count} records")

    try:
        # Get the flow run context
        ctx = get_run_context()
        flow_run_id = ctx.flow_run.id if hasattr(ctx, 'flow_run') else None

        # Update the pipeline with the flow run ID if available
        if flow_run_id:
            from app.db.database import SessionLocal
            from app.db import crud

            db = SessionLocal()
            try:
                crud.update_pipeline(
                    db, pipeline_id, {"prefect_flow_run_id": str(flow_run_id)})
            finally:
                db.close()

        # Execute pipeline stages

        # Stage 1: Generate sample data
        input_file = await generate_data(pipeline_id=pipeline_id, records=record_count)

        # Stage 2: Ingest data
        data = await ingest_data(pipeline_id=pipeline_id, input_file=input_file)

        # Stage 3: Process with Spark
        processed_data = await process_with_spark(pipeline_id=pipeline_id, data=data)

        # Stage 4: Transform with dbt
        transformed_data = await transform_with_dbt(pipeline_id=pipeline_id, data=processed_data)

        # Stage 5: Export results
        output_file = await export_results(pipeline_id=pipeline_id, data=transformed_data)

        logger.info(f"Pipeline {pipeline_id} completed successfully")
        print(f"Pipeline {pipeline_id} completed successfully")
        return {"success": True, "pipeline_id": pipeline_id}

    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} failed: {e}")
        print(f"Pipeline {pipeline_id} failed: {e}")

        # Update pipeline status to failed
        await update_pipeline_status(
            pipeline_id=pipeline_id,
            status="failed",
            message=str(e)
        )

        return {"success": False, "pipeline_id": pipeline_id, "error": str(e)}
