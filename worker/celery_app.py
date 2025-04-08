import os
import sys
from celery import Celery

# Add parent directory to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create the Celery app
app = Celery('datadog_demo')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto discover tasks in all registered Django apps
app.autodiscover_tasks()


@app.task(bind=True, name='debug_task')
def debug_task(self):
    """Task for debugging purposes"""
    print(f'Request: {self.request!r}')
