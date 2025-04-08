#!/bin/bash
set -e

echo "Starting database initialization..."

# Install PostgreSQL client if not already installed
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL client..."
    apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*
fi

# Create databases if they don't exist, handling errors gracefully
echo "Checking if database ${DATABASE_NAME} exists..."
PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USERNAME -c "SELECT 1 FROM pg_database WHERE datname = '${DATABASE_NAME}'" | grep -q 1 || \
  PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USERNAME -c "CREATE DATABASE ${DATABASE_NAME}"

# Create the Prefect database if it doesn't exist
echo "Checking if database prefect exists..."
PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USERNAME -c "SELECT 1 FROM pg_database WHERE datname = 'prefect'" | grep -q 1 || \
  PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USERNAME -c "CREATE DATABASE prefect"

echo "Database initialization completed successfully!"