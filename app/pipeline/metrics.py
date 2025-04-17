import json
import os
import logging
from typing import List, Dict

try:
    from datadog import statsd
    DATADOG_ENABLED = True
except ImportError:
    DATADOG_ENABLED = False

logger = logging.getLogger(__name__)


def read_transformed_metrics() -> List[Dict[str, str | float]]:
    """
    Parses dbt run_results.json and optionally sends metrics to Datadog.

    Returns a list of dictionaries containing per-model metrics.
    """
    results_file = os.path.join("dbt_project", "target", "run_results.json")

    if not os.path.exists(results_file):
        logger.warning(
            "run_results.json not found. Skipping metrics emission.")
        return []

    with open(results_file) as f:
        data = json.load(f)

    metrics = []
    for result in data.get("results", []):
        unique_id = result.get("unique_id")
        status = result.get("status")
        execution_time = result.get("execution_time", 0)

        model_name = unique_id.split(".")[-1]
        tags = [f"model:{model_name}", f"status:{status}"]

        metrics.append({
            "model": model_name,
            "status": status,
            "execution_time": execution_time
        })

        logger.info(
            f"[dbt-metrics] {model_name} | status={status} | time={execution_time}s")

        if DATADOG_ENABLED:
            statsd.gauge("dbt_core.model.execution_time",
                         execution_time, tags=tags)
            statsd.gauge("dbt_core.model.status_code",
                         0 if status == "success" else 1, tags=tags)

    return metrics
