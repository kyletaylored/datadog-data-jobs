---
title: PostgreSQL Overview
description: How PostgreSQL is used for pipeline metadata, status tracking, and future data warehousing
---

# PostgreSQL Overview

[PostgreSQL](https://www.postgresql.org/) serves as the main metadata and pipeline tracking database in the demo. It provides persistent storage for pipeline runs, stage statuses, flow metadata, and future support for warehousing output datasets.

## Responsibilities

- Store metadata for each pipeline run
- Track stage-level execution and status
- Record the number of records processed and error messages
- Enable the UI to display pipeline progress and outcomes
- Act as the backend for potential dbt model materialization

## Usage in the Pipeline

- Initialized with a single schema storing `pipelines` and `pipeline_stages`
- Used by FastAPI for all reads and writes
- Used by Prefect tasks to update execution status

## Data Models

### `pipelines`

Stores overall run metadata:

| Column            | Type     | Description                                 |
| ----------------- | -------- | ------------------------------------------- |
| id                | Integer  | Unique ID for the pipeline                  |
| status            | String   | One of: pending, running, completed, failed |
| created_at        | DateTime | Timestamp of creation                       |
| completed_at      | DateTime | Timestamp of completion                     |
| records_processed | Integer  | Total number of output records              |
| error_message     | String   | Top-level error, if any                     |

### `pipeline_stages`

Stores stage-level information:

| Column            | Type    | Description                                 |
| ----------------- | ------- | ------------------------------------------- |
| id                | Integer | Unique ID for the stage                     |
| pipeline_id       | Integer | Foreign key to pipeline                     |
| stage_name        | String  | Descriptive stage label                     |
| status            | String  | One of: pending, running, completed, failed |
| error_message     | String  | Error message for the stage                 |
| records_processed | Integer | Optional: rows handled by stage             |

## ORM Integration

SQLAlchemy models live in `app/db/models.py`, and are accessed via CRUD helpers in `app/db/crud.py`.

Example:

```python
pipeline = crud.create_pipeline(db, pipeline.dict())
stages = crud.get_pipeline_stages(db, pipeline_id=1)
```

## Observability

PostgreSQL is monitored via the Datadog Agent:

- **Health Checks**: `pg_isready` via Docker healthcheck
- **Logs**: Collected from the container
- **Metrics**: Collected automatically (queries per second, errors, locks)

Datadog autodiscovery label:

```yaml
labels:
  com.datadoghq.ad.logs: '[{"source": "postgresql", "service": "postgres"}]'
  com.datadoghq.ad.checks: '{"postgres": { "init_config": {}, "instances": [{"dbm": true}]}}'
```

## Connection Configuration

Environment variables are used in Docker Compose:

```env
DATABASE_HOST=db
DATABASE_NAME=datadog
DATABASE_USERNAME=datadog
DATABASE_PASSWORD=datadog
DATABASE_PORT=5432
```

These are injected into FastAPI, Celery, Prefect, and dbt containers.

## Future Usage

- Used by dbt to materialize models and serve as a warehouse
- Enables historical dashboards by joining pipeline + performance metadata
- Can be extended to store full payloads or analytics output

## Summary

PostgreSQL is the central source of truth for pipeline metadata, driving the FastAPI dashboard, enabling Prefect status tracking, and acting as a future data warehouse. It's a reliable, open-source core of the demo stack.
