import os
import fitz  # PyMuPDF
import docx
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

DOCUMENTS_PATH = 'media/documents/'
EMBEDDING_MODEL = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')



chroma_client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    persist_directory="chroma_data"  # or any consistent folder name
))

# chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
collection = chroma_client.get_or_create_collection(name="legal_docs")

def extract_text(file_path):
    if file_path.endswith('.pdf'):
        doc = fitz.open(file_path)
        return "\n".join([page.get_text() for page in doc])
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

def embed_and_store(file_name, language_code):
    file_path = os.path.join(DOCUMENTS_PATH, file_name)
    text = extract_text(file_path)

    if not text.strip():
        return f"❌ No text found in: {file_name}"

    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    embeddings = EMBEDDING_MODEL.encode(chunks)

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        collection.add(
            documents=[chunk],
            embeddings=[emb.tolist()],
            ids=[f"{file_name}_{i}"],
            metadatas=[{"language": language_code}]
        )
    return f"✅ Embedded {len(chunks)} chunks from: {file_name}"
