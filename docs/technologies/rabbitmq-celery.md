---
title: RabbitMQ & Celery Overview
description: How RabbitMQ and Celery are used for asynchronous background processing in the pipeline
---

# RabbitMQ & Celery Overview

[RabbitMQ](https://www.rabbitmq.com/) is used as a message broker for background task execution, and [Celery](https://docs.celeryq.dev/) is the distributed task queue framework that connects workers to pipeline services. In this demo, they're used to support async scalability and future offloading of resource-intensive tasks.

## Responsibilities

- Enable async background processing outside FastAPI’s request lifecycle
- Allow task offloading for potentially long-running jobs (e.g. exporting, validation)
- Provide a message-passing backbone for horizontally scalable workers

## Role in the Pipeline

Currently:

- Celery is defined and started in `app/worker/`
- RabbitMQ is deployed via Docker and exposes both AMQP and management UI
- Celery is not yet used in core stages, but is ready to be integrated

## Diagram

```mermaid
graph TD
    FastAPI --> CeleryApp
    CeleryApp --> RabbitMQ[(RabbitMQ Broker)]
    RabbitMQ --> CeleryWorker[Celery Worker]
    CeleryWorker --> PostgreSQL
    CeleryWorker --> Datadog
```

## Implementation Details

### Celery Configuration

```python
# app/worker/celery_app.py
from celery import Celery

celery_app = Celery(
    "pipeline_tasks",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend=None
)
```

### Example Task (Placeholder)

```python
@celery_app.task(name="example_task")
def example_task(pipeline_id):
    print(f"Running async task for pipeline {pipeline_id}")
```

### Running the Worker

The Celery worker is started via Docker Compose:

```bash
celery -A app.worker.celery_app worker --loglevel=info
```

## RabbitMQ Configuration

Defined in `docker-compose.yml`:

```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - "5672:5672"
    - "15672:15672" # Admin UI
  healthcheck:
    test: ["CMD", "rabbitmqctl", "status"]
```

Access UI at:

```bash
http://localhost:15672
# Username: guest
# Password: guest
```

## Observability with Datadog

RabbitMQ is monitored via:

- Queue length and throughput
- Connection status
- Container logs

Celery tasks can be traced using Datadog’s Python APM:

```python
from ddtrace import patch_all
patch_all(celery=True)
```

## Future Use Cases

- Export large datasets in the background
- Send Slack/email alerts on failure
- Validate or transform uploads asynchronously
- Trigger downstream APIs post-run

## Summary

RabbitMQ and Celery form the backbone of asynchronous processing in this demo. Though currently not tied to the main pipeline flow, they're fully integrated and ready for scaling workloads across multiple workers and async task types.
