#!/bin/bash
set -e

echo "Starting RabbitMQ initialization..."

# Install curl if not already installed
if ! command -v curl &> /dev/null; then
    echo "Installing curl..."
    apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
fi

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ..."
until curl -s http://rabbitmq:15672/api/aliveness-test/%2F -u guest:guest > /dev/null 2>&1; do
  sleep 2
done
echo "RabbitMQ is ready!"

# Optional: Set up RabbitMQ queues, exchanges, etc. if needed
# Example: create a queue
# curl -u guest:guest -X PUT http://rabbitmq:15672/api/queues/%2F/my-queue

echo "RabbitMQ initialization completed successfully!"