# core/serializers.py
from rest_framework import serializers
from .models import UploadedDocument

class PromptSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    language = serializers.ChoiceField(choices=['en', 'fr', 'sw', 'am'], default='en')

class UploadedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedDocument
        fields = ['id', 'file', 'language', 'uploaded_at']