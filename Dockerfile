# Stage 1: Base build stage
FROM python:3.9-slim AS builder

# Create the app directory
WORKDIR /app

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN pip install --upgrade pip

# Copy the requirements file first (better caching)
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Java builder for PySpark
FROM openjdk:11-jre-slim AS java-builder

# No need to install anything else, just keeping the Java installation

# Stage 3: Production stage
FROM python:3.9-slim

# Create a non-root user
RUN useradd -m -r appuser && \
    mkdir -p /app/data/input /app/data/output && \
    chown -R appuser /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DBT_PROFILES_DIR=/app/dbt_project
ENV DJANGO_SETTINGS_MODULE=core.settings
ENV PATH="/app:${PATH}"

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy Java from the java-builder (needed for PySpark)
COPY --from=java-builder /usr/local/openjdk-11 /usr/local/openjdk-11
ENV JAVA_HOME=/usr/local/openjdk-11

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Make the entrypoint script executable
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set up dbt
RUN mkdir -p /home/appuser/.dbt && \
    ln -s /app/dbt_project/profiles.yml /home/appuser/.dbt/profiles.yml && \
    chown -R appuser:appuser /home/appuser/.dbt

# Expose ports for Django and other services
EXPOSE 8000

# Switch to non-root user
USER appuser

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (will be overridden in docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "core.wsgi:application"]