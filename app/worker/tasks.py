import time
import logging
import json
import os
from celery import shared_task
import datetime
import random

# Initialize Datadog tracing if available (not required for the demo to work)
try:
    from ddtrace import patch_all
    patch_all()
except ImportError:
    print("Datadog tracing not available, continuing without it.")

logger = logging.getLogger(__name__)


@shared_task(name="process_data_batch")
def process_data_batch(batch_id, data, pipeline_id=None):
    """
    Process a batch of data

    Args:
        batch_id (str): The ID of the batch
        data (list): The data to process
        pipeline_id (int, optional): The ID of the associated pipeline

    Returns:
        dict: Processing results
    """
    logger.info(f"Processing batch {batch_id} with {len(data)} records")

    # Simulate processing time (proportional to data size)
    processing_time = random.uniform(0.5, 2.0) * (len(data) / 100)
    time.sleep(processing_time)

    # Simulate data processing
    results = []
    for item in data:
        # Apply some transformations
        processed_item = item.copy()
        if 'value' in item and 'quantity' in item:
            processed_item['total_value'] = item['value'] * item['quantity']
        processed_item['processed_at'] = datetime.datetime.now().isoformat()
        processed_item['processed_by'] = 'celery'
        results.append(processed_item)

    logger.info(f"Batch {batch_id} processed in {processing_time:.2f}s")

    return {
        'batch_id': batch_id,
        'pipeline_id': pipeline_id,
        'processed_count': len(results),
        'processing_time': processing_time,
        'timestamp': datetime.datetime.now().isoformat()
    }


@shared_task(name="export_data")
def export_data(data, filename=None, pipeline_id=None):
    """
    Export data to a file

    Args:
        data (list): The data to export
        filename (str, optional): The filename to export to
        pipeline_id (int, optional): The ID of the associated pipeline

    Returns:
        dict: Export results
    """
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.json"

    # Ensure the filename has a path
    if not os.path.dirname(filename):
        filename = os.path.join('/app/data/output', filename)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    logger.info(f"Exporting {len(data)} records to {filename}")

    # Simulate export time
    export_time = random.uniform(0.5, 1.5)
    time.sleep(export_time)

    # Write the data to a file
    with open(filename, 'w') as f:
        json.dump({
            'data': data,
            'metadata': {
                'count': len(data),
                'exported_at': datetime.datetime.now().isoformat(),
                'pipeline_id': pipeline_id
            }
        }, f, indent=2)

    logger.info(f"Data exported to {filename} in {export_time:.2f}s")

    return {
        'filename': filename,
        'record_count': len(data),
        'export_time': export_time,
        'timestamp': datetime.datetime.now().isoformat()
    }


@shared_task(name="aggregate_results")
def aggregate_results(results):
    """
    Aggregate multiple processing results

    Args:
        results (list): List of processing results

    Returns:
        dict: Aggregated results
    """
    logger.info(f"Aggregating {len(results)} results")

    # Simulate aggregation time
    aggregation_time = random.uniform(0.2, 0.8)
    time.sleep(aggregation_time)

    # Calculate aggregated metrics
    total_records = sum(r.get('processed_count', 0) for r in results)
    total_time = sum(r.get('processing_time', 0) for r in results)

    logger.info(
        f"Aggregated {total_records} records processed in {total_time:.2f}s total")

    return {
        'total_records': total_records,
        'total_processing_time': total_time,
        'batch_count': len(results),
        'timestamp': datetime.datetime.now().isoformat()
    }
