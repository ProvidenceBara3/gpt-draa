# core/urls.py
from django.urls import path
from core.views import ask_view
from .views import ask_view,  upload_and_embed_view

urlpatterns = [
    path('ask/', ask_view, name='ask'),
    # path('upload/', upload_document),
    path('embed/', upload_and_embed_view, name='embed'),
]
