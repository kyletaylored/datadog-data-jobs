#!/usr/bin/env python3
"""
Script to force deploy the flow using the newer Prefect 3 API
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))


async def force_deploy():
    """Force deploy the flow"""
    # Import here to avoid circular imports
    from app.pipeline.flows import run_data_pipeline_flow
    from prefect.client.orchestration import get_client

    print("Force deploying the flow...")

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

        # Deploy the flow using the newer API
        print("Deploying flow with the new API...")
        deployment_id = await run_data_pipeline_flow.to_deployment(
            name="data-pipeline-deployment",
            work_pool_name="default",
        ).apply()

        print(f"Flow deployed successfully with ID: {deployment_id}")

        # Verify deployment exists
        deployments = await client.read_deployments()
        found = False
        for d in deployments:
            if d.name == "data-pipeline-deployment":
                found = True
                print(f"Verified deployment exists: {d.id} ({d.name})")
                break

        if not found:
            print("WARNING: Deployment was not found after creation!")

        return deployment_id

    except Exception as e:
        print(f"Error in force deploy: {e}")
        raise

if __name__ == "__main__":
    print("Starting force deployment...")
    asyncio.run(force_deploy())
    print("Force deployment completed")
