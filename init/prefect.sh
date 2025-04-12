#!/bin/bash
set -e

echo "Starting Prefect initialization..."

# Install curl if not already installed
if ! command -v curl &> /dev/null; then
    echo "Installing curl..."
    apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
fi

# Wait for Prefect server to be ready
echo "Waiting for Prefect server to be ready..."
until curl -s http://prefect-server:4200/api/health > /dev/null 2>&1; do
  sleep 2
done
echo "Prefect server is ready!"

# Make sure DNS resolves correctly
echo "Checking DNS resolution..."
ping -c 1 prefect-server || echo "prefect-server not pingable, but continuing..."

# Adding hostname to /etc/hosts if needed
if ! ping -c 1 prefect-server > /dev/null 2>&1; then
    echo "Adding prefect-server to /etc/hosts..."
    # Find the IP of the prefect-server container
    PREFECT_IP=$(getent hosts prefect-server | awk '{ print $1 }')
    if [ -z "$PREFECT_IP" ]; then
        echo "Using fallback IP for prefect-server"
        PREFECT_IP="127.0.0.1"
    fi
    echo "$PREFECT_IP prefect-server" >> /etc/hosts
fi

# Create worker pool and deploy flows
echo "Creating worker pool and deploying flows..."
# Add a retry mechanism
for i in {1..5}; do
    if python app/pipeline/deploy.py; then
        echo "Prefect deployment completed successfully!"
        break
    else
        echo "Deployment attempt $i failed. Retrying in 5 seconds..."
        sleep 5
    fi
    
    if [ $i -eq 5 ]; then
        echo "Failed to deploy after 5 attempts"
        exit 1
    fi
done

echo "Prefect initialization completed successfully!"