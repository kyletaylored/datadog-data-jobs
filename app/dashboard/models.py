from django.db import models


class DataPipeline(models.Model):
    """Model to track pipelines that have been run"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    input_file = models.CharField(max_length=255, null=True, blank=True)
    output_file = models.CharField(max_length=255, null=True, blank=True)
    prefect_flow_run_id = models.CharField(
        max_length=255, null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.status})"


class PipelineStage(models.Model):
    """Model to track individual stages of a pipeline"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    pipeline = models.ForeignKey(
        DataPipeline, related_name='stages', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.status})"
