from django.core.management.base import BaseCommand
from core.chroma_client import chroma_client  # ✅ Don't override this!
import os
import chromadb
from chromadb.config import Settings

chroma_client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    persist_directory="chroma_data"
))

class Command(BaseCommand):
    help = 'Displays all embedded chunks stored in ChromaDB'

    def handle(self, *args, **kwargs):
        collection = chroma_client.get_or_create_collection(name="legal_docs")
        results = collection.get(include=['documents', 'metadatas'])

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])

        if not documents:
            self.stdout.write(self.style.WARNING("No documents found in ChromaDB."))
            return

        for i, (text, metadata) in enumerate(zip(documents, metadatas)):
            doc_id = ids[i] if i < len(ids) else f"chunk_{i}"
            self.stdout.write(self.style.SUCCESS(f"\nID: {doc_id}"))
            self.stdout.write(f"Language: {metadata.get('language', 'N/A')}")
            self.stdout.write(f"Text Chunk (first 200 chars): {text[:200]}...")
            self.stdout.write("-" * 80)
