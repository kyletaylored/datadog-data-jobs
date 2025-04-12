#!/bin/bash
set -e

# Create data directories if they don't exist and ensure proper permissions
mkdir -p /app/data/input /app/data/output
chmod -R 777 /app/data

# Wait for PostgreSQL to be ready
function postgres_ready() {
  python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname="${DATABASE_NAME:-datadog}",
        user="${DATABASE_USERNAME:-datadog}",
        password="${DATABASE_PASSWORD:-datadog}",
        host="${DATABASE_HOST:-db}"
    )
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
END
}

until postgres_ready; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done
echo "PostgreSQL is ready!"

# Wait for RabbitMQ to be ready
function rabbitmq_ready() {
  python << END
import sys
import pika
try:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq')
    )
    connection.close()
except Exception:
    sys.exit(1)
sys.exit(0)
END
}

until rabbitmq_ready; do
  echo "Waiting for RabbitMQ..."
  sleep 2
done
echo "RabbitMQ is ready!"

# Check if we need to run migrations and setup
# We only want to do this for the web service, not workers/agents
if [[ "$@" == *"runserver"* ]] || [[ "$@" == *"gunicorn"* ]]; then
  echo "Running migrations..."
  python app/manage.py migrate

  echo "Collecting static files..."
  python app/manage.py collectstatic --noinput

  echo "Initializing database..."
  python app/dashboard/init_db.py
fi

# This snippet should be added to your entrypoint.sh script
# It ensures that container DNS resolution is working properly

# Check if prefect-server resolves properly
if ! ping -c 1 prefect-server > /dev/null 2>&1; then
    echo "Adding prefect-server to /etc/hosts..."
    # Find the IP of the prefect-server container via Docker DNS
    PREFECT_IP=$(getent hosts prefect-server | awk '{ print $1 }')
    if [ -z "$PREFECT_IP" ]; then
        echo "Could not resolve prefect-server IP automatically"
        # Use Docker's internal network gateway as fallback
        PREFECT_IP=$(ip route | grep default | awk '{print $3}')
        if [ -z "$PREFECT_IP" ]; then
            echo "Using 127.0.0.1 as fallback for prefect-server"
            PREFECT_IP="127.0.0.1"
        fi
    fi
    echo "$PREFECT_IP prefect-server" >> /etc/hosts
    echo "Updated /etc/hosts with prefect-server entry: $PREFECT_IP"
fi

echo "Entrypoint script completed, starting service..."

# Execute the command passed to the script
exec "$@"