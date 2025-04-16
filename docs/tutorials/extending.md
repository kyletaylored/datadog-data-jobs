---
title: Extending the Pipeline
description: How to add new stages or customize existing ones in the pipeline
---

# Extending the Pipeline

This tutorial explains how to customize or add new stages to the pipeline. The architecture is modular and designed for flexibility, making it easy to experiment, add features, or simulate real-world pipelines.

## When to Extend

- Add a new processing or validation step
- Simulate external service interactions (e.g., Slack alerts, S3 uploads)
- Replace a simulated stage with a real implementation (e.g., Spark or dbt)

## Step-by-Step Example: Add a Notification Stage

Let’s walk through adding a `send_notification` stage to the pipeline that runs after export.

### 1. Define the New Task

In `app/pipeline/flows.py`:

```python
@task(name="send_notification", retries=1)
async def send_notification(pipeline_id: int):
    from app.pipeline.utils import notify_slack
    message = f"✅ Pipeline {pipeline_id} completed successfully."
    await notify_slack(message)
```

### 2. Add the Task to the Flow

Update `run_data_pipeline_flow`:

```python
# After export_results...
await send_notification(pipeline_id=pipeline_id)
```

### 3. Implement the Utility Function (Optional)

In `app/pipeline/utils.py`:

```python
import httpx

async def notify_slack(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    await httpx.post(webhook_url, json={"text": message})
```

### 4. Update Environment Variables

Add to `.env`:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/real/webhook
```

## Adding a New Stage with Inputs/Outputs

1. Define a new `@task` function
2. Accept upstream data as input parameter
3. Return modified data
4. Insert the stage in the appropriate position in the flow

```python
@task(name="my_custom_stage")
async def my_custom_stage(pipeline_id: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # your transformation here
    return data
```

Then insert it between stages:

```python
data = await ingest_data(...)
data = await my_custom_stage(pipeline_id=pipeline_id, data=data)
```

## Best Practices

- Use descriptive `@task(name=...)` for traceability in Prefect UI
- Keep reusable logic in `utils.py` or a `lib/` module
- Add logs and update pipeline status as needed
- Use retries and error handling consistently

## Ideas for New Stages

- ❄️ Upload output to S3
- 📬 Send email notifications
- 📊 Generate summary statistics
- 🔐 Run validation or quality checks
- 🧹 Clean temporary data

## Summary

Extending the pipeline is straightforward: create a new task, add it to the flow, and optionally log status or send notifications. This pattern allows for iterative development and easy experimentation.
