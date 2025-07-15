# core/management/commands/view_chunks.py

from django.core.management.base import BaseCommand
import chromadb
from chromadb.config import Settings

class Command(BaseCommand):
    help = 'Displays all embedded chunks stored in ChromaDB'

    def handle(self, *args, **kwargs):
        chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
        collection = chroma_client.get_or_create_collection(name="legal_docs")

        results = collection.get(include=['documents', 'metadatas'])

        if not results['documents']:
            self.stdout.write(self.style.WARNING("No documents found in ChromaDB."))
            return

        for i, (text, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
            doc_id = results["ids"][i]
            self.stdout.write(self.style.SUCCESS(f"\nID: {doc_id}"))
            self.stdout.write(f"Language: {metadata.get('language', 'N/A')}")
            self.stdout.write(f"Text Chunk (first 200 chars): {text[:200]}...")
            self.stdout.write("-" * 80)
