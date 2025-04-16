---
title: Production Deployment Guide
description: Recommendations and considerations for deploying the pipeline in a production environment
---

# Production Deployment Guide

This guide outlines best practices and considerations for deploying the pipeline demo into a production-like environment. While the current implementation is containerized for local use, it can be adapted for scalable cloud-based deployments.

## Recommended Stack

| Component          | Recommendation                            |
| ------------------ | ----------------------------------------- |
| Container Runtime  | Docker or containerd                      |
| Orchestration      | Kubernetes (K8s) or Docker Swarm          |
| Message Broker     | Managed RabbitMQ (e.g. CloudAMQP)         |
| Database           | Managed PostgreSQL (e.g. RDS, Cloud SQL)  |
| Monitoring         | Datadog (SaaS) or OpenTelemetry collector |
| Flow Orchestration | Prefect Cloud or Prefect Orion Server     |

## Deployment Targets

- **Kubernetes**: Deploy each service as its own `Deployment` + `Service`
- **Docker Swarm**: Stack mode with secrets and scaling
- **Cloud Run / Fargate**: Stateless services (FastAPI, Celery)

## Scaling Considerations

| Component      | Scaling Strategy                         |
| -------------- | ---------------------------------------- |
| FastAPI        | Horizontal pod autoscaler + ingress      |
| Celery Worker  | Multiple replicas for parallel task load |
| Prefect Worker | Run as Job or DaemonSet for reliability  |
| RabbitMQ       | Use persistent storage + monitoring      |
| Spark          | External Spark cluster or EMR            |

## Secrets Management

Use external secret managers for production credentials:

- AWS Secrets Manager
- GCP Secret Manager
- HashiCorp Vault

## Environment Variables

Use `.env.production` and load securely in your runtime:

```bash
env $(cat .env.production | xargs) docker-compose -f docker-compose.yml up -d
```

Or define via Kubernetes `Secrets` and reference in container specs.

## Logging & Monitoring

Use centralized logging and observability:

- Route logs to Datadog, Loki, or Elastic
- Use Datadog Agent or OpenTelemetry Collector as sidecars
- Configure alerts on failed pipeline runs and slow stages

## Storage

- Mount a shared volume or use object storage (e.g. S3, GCS) for input/output data
- Persist PostgreSQL and RabbitMQ storage with cloud-native volumes or stateful sets

## CI/CD Integration

Use GitHub Actions or similar to:

- Build and publish container images
- Lint and test Python and dbt models
- Deploy via Helm or Docker Compose

## Summary

To move to production, containerize each service independently, secure credentials, and connect to scalable cloud-based infrastructure. Use orchestration tools like Kubernetes to automate deployments and manage lifecycle. Monitor everything via Datadog or another full-stack observability platform.
