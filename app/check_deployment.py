#!/usr/bin/env python3
"""
Script to check existing Prefect deployments using the newer Prefect 3 API
"""
import asyncio
import os


async def list_deployments():
    """List all deployments registered with the Prefect server"""
    from prefect.client.orchestration import get_client

    try:
        print("Connecting to Prefect API...")
        client = get_client()

        print("Fetching deployments...")
        deployments = await client.read_deployments()

        if not deployments:
            print("No deployments found!")
            return

        print(f"Found {len(deployments)} deployments:")
        for deployment in deployments:
            print(f"  - ID: {deployment.id}")
            print(f"    Name: {deployment.name}")
            print(f"    Flow Name: {deployment.flow_name}")
            print(f"    Work Pool: {deployment.work_pool_name}")
            print("    -----")

    except Exception as e:
        print(f"Error listing deployments: {str(e)}")
        raise


async def create_deployment():
    """Create a deployment manually with the newer Prefect 3 API"""
    try:
        print("Creating deployment manually...")

        # Import the flow
        from app.pipeline.flows import run_data_pipeline_flow

        # Use the newer API to deploy the flow
        deployment_id = await run_data_pipeline_flow.to_deployment(
            name="data-pipeline-deployment",
            work_pool_name="default",
        ).apply()

        print(f"Deployment created with ID: {deployment_id}")

    except Exception as e:
        print(f"Error creating deployment: {str(e)}")
        raise


async def main():
    """Main function"""
    await list_deployments()

    # Ask if we should create a deployment
    create = input(
        "Would you like to create a deployment? (y/n): ").lower() == 'y'
    if create:
        await create_deployment()
        # List again to verify
        await list_deployments()

if __name__ == "__main__":
    asyncio.run(main())
