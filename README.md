# Datadog Data Pipeline Demo

This project demonstrates how to use Datadog to monitor a Python-based data processing stack. The demo includes a fully functional data pipeline that simulates real-world data processing using several popular technologies.

## Architecture

The demo simulates a complete data pipeline with the following components:

- **FastAPI**: For web interface and API
- **Prefect**: For workflow orchestration
- **PostgreSQL**: For data storage
- **PySpark**: For distributed data processing
- **Celery & RabbitMQ**: For task queuing
- **Datadog**: For monitoring and observability

The pipeline consists of these stages:

1. **Data Generation**: Creates random structured data
2. **Data Ingestion**: Loads data into the processing pipeline
3. **Spark Processing**: Processes data using PySpark
4. **dbt Transformation**: Applies business logic transformations
5. **Data Export**: Exports the processed data to files

## Prerequisites

- Docker and Docker Compose
- Datadog account (optional for monitoring features)

## Quick Start

1. Clone this repository:

   ```
   git clone <repository-url>
   cd datadog-demo
   ```

2. (Optional) Set up Datadog:

   - Add your Datadog API key to the `.env` file

3. Start the application:

   ```bash
   # Without Datadog monitoring
   docker-compose up -d

   # With Datadog monitoring (if API key is set)
   docker-compose --profile with-datadog up -d
   ```

4. Access the web interface:

   ```
   http://localhost:8000
   ```

5. Run a data pipeline:
   - Navigate to the web interface
   - Click "Trigger New Pipeline" to start a data processing run
   - Watch the pipeline progress through the UI

## Components

- **FastAPI UI**: Available at http://localhost:8000
- **Prefect UI**: Available at http://localhost:4200
- **RabbitMQ Management**: Available at http://localhost:15672 (guest/guest)
- **Postgres**: Available at localhost:5432
- **Spark Master UI**: Available at http://localhost:8080

## File Structure

```
datadog-demo/
├── app/                      # FastAPI application
│   ├── main.py               # Main application file
│   ├── api/                  # API routes
│   ├── db/                   # Database models
│   ├── pipeline/             # Pipeline flows
│   ├── templates/            # HTML templates
│   └── static/               # Static files
├── data/                     # Data directory
│   ├── input/                # Input data files
│   └── output/               # Output data files
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker build instructions
├── requirements.txt          # Python dependencies
└── .env                      # Environment variables
```

## Monitoring with Datadog

If you've set up Datadog, you can monitor:

- APM traces of the entire pipeline process
- Metrics from all services
- Logs from the application
- Infrastructure metrics

## Customization

You can modify the pipeline by:

- Changing the number of records generated
- Adding new transformation stages
- Modifying the processing logic

## Troubleshooting

- If services fail to start, check the logs with `docker-compose logs <service-name>`
- Ensure the required ports (8000, 5432, 5672, 15672, 4200, etc.) are available
- Check that Docker has enough resources allocated
