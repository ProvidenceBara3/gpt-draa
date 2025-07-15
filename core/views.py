from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.serializers import PromptSerializer
from core.gpt_client import ask_mistral
from rest_framework import status
from .serializers import UploadedDocumentSerializer
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from core.embedding_utils import embed_and_store
from .embedding_utils import EMBEDDING_MODEL, collection
@api_view(["POST"])
def ask_view(request):
    serializer = PromptSerializer(data=request.data)
    if serializer.is_valid():
        user_prompt = serializer.validated_data['prompt']
        language = serializer.validated_data['language']

        # Step 1: Embed user question
        query_embedding = EMBEDDING_MODEL.encode(user_prompt)

        # Step 2: Search ChromaDB for relevant chunks
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3  # adjust as needed
        )
        relevant_chunks = results.get('documents', [[]])[0]  # fallback to empty list

        # Step 3: Prepare multilingual system prompt
        system_prompt = {
            'en': "You are an expert in African digital human rights. Use the context below to answer clearly in English.",
            'fr': "Vous êtes un expert des droits numériques en Afrique. Utilisez le contexte ci-dessous pour répondre en français.",
            'sw': "Wewe ni mtaalam wa haki za kidijitali Afrika. Tumia muktadha hapa chini kujibu kwa Kiswahili.",
            'am': "አንተ በአፍሪካ የዲጂታል መብቶች ባለሙያ ነህ። በአማርኛ መልስ ስጥ።"
        }.get(language, 'Answer in English.')

        # Step 4: Construct full prompt with retrieved context
        context = "\n\n".join(relevant_chunks) if relevant_chunks else "No documents found."
        full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser: {user_prompt}"

        # Step 5: Ask Mistral model
        answer = ask_mistral(full_prompt)

        return Response({
            "response": answer,
            "context_used": relevant_chunks
        })

    return Response(serializer.errors, status=400)

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
        
        # Build file path (MEDIA_ROOT/documents/filename)
        file_path = doc_instance.file.name
        language = doc_instance.language
        
        # Trigger embedding
        result = embed_and_store(file_path, language)

        return Response({
            "message": result,
            "document": UploadedDocumentSerializer(doc_instance).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
