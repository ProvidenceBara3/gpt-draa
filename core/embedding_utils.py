import os
import fitz  # PyMuPDF
import docx
from sentence_transformers import SentenceTransformer
from core.chroma_client import chroma_client, collection

DOCUMENTS_PATH = 'media/documents/'
EMBEDDING_MODEL = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

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

    embedded_ids = []

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        doc_id = f"{file_name}_{i}"
        collection.add(
            documents=[chunk],
            embeddings=[emb.tolist()],
            ids=[doc_id],
            metadatas=[{
                "language": language_code,
                "source_document": file_name,
                "chunk_index": i,
                "chunk_size": len(chunk)
            }]
        )
        print(f"✅ Added chunk ID: {doc_id} (first 100 chars): {chunk[:100]}...")

        embedded_ids.append(doc_id)

    print("\n✅ Finished embedding. Summary:")
    print(f"📄 File: {file_name}")
    print(f"🧩 Total Chunks Embedded: {len(chunks)}")
    print(f"🗂️ Stored in Collection: legal_docs")
    print(f"📁 ChromaDB Path: {os.path.abspath('chroma_data')}")
    # PersistentClient auto-persists, no need to call persist()
    return f"✅ Embedded {len(chunks)} chunks from: {file_name}"

# Optional: debug what's already in the DB
def show_current_chunks():
    results = collection.get(include=["documents", "metadatas"])  # ✅ FIXED: removed "ids"
    ids = results.get("ids", [])  # ✅ Still accessible
    print(f"📊 Current Chunks in DB: {len(ids)}")
    
    for i, doc_id in enumerate(ids):
        preview = results["documents"][i][:100]
        lang = results["metadatas"][i].get("language", "unknown")
        print(f"🆔 {doc_id} | 🌍 {lang} | 📄 Preview: {preview}...")


