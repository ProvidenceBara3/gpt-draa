# core/serializers.py
from rest_framework import serializers
from .models import UploadedDocument

class PromptSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    language = serializers.ChoiceField(choices=['en', 'fr', 'sw', 'am'], default='en')

class UploadedDocumentSerializer(serializers.ModelSerializer):
    tags_list = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedDocument
        fields = [
            'id', 'file', 'language', 'uploaded_at', 'title', 'author', 'source',
            'publication_date', 'category', 'category_display', 'description', 
            'tags', 'tags_list', 'document_type', 'geographic_scope', 'target_audience',
            'is_processed', 'processing_notes', 'file_size', 'file_name'
        ]
        read_only_fields = ['id', 'uploaded_at', 'is_processed']
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()
    
    def get_category_display(self, obj):
        return obj.get_category_display_name()
    
    def get_file_size(self, obj):
        try:
            return obj.file.size if obj.file else 0
        except:
            return 0
    
    def get_file_name(self, obj):
        try:
            return obj.file.name.split('/')[-1] if obj.file else 'Unknown'
        except:
            return 'Unknown'