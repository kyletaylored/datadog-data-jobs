"""
Helper functions for integrating with Celery tasks
"""
import logging
import uuid
from typing import List, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)


async def process_data_with_celery(data: List[Dict], pipeline_id: int = None, batch_size: int = 200):
    """
    Process data using Celery workers

    Args:
        data: The data to process
        pipeline_id: The ID of the pipeline
        batch_size: Number of records per batch

    Returns:
        dict: Processing results
    """
    try:
        from app.worker.celery_app import app
        from app.worker.tasks import process_data_batch, aggregate_results

        logger.info(
            f"Processing {len(data)} records with Celery (batch size: {batch_size})")

        # Split data into batches
        batches = [data[i:i + batch_size]
                   for i in range(0, len(data), batch_size)]
        logger.info(f"Split data into {len(batches)} batches")

        # Process each batch
        tasks = []
        for i, batch in enumerate(batches):
            batch_id = f"{pipeline_id}_{uuid.uuid4().hex[:8]}_{i}"
            task = process_data_batch.delay(batch_id, batch, pipeline_id)
            tasks.append(task)

        # Wait for all tasks to complete
        logger.info(f"Waiting for {len(tasks)} Celery tasks to complete")
        results = [task.get() for task in tasks]

        # Aggregate results
        aggregated = aggregate_results.delay(results).get()

        return {
            'success': True,
            'total_records': aggregated['total_records'],
            'processing_time': aggregated['total_processing_time'],
            'batches': len(batches)
        }

    except Exception as e:
        logger.error(f"Error processing data with Celery: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def export_data_with_celery(data: List[Dict], filename: str = None, pipeline_id: int = None):
    """
    Export data using Celery

    Args:
        data: The data to export
        filename: The filename to export to
        pipeline_id: The ID of the pipeline

    Returns:
        dict: Export results
    """
    try:
        from app.worker.celery_app import app
        from app.worker.tasks import export_data

        logger.info(f"Exporting {len(data)} records with Celery")

        # Execute export task
        result = export_data.delay(data, filename, pipeline_id).get()

        return {
            'success': True,
            'filename': result['filename'],
            'record_count': result['record_count']
        }

    except Exception as e:
        logger.error(f"Error exporting data with Celery: {e}")
        return {
            'success': False,
            'error': str(e)
        }
