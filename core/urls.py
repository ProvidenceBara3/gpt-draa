# core/urls.py
from django.urls import path
from core.views_simple import (
    dashboard_view, monitoring_stats, dashboard_data, 
    embedding_stats, performance_trends, system_health
)
from core.views import (
    ask_view, upload_and_embed_view, monitoring_dashboard, rate_response, 
    system_stats
)

urlpatterns = [
    path('ask/', ask_view, name='ask'),
    path('embed/', upload_and_embed_view, name='embed'),
    
    # Dashboard view
    path('dashboard/', dashboard_view, name='dashboard_view'),
    
    # Legacy monitoring endpoints
    path('monitoring/dashboard/', monitoring_dashboard, name='monitoring_dashboard_legacy'),
    path('monitoring/rate/', rate_response, name='rate_response'),
    path('monitoring/stats/', system_stats, name='system_stats_legacy'),
    
    # New Real Data API Endpoints
    path('api/monitoring/stats/', monitoring_stats, name='monitoring_stats_real'),
    path('api/monitoring/dashboard/', dashboard_data, name='dashboard_data_real'),
    path('api/monitoring/embeddings/', embedding_stats, name='embedding_stats'),
    path('api/monitoring/trends/', performance_trends, name='performance_trends'),
    path('api/monitoring/health/', system_health, name='system_health'),
]
