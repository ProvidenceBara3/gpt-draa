# core/monitoring.py
import time
from datetime import date, datetime
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone
from .models import QueryLog, SystemPerformanceMetrics
import json

class PerformanceMonitor:
    """Service class for monitoring and logging system performance"""
    
    def __init__(self):
        self.start_time = None
        self.embedding_time = None
        self.search_time = None
        self.llm_time = None
    
    def start_monitoring(self):
        """Start timing a request"""
        self.start_time = time.time()
        return self
    
    def record_embedding_time(self):
        """Record time taken for embedding generation"""
        if self.start_time:
            self.embedding_time = (time.time() - self.start_time) * 1000  # Convert to ms
    
    def record_search_time(self):
        """Record time taken for vector search"""
        if self.start_time:
            self.search_time = (time.time() - self.start_time) * 1000
    
    def record_llm_time(self):
        """Record time taken for LLM response"""
        if self.start_time:
            self.llm_time = (time.time() - self.start_time) * 1000
    
    def log_query(self, query_text, language, response_text, context_chunks, 
                  relevance_scores, metadata=None):
        """Log a complete query-response interaction"""
        
        if not self.start_time:
            return None
            
        response_time_ms = (time.time() - self.start_time) * 1000
        
        # Calculate relevance metrics
        avg_relevance = None
        max_relevance = None
        min_relevance = None
        
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            max_relevance = max(relevance_scores)
            min_relevance = min(relevance_scores)
        
        # Create log entry
        query_log = QueryLog.objects.create(
            query_text=query_text,
            language=language,
            response_text=response_text,
            response_time_ms=int(response_time_ms),
            context_chunks_found=len(context_chunks),
            avg_relevance_score=avg_relevance,
            max_relevance_score=max_relevance,
            min_relevance_score=min_relevance,
            embedding_time_ms=int(self.embedding_time) if self.embedding_time else None,
            search_time_ms=int(self.search_time) if self.search_time else None,
            llm_time_ms=int(self.llm_time) if self.llm_time else None,
            metadata={
                'relevance_scores': relevance_scores,
                'context_chunks_count': len(context_chunks),
                **(metadata or {})
            }
        )
        
        # Update daily metrics
        self.update_daily_metrics(query_log)
        
        return query_log
    
    def update_daily_metrics(self, query_log):
        """Update or create daily performance metrics"""
        today = date.today()
        
        metrics, created = SystemPerformanceMetrics.objects.get_or_create(
            date=today,
            defaults={
                'total_queries': 0,
                'successful_queries': 0,
                'queries_by_language': {}
            }
        )
        
        # Update metrics
        metrics.total_queries += 1
        metrics.successful_queries += 1
        
        # Update language distribution
        lang_dist = metrics.queries_by_language or {}
        lang_dist[query_log.language] = lang_dist.get(query_log.language, 0) + 1
        metrics.queries_by_language = lang_dist
        
        # Recalculate averages for today
        today_queries = QueryLog.objects.filter(timestamp__date=today)
        aggregates = today_queries.aggregate(
            avg_response_time=Avg('response_time_ms'),
            avg_relevance=Avg('avg_relevance_score'),
            avg_chunks=Avg('context_chunks_found'),
            avg_user_rating=Avg('user_rating'),
            avg_response_relevance=Avg('response_relevance')
        )
        
        metrics.avg_response_time_ms = aggregates['avg_response_time']
        metrics.avg_relevance_score = aggregates['avg_relevance']
        metrics.avg_context_chunks = aggregates['avg_chunks']
        metrics.avg_user_rating = aggregates['avg_user_rating']
        metrics.avg_response_relevance = aggregates['avg_response_relevance']
        
        metrics.save()

class PerformanceAnalyzer:
    """Service for analyzing system performance over time"""
    
    @staticmethod
    def get_daily_stats(days=7):
        """Get performance stats for the last N days"""
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        return SystemPerformanceMetrics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')
    
    @staticmethod
    def get_query_performance_trends():
        """Get query performance trends"""
        from datetime import timedelta
        
        last_7_days = date.today() - timedelta(days=7)
        
        return QueryLog.objects.filter(
            timestamp__date__gte=last_7_days
        ).values('timestamp__date').annotate(
            avg_response_time=Avg('response_time_ms'),
            avg_relevance=Avg('avg_relevance_score'),
            query_count=Count('id')
        ).order_by('timestamp__date')
    
    @staticmethod
    def get_language_usage():
        """Get language usage statistics"""
        return QueryLog.objects.values('language').annotate(
            count=Count('id'),
            avg_relevance=Avg('avg_relevance_score'),
            avg_response_time=Avg('response_time_ms')
        ).order_by('-count')
    
    @staticmethod
    def get_low_performance_queries(threshold=0.03):
        """Get queries with low relevance scores for analysis"""
        return QueryLog.objects.filter(
            avg_relevance_score__lt=threshold
        ).order_by('avg_relevance_score')[:20]
    
    @staticmethod
    def get_system_health():
        """Get overall system health metrics"""
        from datetime import timedelta
        
        last_24h = timezone.now() - timedelta(hours=24)
        last_7d = timezone.now() - timedelta(days=7)
        
        recent_queries = QueryLog.objects.filter(timestamp__gte=last_24h)
        weekly_queries = QueryLog.objects.filter(timestamp__gte=last_7d)
        
        return {
            'last_24h': {
                'total_queries': recent_queries.count(),
                'avg_response_time': recent_queries.aggregate(Avg('response_time_ms'))['response_time_ms__avg'],
                'avg_relevance': recent_queries.aggregate(Avg('avg_relevance_score'))['avg_relevance_score__avg'],
            },
            'last_7d': {
                'total_queries': weekly_queries.count(),
                'avg_response_time': weekly_queries.aggregate(Avg('response_time_ms'))['response_time_ms__avg'],
                'avg_relevance': weekly_queries.aggregate(Avg('avg_relevance_score'))['avg_relevance_score__avg'],
                'languages': weekly_queries.values('language').annotate(count=Count('id')),
            }
        }
