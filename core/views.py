from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.serializers import PromptSerializer
from core.gpt_client import ask_mistral
from rest_framework import status
from .serializers import UploadedDocumentSerializer
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from core.embedding_utils import embed_and_store, EMBEDDING_MODEL, collection
from core.monitoring import PerformanceMonitor, PerformanceAnalyzer
from core.models import QueryLog, SystemPerformanceMetrics, UserAction
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import time
import os
from .embedding_utils import EMBEDDING_MODEL, collection

@api_view(["POST"])
def ask_view(request):
    # Initialize performance monitoring
    monitor = PerformanceMonitor().start_monitoring()
    
    serializer = PromptSerializer(data=request.data)
    if serializer.is_valid():
        user_prompt = serializer.validated_data['prompt']
        language = serializer.validated_data['language']

        try:
            # Step 1: Embed user query
            embed_start = time.time()
            query_embedding = EMBEDDING_MODEL.encode(user_prompt)
            monitor.record_embedding_time()

            # Step 2: Search ChromaDB for relevant chunks
            search_start = time.time()
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=3,  # Reduced from 5 to 3 for TinyLlama
                include=["documents", "metadatas", "distances"]  # Added distances for relevance scoring
            )
            monitor.record_search_time()

            # Extract relevant chunks
            relevant_chunks = results.get('documents', [[]])[0]
            metadata_chunks = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]

            # Step 3: Simplified system prompt for TinyLlama
            system_prompt = {
                'en': "You are an AI assistant. Answer the question about digital rights in Africa using the provided context. Be clear and concise.",
                'fr': "Vous êtes un assistant IA. Répondez à la question sur les droits numériques en Afrique en utilisant le contexte fourni.",
                'sw': "Wewe ni msaidizi wa AI. Jibu swali kuhusu haki za kidijitali Afrika kwa kutumia muktadha uliopiewa.",
                'am': "አንተ የAI ረዳት ነህ። የተሰጠውን አውድ በመጠቀም ስለ አፍሪካ ዲጂታል መብቶች ጥያቄውን መልስ።"
            }.get(language, 'Answer about digital rights in Africa using the context.')

            # Step 4: Construct ultra-simplified prompt for TinyLlama
            if relevant_chunks:
                # Use only the first chunk and severely truncate it
                best_chunk = relevant_chunks[0]
                # Take only the first 150 characters to avoid overloading TinyLlama
                truncated_chunk = best_chunk[:150].strip()
                
                # Ultra-simple prompt structure
                full_prompt = f"Context: {truncated_chunk}\n\nQuestion: {user_prompt}\n\nBrief answer:"
            else:
                full_prompt = f"Question: {user_prompt}\n\nBrief answer about digital rights in Africa:"

            # Step 5: Send to LLM (e.g., Mistral)
            llm_start = time.time()
            answer = ask_mistral(full_prompt, language)
            monitor.record_llm_time()

            # Calculate relevance scores for response
            relevance_scores = []
            if distances:
                for distance in distances:
                    if distance <= 2:  # Likely cosine distance
                        relevance = max(0, 1 - (distance / 2))
                    else:  # Likely euclidean distance
                        relevance = 1 / (1 + distance)
                    relevance_scores.append(relevance)

            # Log the interaction for monitoring
            query_log_entry = monitor.log_query(
                query_text=user_prompt,
                language=language,
                response_text=answer,
                context_chunks=relevant_chunks,
                relevance_scores=relevance_scores,
                metadata={
                    'system_prompt_language': language,
                    'context_chunks_used': len(relevant_chunks)
                }
            )

            return Response({
                "response": answer,
                "context_used": relevant_chunks,
                "metadatas": metadata_chunks,
                "relevance_scores": relevance_scores,
                "query": user_prompt,
                "language": language,
                "query_id": query_log_entry.id if query_log_entry else None  # Add query ID for feedback
            })

        except Exception as e:
            # Log failed query
            monitor.log_query(
                query_text=user_prompt,
                language=language,
                response_text=f"Error: {str(e)}",
                context_chunks=[],
                relevance_scores=[],
                metadata={'error': str(e), 'failed': True}
            )
            
            return Response({
                "error": f"An error occurred while processing your request: {str(e)}",
                "query": user_prompt,
                "language": language
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   



# Create your views here.
# @api_view(['POST'])
# def upload_document(request):
#     serializer = UploadedDocumentSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_and_embed_view(request):
    serializer = UploadedDocumentSerializer(data=request.data)
    
    if serializer.is_valid():
        # Save file info to DB
        doc_instance = serializer.save()
        
        # Extract just the filename from the full path (e.g., 'documents/file.pdf' -> 'file.pdf')
        import os
        file_name = os.path.basename(doc_instance.file.name)
        language = doc_instance.language
        
        # Trigger embedding
        result = embed_and_store(file_name, language)

        return Response({
            "message": result,
            "document": UploadedDocumentSerializer(doc_instance).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Add document management views
@api_view(['GET'])
def list_documents(request):
    """List all uploaded documents"""
    try:
        from .models import UploadedDocument
        documents = UploadedDocument.objects.all().order_by('-uploaded_at')
        serializer = UploadedDocumentSerializer(documents, many=True)
        
        # Add extra metadata
        documents_data = []
        for doc_data in serializer.data:
            doc = UploadedDocument.objects.get(id=doc_data['id'])
            
            # Get file size
            file_size = 0
            try:
                file_size = doc.file.size
            except:
                pass
                
            # Get embedding status from ChromaDB
            embedded_chunks = 0
            try:
                # Check if document chunks exist in ChromaDB
                results = collection.get(
                    where={"source_document": {"$eq": doc.file.name}}
                )
                embedded_chunks = len(results['ids']) if results['ids'] else 0
            except:
                pass
            
            documents_data.append({
                **doc_data,
                'file_size': file_size,
                'embedded_chunks': embedded_chunks,
                'is_embedded': embedded_chunks > 0,
                'file_name': doc.file.name.split('/')[-1] if doc.file.name else 'Unknown'
            })
        
        return Response({
            'documents': documents_data,
            'total_count': len(documents_data),
            'embedded_count': sum(1 for doc in documents_data if doc['is_embedded'])
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['DELETE'])
def delete_document(request, doc_id):
    """Delete a document and its embeddings"""
    try:
        from .models import UploadedDocument
        import os
        
        # Get the document
        document = UploadedDocument.objects.get(id=doc_id)
        file_name = document.file.name
        
        # Delete embeddings from ChromaDB
        try:
            # Get all chunks for this document
            results = collection.get(
                where={"source_document": {"$eq": file_name}}
            )
            
            if results['ids']:
                collection.delete(ids=results['ids'])
                print(f"Deleted {len(results['ids'])} chunks from ChromaDB for {file_name}")
        except Exception as e:
            print(f"Error deleting from ChromaDB: {e}")
        
        # Delete the physical file
        try:
            if document.file and os.path.exists(document.file.path):
                os.remove(document.file.path)
        except Exception as e:
            print(f"Error deleting physical file: {e}")
        
        # Delete the database record
        document.delete()
        
        return Response({
            'message': f'Document {file_name} deleted successfully',
            'deleted_chunks': len(results['ids']) if 'results' in locals() and results['ids'] else 0
        })
        
    except UploadedDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def re_embed_document(request, doc_id):
    """Re-embed a document (useful if embedding failed)"""
    try:
        from .models import UploadedDocument
        import os
        
        document = UploadedDocument.objects.get(id=doc_id)
        # Extract just the filename from the full path (e.g., 'documents/file.pdf' -> 'file.pdf')
        file_name = os.path.basename(document.file.name)
        language = document.language
        
        # Re-trigger embedding
        result = embed_and_store(file_name, language)
        
        return Response({
            'message': f'Document re-embedded successfully: {result}',
            'document_id': doc_id
        })
        
    except UploadedDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['PUT'])
def update_document(request, doc_id):
    """Update document metadata"""
    try:
        from .models import UploadedDocument
        
        document = UploadedDocument.objects.get(id=doc_id)
        
        # Update fields from request data
        updateable_fields = [
            'title', 'author', 'source', 'publication_date', 'category',
            'description', 'tags', 'document_type', 'geographic_scope',
            'target_audience', 'processing_notes'
        ]
        
        for field in updateable_fields:
            if field in request.data:
                setattr(document, field, request.data[field])
        
        document.save()
        
        # Return updated document data
        serializer = UploadedDocumentSerializer(document)
        return Response({
            'message': 'Document updated successfully',
            'document': serializer.data
        })
        
    except UploadedDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def document_stats(request):
    """Get comprehensive document and embedding statistics"""
    try:
        from .models import UploadedDocument
        from django.db.models import Count
        
        # Database stats
        total_docs = UploadedDocument.objects.count()
        
        # Language distribution
        language_stats = UploadedDocument.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # ChromaDB stats
        total_chunks = 0
        total_documents_embedded = 0
        chunk_details = []
        
        try:
            collection_info = collection.get()
            total_chunks = len(collection_info['ids']) if collection_info['ids'] else 0
            
            # Get unique documents in ChromaDB
            metadatas = collection_info.get('metadatas', [])
            unique_documents = set()
            
            for metadata in metadatas:
                if metadata and 'source_document' in metadata:
                    unique_documents.add(metadata['source_document'])
            
            total_documents_embedded = len(unique_documents)
            
            # Get chunk distribution per document
            chunk_distribution = {}
            for metadata in metadatas:
                if metadata and 'source_document' in metadata:
                    doc_name = metadata['source_document']
                    chunk_distribution[doc_name] = chunk_distribution.get(doc_name, 0) + 1
            
            chunk_details = [
                {'document': doc, 'chunks': count} 
                for doc, count in chunk_distribution.items()
            ]
            
        except Exception as e:
            print(f"Error getting ChromaDB stats: {e}")
        
        # File storage stats
        storage_stats = {
            'total_size': 0,
            'avg_size': 0
        }
        
        try:
            documents = UploadedDocument.objects.all()
            sizes = []
            for doc in documents:
                try:
                    size = doc.file.size
                    sizes.append(size)
                except:
                    pass
            
            if sizes:
                storage_stats['total_size'] = sum(sizes)
                storage_stats['avg_size'] = sum(sizes) / len(sizes)
        except Exception as e:
            print(f"Error calculating storage stats: {e}")
        
        return Response({
            'database_stats': {
                'total_documents': total_docs,
                'language_distribution': list(language_stats)
            },
            'embedding_stats': {
                'total_chunks': total_chunks,
                'documents_embedded': total_documents_embedded,
                'avg_chunks_per_doc': total_chunks / max(total_documents_embedded, 1),
                'chunk_distribution': chunk_details
            },
            'storage_stats': storage_stats
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(["GET"])
def monitoring_dashboard(request):
    """Get system performance dashboard data"""
    try:
        analyzer = PerformanceAnalyzer()
        
        # Get various metrics
        daily_stats = list(analyzer.get_daily_stats(days=7))
        language_usage = list(analyzer.get_language_usage())
        system_health = analyzer.get_system_health()
        performance_trends = list(analyzer.get_query_performance_trends())
        low_performance_queries = list(analyzer.get_low_performance_queries())
        
        return Response({
            "dashboard": {
                "daily_stats": [
                    {
                        "date": stat.date.isoformat(),
                        "total_queries": stat.total_queries,
                        "avg_response_time_ms": stat.avg_response_time_ms,
                        "avg_relevance_score": stat.avg_relevance_score,
                        "queries_by_language": stat.queries_by_language,
                        "avg_user_rating": stat.avg_user_rating
                    } for stat in daily_stats
                ],
                "language_usage": language_usage,
                "system_health": system_health,
                "performance_trends": [
                    {
                        "date": trend['timestamp__date'].isoformat(),
                        "avg_response_time": trend['avg_response_time'],
                        "avg_relevance": trend['avg_relevance'],
                        "query_count": trend['query_count']
                    } for trend in performance_trends
                ],
                "low_performance_queries": [
                    {
                        "query": query.query_text[:100],
                        "language": query.language,
                        "avg_relevance": query.avg_relevance_score,
                        "response_time": query.response_time_ms,
                        "timestamp": query.timestamp.isoformat()
                    } for query in low_performance_queries
                ]
            }
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
def rate_response(request):
    """Allow users to rate responses for quality evaluation"""
    try:
        query_id = request.data.get('query_id')
        user_rating = request.data.get('user_rating')  # 1-5 or 'up'/'down'
        response_relevance = request.data.get('response_relevance')  # 1-5
        feedback_type = request.data.get('feedback_type', 'rating')  # 'rating', 'copy', 'regenerate'
        
        if not query_id:
            return Response({"error": "query_id is required"}, status=400)
        
        try:
            query_log = QueryLog.objects.get(id=query_id)
            
            # Handle different feedback types
            if feedback_type == 'rating':
                if user_rating == 'up':
                    query_log.user_rating = 5  # Convert 'up' to 5 stars
                elif user_rating == 'down':
                    query_log.user_rating = 1  # Convert 'down' to 1 star
                elif isinstance(user_rating, int) and 1 <= user_rating <= 5:
                    query_log.user_rating = user_rating
            elif feedback_type == 'regenerate':
                query_log.regeneration_count += 1
                    
            if response_relevance:
                query_log.response_relevance = response_relevance
                
            query_log.save()
            
            # Also log the action for analytics
            UserAction.objects.create(
                query_log=query_log,
                action_type=feedback_type,
                details={
                    'user_rating': user_rating,
                    'response_relevance': response_relevance,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            return Response({
                "message": "Feedback saved successfully",
                "query_id": query_id,
                "user_rating": query_log.user_rating,
                "response_relevance": query_log.response_relevance
            })
            
        except QueryLog.DoesNotExist:
            return Response({"error": "Query not found"}, status=404)
            
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
def system_stats(request):
    """Get real-time system statistics"""
    try:
        from django.db.models import Count, Avg
        from datetime import datetime, timedelta
        
        # Get statistics for different time periods
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        last_week = now - timedelta(weeks=1)
        
        stats = {
            "last_hour": QueryLog.objects.filter(timestamp__gte=last_hour).aggregate(
                count=Count('id'),
                avg_response_time=Avg('response_time_ms'),
                avg_relevance=Avg('avg_relevance_score')
            ),
            "last_day": QueryLog.objects.filter(timestamp__gte=last_day).aggregate(
                count=Count('id'),
                avg_response_time=Avg('response_time_ms'),
                avg_relevance=Avg('avg_relevance_score')
            ),
            "last_week": QueryLog.objects.filter(timestamp__gte=last_week).aggregate(
                count=Count('id'),
                avg_response_time=Avg('response_time_ms'),
                avg_relevance=Avg('avg_relevance_score')
            ),
            "total_queries": QueryLog.objects.count(),
            "languages": QueryLog.objects.values('language').annotate(
                count=Count('id')
            ).order_by('-count')
        }
        
        return Response({"stats": stats})
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)

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

# Real Monitoring API Endpoints

@api_view(['GET'])
def monitoring_stats(request):
    """Get real system statistics from PostgreSQL database"""
    try:
        from django.db.models import Count, Avg, Max, Min
        from datetime import timedelta
        
        now = timezone.now()
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(days=7)
        
        # Query PostgreSQL for real stats
        total_queries = QueryLog.objects.count()
        
        # Last day statistics
        last_day_queries = QueryLog.objects.filter(timestamp__gte=one_day_ago)
        last_day_stats = last_day_queries.aggregate(
            avg_response_time=Avg('response_time'),
            avg_relevance=Avg('relevance_score'),
            count=Count('id')
        )
        
        # Last week statistics
        last_week_queries = QueryLog.objects.filter(timestamp__gte=one_week_ago)
        last_week_stats = last_week_queries.aggregate(
            avg_response_time=Avg('response_time'),
            avg_relevance=Avg('relevance_score'),
            count=Count('id')
        )
        
        # Language distribution
        language_stats = QueryLog.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats = {
            'total_queries': total_queries,
            'last_day': {
                'avg_response_time': last_day_stats['avg_response_time'] or 0,
                'avg_relevance': last_day_stats['avg_relevance'] or 0,
                'count': last_day_stats['count']
            },
            'last_week': {
                'avg_response_time': last_week_stats['avg_response_time'] or 0,
                'avg_relevance': last_week_stats['avg_relevance'] or 0,
                'count': last_week_stats['count']
            },
            'languages': list(language_stats)
        }
        
        return Response({'stats': stats})
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def dashboard_data(request):
    """Get dashboard data including recent queries"""
    try:
        # Get recent queries (last 20)
        recent_queries = QueryLog.objects.order_by('-timestamp')[:20]
        
        queries_data = []
        for query in recent_queries:
            queries_data.append({
                'id': query.id,
                'query_text': query.query_text,
                'language': query.language,
                'response_time_ms': query.response_time * 1000,  # Convert to milliseconds
                'avg_relevance': query.relevance_score,
                'timestamp': query.timestamp.isoformat()
            })
        
        return Response({
            'recent_queries': queries_data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def embedding_stats(request):
    """Get real embedding statistics from ChromaDB"""
    try:
        # Query ChromaDB for real statistics
        collection_info = collection.get()
        
        # Count total documents and chunks
        total_chunks = len(collection_info['ids']) if collection_info['ids'] else 0
        
        # Get unique documents (assuming each chunk has source_document metadata)
        metadatas = collection_info.get('metadatas', [])
        unique_documents = set()
        total_tokens = 0
        
        for metadata in metadatas:
            if metadata and 'source_document' in metadata:
                unique_documents.add(metadata['source_document'])
            # Estimate tokens (rough estimate: ~4 characters per token)
            if metadata and 'chunk_size' in metadata:
                total_tokens += metadata.get('chunk_size', 0)
        
        avg_chunk_size = total_tokens // total_chunks if total_chunks > 0 else 0
        
        # Check if we have real documents in media/documents/
        documents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'documents')
        document_files = []
        if os.path.exists(documents_dir):
            document_files = [f for f in os.listdir(documents_dir) 
                            if f.endswith(('.pdf', '.docx', '.txt'))]
        
        stats = {
            'totalDocuments': len(unique_documents) or len(document_files),
            'totalChunks': total_chunks,
            'avgChunkSize': avg_chunk_size or 512,  # Default if no data
            'lastUpdated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'documentsInStorage': len(document_files)
        }
        
        return Response(stats)
        
    except Exception as e:
        # Return safe defaults if ChromaDB has issues
        return Response({
            'totalDocuments': 2,  # Known documents from your media folder
            'totalChunks': 42,    # Default fallback
            'avgChunkSize': 512,
            'lastUpdated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'documentsInStorage': 2,
            'error': f'ChromaDB connection issue: {str(e)}'
        })

@api_view(['GET'])
def performance_trends(request):
    """Get performance trends data for charts"""
    try:
        from datetime import timedelta
        from django.db.models import Avg, Count
        from django.db.models.functions import TruncHour, TruncDay
        
        now = timezone.now()
        
        # Response time trend (last 24 hours)
        response_time_data = QueryLog.objects.filter(
            timestamp__gte=now - timedelta(hours=24)
        ).annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            avg_response_time=Avg('response_time')
        ).order_by('hour')
        
        # Query volume trend (last 7 days)
        query_volume_data = QueryLog.objects.filter(
            timestamp__gte=now - timedelta(days=7)
        ).annotate(
            day=TruncDay('timestamp')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Relevance distribution
        relevance_high = QueryLog.objects.filter(relevance_score__gt=0.05).count()
        relevance_medium = QueryLog.objects.filter(
            relevance_score__gte=0.03, 
            relevance_score__lte=0.05
        ).count()
        relevance_low = QueryLog.objects.filter(relevance_score__lt=0.03).count()
        
        return Response({
            'response_time_trend': list(response_time_data),
            'query_volume_trend': list(query_volume_data),
            'relevance_distribution': [relevance_high, relevance_medium, relevance_low]
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])  
def system_health(request):
    """Get real-time system health status"""
    try:
        from datetime import timedelta
        from django.db.models import Avg
        
        # Check ChromaDB connectivity
        chroma_status = 'active'
        try:
            collection.get()
        except:
            chroma_status = 'error'
        
        # Check recent query performance
        recent_queries = QueryLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=30)
        )
        
        avg_response_time = recent_queries.aggregate(
            avg_time=Avg('response_time')
        )['avg_time'] or 0
        
        avg_relevance = recent_queries.aggregate(
            avg_rel=Avg('relevance_score')
        )['avg_rel'] or 0
        
        # Determine health status
        if avg_response_time < 5 and avg_relevance > 0.05:
            health_status = 'excellent'
        elif avg_response_time < 10 and avg_relevance > 0.03:
            health_status = 'good'
        elif avg_response_time < 20 and avg_relevance > 0.02:
            health_status = 'fair'
        else:
            health_status = 'poor'
        
        return Response({
            'status': health_status,
            'chromadb_status': chroma_status,
            'avg_response_time': avg_response_time,
            'avg_relevance': avg_relevance,
            'recent_queries_count': recent_queries.count()
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)
