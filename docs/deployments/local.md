---
title: Local Deployment Guide
description: How to run the data pipeline locally with Docker Compose
---

# Local Deployment Guide

This guide explains how to run the entire data pipeline locally using Docker Compose.

## Requirements

- [Docker](https://www.docker.com/) and Docker Compose v2+
- `.env` file with required variables (see example below)
- Optional: [Datadog account](https://www.datadoghq.com/) for observability

## Quickstart

```bash
git clone https://github.com/your-repo/datadog-data-jobs.git
cd datadog-data-jobs
cp .env.example .env
docker-compose up --build
```

This launches:

- FastAPI app (UI + API)
- PostgreSQL
- Prefect Server + Worker
- Spark Master + Worker
- RabbitMQ
- Celery Worker
- Optional: Datadog Agent

## Environment Configuration

Update your `.env` file with any needed values:

```env
DATABASE_NAME=datadog
DATABASE_USERNAME=datadog
DATABASE_PASSWORD=datadog
DD_API_KEY=your_datadog_api_key
```

## Docker Profiles

To run with Datadog:

```bash
docker-compose --profile with-datadog up -d
```

To run minimal stack without Datadog:

```bash
docker-compose up -d
```

## Service Ports

| Service       | Port       | Description              |
| ------------- | ---------- | ------------------------ |
| FastAPI UI    | `8000`     | Main dashboard           |
| Prefect UI    | `4200`     | Flow orchestration       |
| RabbitMQ UI   | `15672`    | Broker management        |
| Spark Master  | `8080`     | Spark job viewer         |
| PostgreSQL    | `5432`     | DB (internal only)       |
| Datadog Agent | _internal_ | Traces + Logs if enabled |

## Data Volumes

- `./data/` holds all input and output JSON
- Docker volumes used for `postgres_data`, `rabbitmq_data`, `prefect_data`

## Common Commands

| Action             | Command                                                  |
| ------------------ | -------------------------------------------------------- |
| Start all services | `docker-compose up -d`                                   |
| View logs          | `docker-compose logs -f`                                 |
| Trigger a pipeline | Use UI or `curl -X POST http://localhost:8000/trigger/1` |
| Shutdown stack     | `docker-compose down -v`                                 |

## Troubleshooting

<details>
<summary>Port already in use</summary>

Stop conflicting services or update the ports in `docker-compose.yml`

</details>

<details>
<summary>Prefect worker not executing flows</summary>

Make sure the worker container is running and connected to the default work queue.

</details>

<details>
<summary>Database connection failed</summary>

Ensure `db` service is healthy and environment variables match.

</details>

## Summary

Running locally is the best way to develop and demo this pipeline. Use Docker Compose profiles to optionally include Datadog. All services work together in a fully containerized environment with minimal setup.
