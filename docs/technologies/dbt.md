---
title: dbt Overview
description: How dbt is used for data transformation and business logic in the pipeline
---

# dbt Overview

[dbt](https://www.getdbt.com/) (data build tool) is used to apply business logic and data transformations to the processed dataset within the pipeline. Although this demo simulates dbt behavior using Python, the design is ready for integration with actual dbt projects.

## Responsibilities

- Apply business rules and logic to processed data
- Perform categorization and enrichment
- Output analytics-ready transformed data
- Simulate transformations typical of dbt SQL models

## Stage Role

This stage runs after Spark processing and before data export. It:

- Evaluates conditions like value thresholds
- Assigns pricing tiers and status flags
- Calculates category-level metrics (e.g., averages)

## Simulated Processing

```python
@task(name="transform_with_dbt")
async def transform_with_dbt(pipeline_id: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for record in data:
        record["tier"] = "premium" if record["total_value"] > 5000 else "standard"
        record["is_high_value"] = record["total_value"] > 1000
```

## Real dbt Integration (Optional)

To integrate real dbt models, you could:

1. Use the dbt CLI inside a container
2. Materialize data into PostgreSQL
3. Call dbt with:

```bash
dbt run --project-dir=/app/dbt_project --profiles-dir=/app/dbt_project
```

## dbt Model Example

```sql
-- models/item_metrics.sql
SELECT *,
    CASE
        WHEN total_value > 5000 THEN 'premium'
        WHEN total_value > 1000 THEN 'standard'
        ELSE 'basic'
    END AS pricing_tier
FROM {{ ref('stg_items') }}
```

## Schema Testing Example

```yaml
version: 2
models:
  - name: item_metrics
    columns:
      - name: total_value
        tests:
          - not_null
          - is_positive
```

## Project Structure

```bash
dbt_project/
├── models/
│   ├── staging/
│   └── marts/
├── macros/
├── dbt_project.yml
├── profiles.yml
```

## Observability with Datadog

Since dbt is simulated:

- Logs are emitted during transformation
- Metrics (records processed, duration) are emitted via `statsd`
- Pipeline status is updated in PostgreSQL

Real dbt jobs can be monitored via:

- Custom log tailing or dbt Cloud APIs
- Step timing and exit codes

## Best Practices

1. Write modular models (`staging`, `marts`, `snapshots`)
2. Test transformations with `schema.yml`
3. Use version control for SQL logic
4. Separate metrics logic from ETL logic

## Summary

dbt is the transformation layer of the pipeline. This stage is simulated in Python but aligns structurally with real dbt workflows. It enables classification, enrichment, and preparation of data for downstream consumption.
