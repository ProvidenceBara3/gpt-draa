from django.db import models
from django.utils import timezone
import json

class UploadedDocument(models.Model):
    # File Information
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, choices=[
        ('en', 'English'),
        ('fr', 'Français'),
        ('sw', 'Swahili'),
        ('am', 'Amharic')
    ])
    
    # Document Metadata
    title = models.CharField(max_length=300, blank=True, help_text="Document title")
    author = models.CharField(max_length=200, blank=True, help_text="Author or organization")
    source = models.CharField(max_length=200, blank=True, help_text="Source organization or publisher")
    publication_date = models.DateField(null=True, blank=True, help_text="Original publication date")
    
    # Categorization
    CATEGORY_CHOICES = [
        ('internet_freedom', 'Internet Freedom'),
        ('accessibility', 'Accessibility'),
        ('gender_violence', 'Technology Facilitated Gender-Based Violence'),
        ('digital_inclusion', 'Digital Inclusion'),
        ('policy_governance', 'Policy & Governance'),
        ('cybersecurity', 'Cybersecurity'),
        ('data_protection', 'Data Protection & Privacy'),
        ('digital_economy', 'Digital Economy'),
        ('education_literacy', 'Digital Education & Literacy'),
        ('infrastructure', 'Digital Infrastructure'),
        ('research_reports', 'Research & Reports'),
        ('legal_frameworks', 'Legal Frameworks'),
        ('other', 'Other')
    ]
    
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Document category"
    )
    
    # Additional Details
    description = models.TextField(blank=True, help_text="Brief description of the document content")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    document_type = models.CharField(max_length=50, choices=[
        ('report', 'Report'),
        ('policy', 'Policy Document'),
        ('research', 'Research Paper'),
        ('guideline', 'Guidelines'),
        ('case_study', 'Case Study'),
        ('presentation', 'Presentation'),
        ('manual', 'Manual/Handbook'),
        ('legislation', 'Legislation'),
        ('other', 'Other')
    ], default='other')
    
    # Geographic and Scope Information
    geographic_scope = models.CharField(max_length=100, blank=True, help_text="Geographic coverage (e.g., 'Kenya', 'East Africa', 'Global')")
    target_audience = models.CharField(max_length=200, blank=True, help_text="Intended audience")
    
    # Processing Status
    is_processed = models.BooleanField(default=False, help_text="Whether document has been embedded")
    processing_notes = models.TextField(blank=True, help_text="Notes about processing or any issues")
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['language']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return self.title or self.file.name
    
    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def get_category_display_name(self):
        """Get human-readable category name"""
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)

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
    regeneration_count = models.IntegerField(default=0)  # Track how many times response was regenerated
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['language']),
            models.Index(fields=['avg_relevance_score']),
        ]
    
    def __str__(self):
        return f"Query: {self.query_text[:50]}... at {self.timestamp}"

class UserAction(models.Model):
    """Track user interactions for analytics"""
    
    query_log = models.ForeignKey(QueryLog, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=[
        ('copy', 'Copy Message'),
        ('regenerate', 'Regenerate Response'),
        ('rating', 'Rate Response'),
        ('follow_up', 'Follow-up Question'),
    ])
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.action_type} on Query #{self.query_log.id}"

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
