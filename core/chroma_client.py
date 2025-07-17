from chromadb import PersistentClient

chroma_client = PersistentClient(path="chroma_data")
collection = chroma_client.get_or_create_collection("legal_docs")
