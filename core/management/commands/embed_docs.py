from django.core.management.base import BaseCommand
from core.embedding_utils import embed_and_store, collection
import os

class Command(BaseCommand):
    help = 'Embed documents into ChromaDB'

    def handle(self, *args, **options):
        self.stdout.write(f"Current collection count: {collection.count()}")
        
        documents_path = 'media/documents/'
        
        # List available documents
        if os.path.exists(documents_path):
            files = os.listdir(documents_path)
            self.stdout.write(f"Found files: {files}")
            
            for file in files:
                if file.endswith(('.pdf', '.docx')):
                    self.stdout.write(f"Embedding: {file}")
                    try:
                        result = embed_and_store(file, 'en')
                        self.stdout.write(f"Result: {result}")
                    except Exception as e:
                        self.stdout.write(f"Error embedding {file}: {e}")
        
        self.stdout.write(f"Final collection count: {collection.count()}")
        self.stdout.write(self.style.SUCCESS('Document embedding completed!'))
