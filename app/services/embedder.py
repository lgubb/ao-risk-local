from sentence_transformers import SentenceTransformer
from typing import List

# On charge UNE SEULE fois le modèle
model = SentenceTransformer("dangvantuan/sentence-camembert-large")

def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    """Génère les embeddings pour une liste de chunks."""
    return model.encode(
        chunks,
        batch_size=8
    ).tolist()

def embed_query(query: str) -> List[float]:
    """Embeddings pour une query (retriever)."""
    return model.encode([query])[0].tolist()
