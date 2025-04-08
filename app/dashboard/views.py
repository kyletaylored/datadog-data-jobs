from prefect.flows import run_data_pipeline_flow
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DataPipeline, PipelineStage
from .serializers import DataPipelineSerializer, PipelineStageSerializer
import json
import os
from prefect.client import get_client
from prefect import flow
import asyncio
import sys

# Add parent directory to path to allow imports
sys.path.append('/app')


class DashboardView:
    """Views for the dashboard UI"""

    @staticmethod
    def index(request):
        """Dashboard home page"""
        pipelines = DataPipeline.objects.all().order_by('-created_at')
        return render(request, 'dashboard/index.html', {'pipelines': pipelines})

    @staticmethod
    def pipeline_detail(request, pipeline_id):
        """Detail view for a specific pipeline"""
        pipeline = get_object_or_404(DataPipeline, id=pipeline_id)
        stages = pipeline.stages.all().order_by('id')
        return render(request, 'dashboard/pipeline_detail.html', {'pipeline': pipeline, 'stages': stages})

    @staticmethod
    @csrf_exempt
    def trigger_pipeline(request):
        """Trigger a new data pipeline run"""
        if request.method == 'POST':
            try:
                # Create pipeline record
                pipeline = DataPipeline.objects.create(
                    name=f"Data Pipeline Run {DataPipeline.objects.count() + 1}",
                    description="Automated data processing pipeline",
                    status="pending"
                )

                # Create stages
                stages = [
                    "data_generation",
                    "data_ingestion",
                    "spark_processing",
                    "dbt_transformation",
                    "data_export"
                ]

                for stage_name in stages:
                    PipelineStage.objects.create(
                        pipeline=pipeline,
                        name=stage_name.replace('_', ' ').title(),
                        description=f"Pipeline stage: {stage_name}",
                        status="pending"
                    )

                # Trigger Prefect flow asynchronously
                asyncio.run(trigger_prefect_flow(pipeline.id))

                messages.success(request, "Pipeline triggered successfully!")
                return redirect('pipeline_detail', pipeline_id=pipeline.id)

            except Exception as e:
                messages.error(request, f"Error triggering pipeline: {str(e)}")
                return redirect('index')

        return redirect('index')

    @staticmethod
    @csrf_exempt
    def update_pipeline_status(request):
        """API endpoint to update pipeline status from Prefect"""
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                pipeline_id = data.get('pipeline_id')
                stage_name = data.get('stage_name')
                status = data.get('status')
                error_message = data.get('error_message', None)
                records_processed = data.get('records_processed', None)

                pipeline = DataPipeline.objects.get(id=pipeline_id)

                if stage_name:
                    # Update specific stage
                    stage = PipelineStage.objects.get(
                        pipeline_id=pipeline_id, name=stage_name)
                    stage.status = status
                    if error_message:
                        stage.error_message = error_message
                    stage.save()

                    # Check if all stages are complete to update pipeline status
                    if status == "completed":
                        all_stages_completed = all(
                            s.status == "completed" for s in pipeline.stages.all())
                        if all_stages_completed:
                            pipeline.status = "completed"
                    elif status == "failed":
                        pipeline.status = "failed"
                        pipeline.error_message = error_message
                else:
                    # Update entire pipeline
                    pipeline.status = status
                    if error_message:
                        pipeline.error_message = error_message
                    if records_processed:
                        pipeline.records_processed = records_processed

                pipeline.save()
                return JsonResponse({"success": True})

            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)})

        return JsonResponse({"success": False, "error": "Invalid request method"})


class DataPipelineViewSet(viewsets.ModelViewSet):
    """API viewset for DataPipeline"""
    queryset = DataPipeline.objects.all()
    serializer_class = DataPipelineSerializer

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """Trigger a specific pipeline"""
        pipeline = self.get_object()
        # Logic to trigger pipeline
        return Response({'status': 'pipeline triggered'})


class PipelineStageViewSet(viewsets.ModelViewSet):
    """API viewset for PipelineStage"""
    queryset = PipelineStage.objects.all()
    serializer_class = PipelineStageSerializer


async def trigger_prefect_flow(pipeline_id):
    """Trigger a Prefect flow run"""
    try:
        # This would normally use Prefect's API to trigger flows
        # But for local development, we'll call the flow directly
        await run_data_pipeline_flow(pipeline_id=pipeline_id)
        return True
    except Exception as e:
        print(f"Error triggering Prefect flow: {str(e)}")
        return False
