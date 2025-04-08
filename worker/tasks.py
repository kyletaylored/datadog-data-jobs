from dashboard.models import DataPipeline, PipelineStage
import django
import os
import json
import time
import random
import sys
import datetime
import requests
from celery import shared_task

# Add app directory to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../app')))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()


# Initialize Datadog tracing if available (not required for the demo to work)
try:
    from ddtrace import patch_all
    patch_all()
except ImportError:
    print("Datadog tracing not available, continuing without it.")


@shared_task(name="process_data_batch")
def process_data_batch(pipeline_id, batch_id, data):
    """
    Process a batch of data in the pipeline

    This is a long-running task that would typically be used in a real
    data processing pipeline to handle a batch of records.
    """
    # Simulate processing time
    processing_time = random.uniform(1.0, 3.0)
    time.sleep(processing_time)

    # Process data
    result = {
        "batch_id": batch_id,
        "records_processed": len(data),
        "processing_time": processing_time,
        "timestamp": datetime.datetime.now().isoformat()
    }

    # Update the pipeline record with progress
    update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Data Processing",
        status="running",
        message=f"Processed batch {batch_id} with {len(data)} records"
    )

    return result


@shared_task(name="aggregate_results")
def aggregate_results(pipeline_id, results):
    """
    Aggregate results from multiple batches

    This task would typically consolidate results from multiple batches
    of processed data.
    """
    # Simulate aggregation time
    aggregation_time = random.uniform(0.5, 1.5)
    time.sleep(aggregation_time)

    # Calculate totals
    total_records = sum(r.get("records_processed", 0) for r in results)
    total_time = sum(r.get("processing_time", 0) for r in results)

    # Update pipeline with totals
    try:
        pipeline = DataPipeline.objects.get(id=pipeline_id)
        pipeline.records_processed = total_records
        pipeline.save()
    except DataPipeline.DoesNotExist:
        pass

    return {
        "pipeline_id": pipeline_id,
        "total_records": total_records,
        "total_processing_time": total_time,
        "timestamp": datetime.datetime.now().isoformat()
    }


@shared_task(name="export_data")
def export_data(pipeline_id, output_path):
    """
    Export processed data to a file

    This task simulates exporting data to an output file after processing.
    """
    # Simulate export time
    export_time = random.uniform(1.0, 2.0)
    time.sleep(export_time)

    # Update pipeline status
    update_pipeline_status(
        pipeline_id=pipeline_id,
        stage_name="Data Export",
        status="running",
        message=f"Exporting data to {output_path}"
    )

    # In a real scenario, we would write actual data here
    try:
        pipeline = DataPipeline.objects.get(id=pipeline_id)
        pipeline.output_file = output_path
        pipeline.save()

        # Write a sample file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(f"# Data export from pipeline {pipeline_id}\n")
            f.write(f"# Generated at {datetime.datetime.now().isoformat()}\n")
            f.write(f"# Total records: {pipeline.records_processed}\n\n")

            # Write some dummy data
            f.write("id,name,value,processed_at\n")
            for i in range(min(10, pipeline.records_processed)):
                f.write(
                    f"{i},item_{i},{random.random():.4f},{datetime.datetime.now().isoformat()}\n")

        return {"success": True, "file": output_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_pipeline_status(pipeline_id, stage_name=None, status=None, message=None):
    """
    Helper function to update pipeline status

    This could make an API call to the Django app or update the DB directly.
    In a real-world scenario, this might be separated into its own service.
    """
    try:
        # Method 1: Direct DB update (works when sharing the same DB)
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

        except DataPipeline.DoesNotExist:
            pass

        # Method 2: API call (more resilient in distributed systems)
        try:
            payload = {
                'pipeline_id': pipeline_id,
                'stage_name': stage_name.replace('_', ' ').title() if stage_name else None,
                'status': status,
                'error_message': message if status == 'failed' else None
            }

            requests.post(
                'http://webapp:8000/api/update-status/',
                json=payload,
                timeout=5
            )
        except Exception as e:
            print(f"Failed to update pipeline via API: {e}")

    except Exception as e:
        print(f"Error updating pipeline status: {e}")
