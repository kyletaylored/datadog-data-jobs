---
title: Pipeline Exercises
description: Hands-on exercises for learning, testing, and customizing the pipeline
---

# Pipeline Exercises

This tutorial contains a set of exercises designed to help you learn how the pipeline works, explore customization, and test observability and resilience.

Each exercise includes an objective, instructions, and a follow-up challenge.

---

## 🧪 Exercise 1: Simulate a Failed Stage

**Goal**: Understand how failures are reported and visualized.

### Steps:

1. In `flows.py`, temporarily modify the `ingest_data` task:
   ```python
   raise ValueError("Simulated ingestion error")
   ```
2. Trigger a new pipeline from the UI or API
3. Observe:
   - Datadog trace showing failure
   - Logs containing the exception
   - UI showing stage failure and status: `failed`

**Challenge**: Add error-specific tags to your logs (e.g. `error_type`)

---

## 🧪 Exercise 2: Add a Custom Metric

**Goal**: Track a meaningful value in Datadog.

### Steps:

1. Open `flows.py`, inside `transform_with_dbt` task:
   ```python
   from datadog import statsd
   statsd.gauge("pipeline.records.transformed", len(transformed_data), tags=["stage:dbt"])
   ```
2. Re-run the pipeline
3. Confirm metric appears in Datadog

**Challenge**: Create a Datadog dashboard widget to display this metric.

---

## 🧪 Exercise 3: Add a New Stage (Cleanup)

**Goal**: Extend the pipeline with a cleanup step after export.

### Steps:

1. Define a task `cleanup_temp_files(pipeline_id)`
2. Log a message and remove files in `/app/data/input`
3. Add to the flow after `export_results`

**Challenge**: Monitor this task in the Prefect UI and trace its log in Datadog.

---

## 🧪 Exercise 4: Modify Flow Parameters

**Goal**: Make the pipeline flexible for varying workloads.

### Steps:

1. Update `run_data_pipeline_flow` to accept `record_count`
2. Create a new pipeline from the UI with a higher record count
3. Monitor execution time in Prefect and Datadog

**Challenge**: Chart stage duration vs. record count in a Datadog dashboard.

---

## 🧪 Exercise 5: Break and Fix the Database Connection

**Goal**: See how failures in external services impact the pipeline.

### Steps:

1. Stop the `db` container:
   ```bash
   docker-compose stop db
   ```
2. Trigger a pipeline
3. Observe failure in:
   - FastAPI logs and API response
   - Prefect UI flow run
   - Datadog APM + logs

**Challenge**: Restart DB, rerun, and verify successful recovery.

---

## Summary

These exercises provide hands-on ways to experiment with pipeline features and break things on purpose to understand resilience and monitoring. Feel free to extend these or create your own scenarios to simulate real-world failures and fixes.
