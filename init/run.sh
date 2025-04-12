#!/bin/bash
set -e

echo "Starting initialization sequence..."

# Make sure all scripts are executable
chmod +x /app/init/*.sh

# Run each initialization script in sequence
echo "Running database initialization..."
/app/init/db.sh &

echo "Running RabbitMQ initialization..."
/app/init/rabbitmq.sh &

echo "Running Prefect initialization..."
/app/init/prefect.sh &

# Add other init scripts as needed
wait
echo "All initialization tasks completed successfully!"