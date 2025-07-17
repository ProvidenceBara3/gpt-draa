from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from core.serializers import PromptSerializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from core.models import QueryLog, SystemPerformanceMetrics
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import time
import os
import random
from datetime import datetime, timedelta

def dashboard_view(request):
    """Serve the monitoring dashboard HTML page"""
    try:
        # Read the dashboard HTML file
        dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'dashboard.html')
        with open(dashboard_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return HttpResponse(html_content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse("""
        <html>
        <head><title>Dashboard Not Found</title></head>
        <body>
            <h1>Dashboard Not Found</h1>
            <p>The dashboard HTML file could not be found. Please ensure the dashboard.html file exists in the static directory.</p>
        </body>
        </html>
        """, content_type='text/html', status=404)

@api_view(["POST"])
def ask_view(request):
    """Simplified ask view for demo purposes"""
    serializer = PromptSerializer(data=request.data)
    if serializer.is_valid():
        user_prompt = serializer.validated_data['prompt']
        language = serializer.validated_data['language']

        # Mock response for demo
        mock_responses = [
            "Digital inclusion in Africa requires addressing infrastructure gaps, digital literacy, and accessibility for persons with disabilities.",
            "CIPESA promotes digital rights and inclusion across Africa through research, advocacy, and capacity building.",
            "Key challenges include connectivity, affordability, and ensuring technology serves all community members equally.",
            "Accessibility features must be built into digital platforms from the start to ensure inclusion for all users."
        ]
        
        mock_response = {
            'response': random.choice(mock_responses),
            'context_used': [
                {'text': 'Digital inclusion in Africa faces significant challenges including infrastructure limitations.'},
                {'text': 'Accessibility features for persons with disabilities require specialized attention.'},
                {'text': 'CIPESA works to promote digital rights and inclusion across the continent.'}
            ],
            'relevance_scores': [0.065, 0.058, 0.042],
            'language': language,
            'query': user_prompt
        }

        # Create mock query log
        QueryLog.objects.create(
            query_text=user_prompt,
            language=language,
            response_text=mock_response['response'],
            response_time_ms=random.randint(2000, 5000),
            context_chunks_found=3,
            avg_relevance_score=random.uniform(0.04, 0.08),
            timestamp=timezone.now()
        )

        return Response(mock_response, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def system_stats(request):
    """Get system statistics for monitoring"""
    try:
        # Get query statistics
        total_queries = QueryLog.objects.count()
        
        # Language distribution
        from django.db import models
        languages = QueryLog.objects.values('language').annotate(
            count=models.Count('language')
        ).order_by('-count')
        
        # Recent performance metrics
        last_day_queries = QueryLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=1)
        )
        
        if last_day_queries.exists():
            avg_response_time = last_day_queries.aggregate(
                avg=models.Avg('response_time_ms')
            )['avg']
            avg_relevance = last_day_queries.aggregate(
                avg=models.Avg('avg_relevance_score')
            )['avg']
        else:
            avg_response_time = 0
            avg_relevance = 0
        
        stats = {
            'total_queries': total_queries,
            'languages': list(languages),
            'last_day': {
                'avg_response_time': avg_response_time,
                'avg_relevance': avg_relevance,
                'total_queries': last_day_queries.count()
            }
        }
        
        return JsonResponse({'stats': stats})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def monitoring_dashboard(request):
    """Get dashboard data including recent queries"""
    try:
        # Get recent queries
        recent_queries = QueryLog.objects.order_by('-timestamp')[:10]
        
        query_data = []
        for query in recent_queries:
            query_data.append({
                'id': query.id,
                'query_text': query.query_text,
                'language': query.language,
                'response_time_ms': query.response_time_ms,
                'avg_relevance': float(query.avg_relevance_score) if query.avg_relevance_score else 0,
                'timestamp': query.timestamp.isoformat(),
                'context_chunks_used': query.context_chunks_found or 0
            })
        
        return JsonResponse({
            'recent_queries': query_data,
            'status': 'success'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def rate_response(request):
    """Rate a query response"""
    try:
        query_id = request.data.get('query_id')
        rating = request.data.get('rating')
        
        if not query_id or rating is None:
            return JsonResponse({'error': 'Missing query_id or rating'}, status=400)
        
        query = QueryLog.objects.get(id=query_id)
        query.user_rating = rating
        query.save()
        
        return JsonResponse({'status': 'success', 'message': 'Rating saved'})
        
    except QueryLog.DoesNotExist:
        return JsonResponse({'error': 'Query not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_embed_view(request):
    """Simplified upload view"""
    return JsonResponse({
        'message': 'Upload functionality temporarily disabled for demo',
        'status': 'success'
    })
