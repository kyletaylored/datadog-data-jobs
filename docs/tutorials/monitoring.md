---
title: Monitoring the Pipeline
description: How to observe, troubleshoot, and improve pipeline health using Datadog
---

# Monitoring the Pipeline

This tutorial shows how to monitor and debug your pipeline using [Datadog](https://www.datadoghq.com/). Monitoring provides critical visibility into the health, performance, and behavior of every component in your stack.

## Prerequisites

- Datadog Agent enabled (via Docker Compose profile)
- `DD_API_KEY` set in your `.env`

Start with:

```bash
docker-compose --profile with-datadog up -d
```

## Monitoring Layers

| Layer      | Signals Collected                 |
| ---------- | --------------------------------- |
| FastAPI    | APM traces, logs, request metrics |
| Prefect    | Task logs, flow duration, retries |
| Celery     | Task execution traces and logs    |
| PostgreSQL | Query count, locks, errors        |
| Spark      | Executor count, job metrics       |
| RabbitMQ   | Queue length, throughput          |

## Dashboards

Check the prebuilt dashboard (or import the JSON template provided) for:

- Flow durations by stage
- Failure rate and recent errors
- Throughput (records per minute)
- Active Spark executors

## Key Metrics

```text
pipeline.runs
pipeline.errors
pipeline.stage.duration{stage:dbt}
prefect.flow.duration
rabbitmq.queue.length{queue:celery}
spark.job.duration
```

## APM Traces

Every FastAPI request, Prefect task, and Celery job is traced. You can:

- View end-to-end trace of a pipeline
- Drill into slow or failed stages
- Correlate traces with logs and metrics

## Log Search Examples

Search for failed stages:

```text
status:failed source:pipeline
```

View logs by pipeline ID:

```text
pipeline_id:42 service:prefect
```

## Alerts

Create custom monitors using Datadog's metric alert system:

### Pipeline Failures

```yaml
sum(last_5m):sum:pipeline.errors{*} > 0
```

### Stage Duration Spike

```yaml
avg(last_10m):avg:pipeline.stage.duration{stage:spark} > 5
```

### No Pipelines Running

```yaml
change(last_10m):avg:pipeline.runs{*} < 1
```

## Troubleshooting Checklist

- Check **pipeline.runs** for missing executions
- Inspect **pipeline.errors** for high failure counts
- Drill into **APM traces** for span-level analysis
- Search **logs by pipeline ID** for stage failures
- Monitor **queue lengths** for RabbitMQ bottlenecks

## Tips

- Use consistent `pipeline_id` tags across stages
- Add custom metrics for each new task
- Group alerts into notebooks or monitors
- Use Slack or email for alert routing

## Summary

With Datadog, you can instrument and observe your pipeline across every layer: services, queues, databases, and application logic. Traces, logs, and metrics come together to provide full visibility and actionable insights.
