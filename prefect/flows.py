from worker.tasks import process_data_batch, aggregate_results, export_data
from prefect.context import get_run_context
from prefect import flow, task, get_run_logger
from dashboard.models import DataPipeline, PipelineStage
from django.conf import settings
import django
import os
import sys
import json
import time
import random
import asyncio
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import Django models

# Import Prefect

# Import Celery tasks

# Initialize Datadog tracing if available
try:
    from ddtrace import patch_all
    patch_all()
except ImportError:
    print("Datadog tracing not available, continuing without it.")


@task(name="generate_data", retries=2)
def generate_data(records: int = 1000) -> str:
    """
    Generate a sample dataset for processing

    Args:
        records: Number of records to generate

    Returns:
        Path to the generated data file
    """
    logger = get_run_logger()
    logger.info(f"Generating {records} records of sample data")

    # Create data directory if it doesn't exist
    data_dir = os.path.join(settings.DATA_INPUT_DIR)
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
    return filepath


@task(name="ingest_data", retries=3)
def ingest_data(pipeline_id: int, input_file: str) -> List[Dict[str, Any]]:
    """
    Ingest data from the input file

    Args:
        pipeline_id: ID of the pipeline to update
        input_file: Path to the input data file

    Returns:
        List of data records
    """
    logger = get_run_logger()
    logger.info(f"Ingesting data from {input_file}")

    # Update pipeline with input file information
    update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Data Ingestion",
        status="running",
        message=f"Ingesting data from {input_file}"
    )

    try:
        pipeline = DataPipeline.objects.get(id=pipeline_id)
        pipeline.input_file = os.path.basename(input_file)
        pipeline.save()

        # Read data from file
        with open(input_file, 'r') as f:
            data = json.load(f)

        logger.info(f"Ingested {len(data)} records")

        # Update pipeline status
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Ingestion",
            status="completed",
            message=f"Successfully ingested {len(data)} records"
        )

        return data

    except Exception as e:
        logger.error(f"Error ingesting data: {e}")
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Ingestion",
            status="failed",
            message=f"Error ingesting data: {str(e)}"
        )
        raise


@flow(name="Data Pipeline")
async def run_data_pipeline_flow(pipeline_id: int, record_count: int = 1000):
    """
    Main flow that orchestrates the entire data pipeline

    Args:
        pipeline_id: ID of the pipeline to run
        record_count: Number of records to generate
    """
    logger = get_run_logger()
    logger.info(
        f"Starting data pipeline {pipeline_id} with {record_count} records")

    try:
        # Update pipeline status
        pipeline = DataPipeline.objects.get(id=pipeline_id)
        pipeline.status = "running"
        pipeline.save()

        ctx = get_run_context()
        flow_run_id = ctx.flow_run.id if hasattr(ctx, 'flow_run') else None

        if flow_run_id:
            pipeline.prefect_flow_run_id = str(flow_run_id)
            pipeline.save()

        # Execute pipeline stages

        # Stage 1: Generate sample data
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Generation",
            status="running"
        )

        input_file = await generate_data(records=record_count)

        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Generation",
            status="completed",
            message=f"Generated {record_count} records in {os.path.basename(input_file)}"
        )

        # Stage 2: Ingest data
        data = await ingest_data(pipeline_id=pipeline_id, input_file=input_file)

        # Stage 3: Process with Spark
        processed_data = await process_with_spark(pipeline_id=pipeline_id, data=data)

        # Stage 4: Transform with dbt
        transformed_data = await transform_with_dbt(pipeline_id=pipeline_id, data=processed_data)

        # Stage 5: Export results
        output_file = await export_results(pipeline_id=pipeline_id, data=transformed_data)

        # Update final pipeline status
        pipeline.status = "completed"
        pipeline.output_file = os.path.basename(output_file)
        pipeline.records_processed = len(transformed_data)
        pipeline.save()

        logger.info(f"Pipeline {pipeline_id} completed successfully")
        return {"success": True, "pipeline_id": pipeline_id}

    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} failed: {e}")

        # Update pipeline status
        try:
            pipeline = DataPipeline.objects.get(id=pipeline_id)
            pipeline.status = "failed"
            pipeline.error_message = str(e)
            pipeline.save()
        except:
            pass

        return {"success": False, "pipeline_id": pipeline_id, "error": str(e)}


def update_pipeline_status(pipeline_id, stage_name=None, status=None, message=None):
    """
    Helper function to update pipeline and stage status
    """
    try:
        pipeline = DataPipeline.objects.get(id=pipeline_id)

        if stage_name:
            try:
                stage = PipelineStage.objects.get(
                    pipeline_id=pipeline_id,
                    name__iexact=stage_name.replace('_', ' ').title()
                )

                if status:
                    stage.status = status

                if status == "running" and not stage.started_at:
                    stage.started_at = datetime.datetime.now()

                if status == "completed" and not stage.completed_at:
                    stage.completed_at = datetime.datetime.now()
                    if stage.started_at:
                        stage.execution_time_seconds = (
                            stage.completed_at - stage.started_at
                        ).total_seconds()

                if message:
                    stage.description = message

                stage.save()

            except PipelineStage.DoesNotExist:
                pass

        if status and not stage_name:
            pipeline.status = status

        pipeline.save()

    except Exception as e:
        print(f"Error updating pipeline status: {e}")


# For testing purposes
if __name__ == "__main__":
    import asyncio

    # Run the flow
    pipeline_id = 1
    asyncio.run(run_data_pipeline_flow(
        pipeline_id=pipeline_id, record_count=500))


@task(name="process_with_spark")
def process_with_spark(pipeline_id: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process data using PySpark

    In a real scenario, this would use a PySpark cluster to process the data.
    For this demo, we'll simulate the processing.

    Args:
        pipeline_id: ID of the pipeline to update
        data: List of data records

    Returns:
        Processed data
    """
    logger = get_run_logger()
    logger.info(f"Processing {len(data)} records with PySpark")

    # Update pipeline status
    update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Spark Processing",
        status="running",
        message=f"Processing {len(data)} records with PySpark"
    )

    try:
        # In a real scenario, we would use PySpark to process the data
        # For this demo, we'll just simulate it by importing the PySpark module
        # and creating some dummy processing logic
        import pyspark
        from pyspark.sql import SparkSession

        # Log PySpark version
        logger.info(f"Using PySpark version: {pyspark.__version__}")

        # Create SparkSession (local mode)
        spark = SparkSession.builder \
            .appName(f"DataPipeline-{pipeline_id}") \
            .master("local[*]") \
            .getOrCreate()

        # Process data (simulate by sleeping)
        # Scale with data size, max 5 seconds
        processing_time = min(len(data) * 0.01, 5)
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

        # Update pipeline status
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Spark Processing",
            status="completed",
            message=f"Successfully processed {num_records} records"
        )

        # Stop SparkSession
        spark.stop()

        return processed_data

    except Exception as e:
        logger.error(f"Error processing data with Spark: {e}")
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Spark Processing",
            status="failed",
            message=f"Error processing data: {str(e)}"
        )
        raise


@task(name="transform_with_dbt")
def transform_with_dbt(pipeline_id: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform data using dbt

    In a real scenario, this would use dbt to transform data in the database.
    For this demo, we'll simulate the transformation.

    Args:
        pipeline_id: ID of the pipeline to update
        data: List of processed data records

    Returns:
        Transformed data
    """
    logger = get_run_logger()
    logger.info(f"Transforming data with dbt")

    # Update pipeline status
    update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="DBT Transformation",
        status="running",
        message=f"Transforming data with dbt-core"
    )

    try:
        # In a real scenario, we would use dbt to transform data in the database
        # For this demo, we'll simulate the process

        # Write data to a temporary file that dbt could read
        temp_dir = os.path.join(settings.DATA_INPUT_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        temp_file = os.path.join(temp_dir, f"pipeline_{pipeline_id}_data.json")
        with open(temp_file, 'w') as f:
            json.dump(data, f)

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

        # Update pipeline status
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="DBT Transformation",
            status="completed",
            message=f"Successfully transformed {len(transformed_data)} records"
        )

        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)

        return transformed_data

    except Exception as e:
        logger.error(f"Error transforming data with dbt: {e}")
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="DBT Transformation",
            status="failed",
            message=f"Error transforming data: {str(e)}"
        )
        raise


@task(name="export_results")
def export_results(pipeline_id: int, data: List[Dict[str, Any]]) -> str:
    """
    Export the transformed data

    Args:
        pipeline_id: ID of the pipeline to update
        data: List of transformed data records

    Returns:
        Path to the exported data file
    """
    logger = get_run_logger()
    logger.info(f"Exporting {len(data)} records")

    # Update pipeline status
    update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Data Export",
        status="running",
        message=f"Exporting {len(data)} records"
    )

    try:
        # Create output directory if it doesn't exist
        output_dir = settings.DATA_OUTPUT_DIR
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

        # Use Celery task for final processing
        export_task = export_data.delay(pipeline_id, output_file)

        # Update pipeline status
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Export",
            status="completed",
            message=f"Data exported to {os.path.basename(output_file)}"
        )

        return output_file

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        update_pipeline_status(
            pipeline_id=pipeline_id,
            stage_name="Data Export",
            status="failed",
            message=f"Error exporting data: {str(e)}"
        )
        raise
