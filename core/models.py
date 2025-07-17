from django.db import models
from django.utils import timezone
import json

class UploadedDocument(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, choices=[
        ('en', 'English'),
        ('fr', 'Français'),
        ('sw', 'Swahili'),
        ('am', 'Amharic')
    ])

    def __str__(self):
        return self.file.name

class QueryLog(models.Model):
    """Log all user queries and system responses for performance monitoring"""
    
    # Query Information
    query_text = models.TextField()
    language = models.CharField(max_length=5, choices=[
        ('en', 'English'),
        ('fr', 'French'),
        ('sw', 'Swahili'),
        ('am', 'Amharic')
    ])
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Response Information
    response_text = models.TextField()
    response_time_ms = models.IntegerField()  # Response time in milliseconds
    
    # Context Retrieval Metrics
    context_chunks_found = models.IntegerField()
    avg_relevance_score = models.FloatField(null=True, blank=True)
    max_relevance_score = models.FloatField(null=True, blank=True)
    min_relevance_score = models.FloatField(null=True, blank=True)
    
    # System Performance
    embedding_time_ms = models.IntegerField(null=True, blank=True)
    search_time_ms = models.IntegerField(null=True, blank=True)
    llm_time_ms = models.IntegerField(null=True, blank=True)
    
    # Quality Metrics (can be updated later through evaluation)
    user_rating = models.IntegerField(null=True, blank=True, choices=[
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent')
    ])
    response_relevance = models.IntegerField(null=True, blank=True, choices=[
        (1, 'Not Relevant'),
        (2, 'Somewhat Relevant'),
        (3, 'Relevant'),
        (4, 'Very Relevant'),
        (5, 'Highly Relevant')
    ])
    
    # Additional Data
    metadata = models.JSONField(default=dict, blank=True)  # Store relevance scores, etc.
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['language']),
            models.Index(fields=['avg_relevance_score']),
        ]
    
    def __str__(self):
        return f"Query: {self.query_text[:50]}... at {self.timestamp}"

class SystemPerformanceMetrics(models.Model):
    """Daily aggregated system performance metrics"""
    
    date = models.DateField(unique=True)
    
    # Volume Metrics
    total_queries = models.IntegerField(default=0)
    successful_queries = models.IntegerField(default=0)
    failed_queries = models.IntegerField(default=0)
    
    # Performance Metrics
    avg_response_time_ms = models.FloatField(null=True, blank=True)
    avg_relevance_score = models.FloatField(null=True, blank=True)
    avg_context_chunks = models.FloatField(null=True, blank=True)
    
    # Language Distribution
    queries_by_language = models.JSONField(default=dict)
    
    # Quality Metrics
    avg_user_rating = models.FloatField(null=True, blank=True)
    avg_response_relevance = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date}: {self.total_queries} queries"
