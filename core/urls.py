# core/urls.py
from django.urls import path
from core.views_simple import (
    monitoring_stats, dashboard_data, 
    embedding_stats, performance_trends, system_health,
    dashboard_main_view, chat_view, documents_view, settings_view
)
from core.views import (
    ask_view, upload_and_embed_view, monitoring_dashboard, rate_response, 
    system_stats, list_documents, delete_document, re_embed_document, document_stats, update_document
)

urlpatterns = [
    path('ask/', ask_view, name='ask'),
    path('embed/', upload_and_embed_view, name='embed'),
    
    # Main dashboard route
    path('dashboard/', dashboard_main_view, name='dashboard_main'),
    path('', dashboard_main_view, name='dashboard_home'),  # Also serve dashboard at root
    path('chat/', chat_view, name='chat_view'),
    path('documents/', documents_view, name='documents_view'),
    path('settings/', settings_view, name='settings_view'),
    
    # Legacy monitoring endpoints
    path('monitoring/dashboard/', monitoring_dashboard, name='monitoring_dashboard_legacy'),
    path('monitoring/rate/', rate_response, name='rate_response'),
    path('monitoring/stats/', system_stats, name='system_stats_legacy'),
    
    # Document Management API Endpoints
    path('api/documents/', list_documents, name='list_documents'),
    path('api/documents/<int:doc_id>/delete/', delete_document, name='delete_document'),
    path('api/documents/<int:doc_id>/update/', update_document, name='update_document'),
    path('api/documents/<int:doc_id>/re-embed/', re_embed_document, name='re_embed_document'),
    path('api/documents/stats/', document_stats, name='document_stats'),
    
    # New Real Data API Endpoints
    path('api/monitoring/stats/', monitoring_stats, name='monitoring_stats_real'),
    path('api/monitoring/dashboard/', dashboard_data, name='dashboard_data_real'),
    path('api/monitoring/embeddings/', embedding_stats, name='embedding_stats'),
    path('api/monitoring/trends/', performance_trends, name='performance_trends'),
    path('api/monitoring/health/', system_health, name='system_health'),
]
