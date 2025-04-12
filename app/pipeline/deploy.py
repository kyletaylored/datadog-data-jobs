#!/usr/bin/env python3
"""
Script to create Prefect deployments for our data pipeline flows
"""
from prefect.filesystems import LocalFileSystem
from prefect.client import get_client
from prefect.deployments import Deployment
from app.pipeline.flows import run_data_pipeline_flow
from pathlib import Path
import asyncio
import sys
import time
import os

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the flow first

# Then import Prefect modules

print("Starting deployment script...")
print(f"Using Prefect API URL: {os.environ.get('PREFECT_API_URL')}")


async def create_worker_pool():
    """Create the default worker pool if it doesn't exist"""
    print("Connecting to Prefect API...")
    client = get_client()

    try:
        # Check if pool exists
        print("Checking for existing worker pools...")
        pools = await client.read_work_pools()
        pool_exists = False

        for pool in pools:
            print(f"Found pool: {pool.name} (ID: {pool.id})")
            if pool.name == "default":
                pool_exists = True
                print("Worker pool 'default' already exists")
                return pool.id

        if not pool_exists:
            print("Creating 'default' worker pool...")
            pool = await client.create_work_pool(
                name="default",
                type="process"
            )
            print(f"Worker pool created with ID: {pool.id}")

            # Create default work queue
            await client.create_work_queue(
                name="default",
                work_pool_name="default"
            )
            print("Default work queue created")
            return pool.id
    except Exception as e:
        print(f"Error creating worker pool: {str(e)}")
        raise


async def deploy_flow():
    """Deploy the flow using the Prefect 3 API"""
    from prefect.client.orchestration import get_client

    try:
        # First ensure work pool exists
        client = get_client()

        # Check if pool exists
        print("Checking for existing worker pools...")
        pools = await client.read_work_pools()
        pool_exists = False

        for pool in pools:
            print(f"Found pool: {pool.name} (ID: {pool.id})")
            if pool.name == "default":
                pool_exists = True
                print("Worker pool 'default' already exists")
                break

        if not pool_exists:
            print("Creating 'default' worker pool...")
            pool = await client.create_work_pool(
                name="default",
                type="process"
            )
            print(f"Worker pool created with ID: {pool.id}")

        # For deployments, we need to use the direct API endpoints
        # since deploy() is not async-compatible
        from app.pipeline.flows import run_data_pipeline_flow
        import inspect

        # Get the source code and details
        source_path = str(Path(__file__).parent.parent)
        entrypoint = "app/pipeline/flows.py:run_data_pipeline_flow"

        print(
            f"Creating deployment from source: {source_path}, entrypoint: {entrypoint}")

        # Create a deployment using the API directly
        deployment = await client.create_deployment(
            name="data-pipeline-deployment",
            flow_id=run_data_pipeline_flow._flow_id,
            work_pool_name="default",
            path=source_path,
            entrypoint=entrypoint,
        )

        print(f"Deployment created with ID: {deployment.id}")

        return deployment.id

    except Exception as e:
        print(f"Error deploying flow: {e}")
        raise


async def main():
    try:
        # Retry mechanism for creating the worker pool
        max_retries = 5
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} to create worker pool")
                pool_id = await create_worker_pool()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                else:
                    print("Maximum retries reached. Giving up.")
                    raise

        # Deploy the flow
        await deploy_flows(pool_id)
        print("Deployment completed successfully")
    except Exception as e:
        print(f"Deployment failed: {e}")
        raise

if __name__ == "__main__":
    print("Running deployment process...")
    asyncio.run(main())
    print("Deployment process completed")
