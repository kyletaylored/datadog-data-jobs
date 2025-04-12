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

# Run database migrations using Alembic if migrations directory exists
if [ -d "/app/alembic" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

echo "Entrypoint script completed, starting service..."

# Execute the command passed to the script
exec "$@"