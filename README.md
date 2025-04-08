# Datadog Monitoring Demo for Python Data Stack

This project demonstrates how to use Datadog to monitor a Python-based data processing stack. The demo includes a fully functional data pipeline that simulates real-world data processing using several popular technologies:

- **Prefect**: For workflow orchestration
- **dbt-core**: For data transformation
- **PySpark**: For distributed data processing
- **Celery & RabbitMQ**: For task queuing
- **PostgreSQL**: For data storage
- **Django**: For web interface and API

## Architecture

The demo simulates a complete data pipeline:

1. **Data Generation**: Creates random structured data
2. **Data Ingestion**: Loads data into the processing pipeline
3. **Spark Processing**: Processes data using PySpark
4. **dbt Transformation**: Applies business logic transformations
5. **Data Export**: Exports the processed data to files

All of these processes are monitored with Datadog, allowing you to see metrics, traces, and logs throughout the pipeline.

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

   - Set your Datadog API key in an environment variable:
     ```
     export DD_API_KEY=your_datadog_api_key
     ```
   - If you're using a Datadog site other than US, also set:
     ```
     export DD_SITE=datadoghq.eu
     ```

3. Start the application:

   ```
   docker-compose up -d
   ```

4. Access the web interface:

   ```
   http://localhost:8000
   ```

5. Run a data pipeline:
   - Navigate to the web interface
   - Click "Trigger New Pipeline" to start a data processing run
   - Watch the pipeline progress through the UI

## Using the Demo

### Web Interface

The Django web interface provides:

- Dashboard of all pipeline runs
- Detailed view of each pipeline
- Button to trigger new pipeline runs
- Status monitoring of each stage

### Monitoring with Datadog

If Datadog is set up, you can monitor:

- APM traces of the entire pipeline process
- Metrics from all services
- Logs from the application
- Infrastructure metrics

### Components

- **Prefect UI**: Available at http://localhost:4200
- **RabbitMQ Management**: Available at http://localhost:15672 (guest/guest)
- **Postgres**: Available at localhost:5432
- **Django Admin**: Available at http://localhost:8000/admin (admin/datadog)

## Customization

You can modify the pipeline by:

- Changing the number of records generated
- Adding new transformation stages
- Modifying the dbt models
- Adding new Spark transformations

## Troubleshooting

- If services fail to start, check the logs with `docker-compose logs <service-name>`
- Ensure the required ports (8000, 5432, 5672, 15672, 4200, etc.) are available
- Check that Docker has enough resources allocated

## License

This project is licensed under the MIT License - see the LICENSE file for details.
