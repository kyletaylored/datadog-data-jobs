import os
from celery import Celery

# Initialize Datadog tracing if available (not required for the demo to work)
try:
    from ddtrace import patch_all
    patch_all()
except ImportError:
    print("Datadog tracing not available, continuing without it.")

# Set the default settings module
os.environ.setdefault('DATABASE_ENGINE', 'postgresql')
os.environ.setdefault('DATABASE_NAME', 'datadog')
os.environ.setdefault('DATABASE_USERNAME', 'datadog')
os.environ.setdefault('DATABASE_PASSWORD', 'datadog')
os.environ.setdefault('DATABASE_HOST', 'db')
os.environ.setdefault('DATABASE_PORT', '5432')

# Create the Celery app
app = Celery('datadog_pipeline')

# Configure the broker URL (RabbitMQ)
app.conf.broker_url = 'amqp://guest:guest@rabbitmq:5672//'

# Configure the result backend (PostgreSQL)
app.conf.result_backend = f"db+postgresql://{os.environ.get('DATABASE_USERNAME')}:{os.environ.get('DATABASE_PASSWORD')}@{os.environ.get('DATABASE_HOST')}:{os.environ.get('DATABASE_PORT')}/{os.environ.get('DATABASE_NAME')}"

# Automatically discover tasks in the 'tasks' module
app.autodiscover_tasks(['app.worker.tasks'])

# Optional: Configure serialization format
app.conf.accept_content = ['json']
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'

# Optional: Configure task routes
app.conf.task_routes = {
    'app.worker.tasks.*': {'queue': 'default'}
}

# Optional: Set timezone
app.conf.timezone = 'UTC'

if __name__ == '__main__':
    app.start()
