import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(path="./chroma_db")  # ✅ Nouvelle API

collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

def insert_document(doc_id: str, content: str, metadata: dict = None):
    # 👇 On force à avoir un dictionnaire avec au moins 1 champ
    safe_metadata = metadata if metadata and len(metadata) > 0 else {"source": "unknown"}

    collection.add(
        ids=[doc_id],
        documents=[content],
        metadatas=[safe_metadata]
    )

    

def query_similar(query_text: str, top_k: int = 3):
    return collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
