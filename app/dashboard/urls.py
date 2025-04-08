from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRF router
router = DefaultRouter()
router.register(r'pipelines', views.DataPipelineViewSet)
router.register(r'stages', views.PipelineStageViewSet)

# URL patterns
urlpatterns = [
    # UI views
    path('', views.DashboardView.index, name='index'),
    path('pipeline/<int:pipeline_id>/',
         views.DashboardView.pipeline_detail, name='pipeline_detail'),
    path('pipeline/trigger/', views.DashboardView.trigger_pipeline,
         name='trigger_pipeline'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/update-status/', views.DashboardView.update_pipeline_status,
         name='update_pipeline_status'),
]
