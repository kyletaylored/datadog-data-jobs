from rest_framework import serializers
from .models import DataPipeline, PipelineStage


class PipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = '__all__'


class DataPipelineSerializer(serializers.ModelSerializer):
    stages = PipelineStageSerializer(many=True, read_only=True)

    class Meta:
        model = DataPipeline
        fields = '__all__'
