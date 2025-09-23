from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import chromadb

from app.services.chunker import chunk_text
from app.services.embedder import generate_embeddings
from app.services.bm25_service import bm25_add


# Connexion Chroma unique
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    "ao-risk",
    metadata={"hnsw:space": "cosine"},
)

def get_chroma_collection():
    """Expose la collection Chroma partagée."""
    return collection

def _sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = json.dumps(v, ensure_ascii=False)
    return clean

def index_document_in_chroma(
    document_id: str,
    content: str,
    doc_type: Optional[str] = None,
    filename: Optional[str] = None,
    pages: Optional[list[dict]] = None,
) -> int:
    # 1) Chunking
    chunks: List[str] = chunk_text(content)
    chunk_count = len(chunks)
    print(f"[INDEX] document_id={document_id} | chunks={chunk_count}")
    if chunk_count == 0:
        return 0

    # 2) Embeddings
    embeddings: List[List[float]] = generate_embeddings(chunks)
    if len(embeddings) != chunk_count:
        raise RuntimeError("Embeddings count != chunks count")

    # 3) Métadonnées
    created_at = datetime.utcnow().isoformat()
    base_meta: Dict[str, Any] = {
        "indexer": "vector_service",
        "document_id": document_id,
        "filename": filename,
        "doc_type": (doc_type or "unknown"),
        "created_at": created_at,
    }

    # Helpers pour page et titre de section
    def _normalize(s: str) -> str:
        return " ".join((s or "").lower().split())

    page_lookup: list[tuple[int, str]] = []
    if pages:
        for p in pages:
            try:
                page_lookup.append((int(p.get("page")), _normalize(p.get("text", ""))))
            except Exception:
                continue

    def _guess_page_for_chunk(ch: str) -> Optional[int]:
        if not page_lookup:
            return None
        probe = _normalize(ch[:200])
        for num, text_norm in page_lookup:
            if probe and probe in text_norm:
                return num
        # fallback: cherche des mots rares du début
        words = [w for w in probe.split() if len(w) > 4][:6]
        if not words:
            return None
        for num, text_norm in page_lookup:
            hits = sum(1 for w in words if w in text_norm)
            if hits >= max(2, len(words)//2):
                return num
        return None

    def _extract_section_title(ch: str) -> Optional[str]:
        head = ch.strip().splitlines()[0] if ch.strip() else ""
        head = head.strip()
        if not head:
            return None
        return head[:140]

    ids: List[str] = [f"{document_id}_{i}" for i in range(chunk_count)]
    metadatas: List[Dict[str, Any]] = []
    for i, ch in enumerate(chunks):
        meta = {
            **base_meta,
            "chunk_index": i,
            "page": _guess_page_for_chunk(ch),
            "section_title": _extract_section_title(ch),
            "char_start": None,
            "char_end": None,
            "token_start": None,
            "token_end": None,
        }
        metadatas.append(_sanitize_metadata(meta))

    # 4) Insertion batch (Dense)
    BATCH = 64
    total = 0
    for start in range(0, chunk_count, BATCH):
        end = min(start + BATCH, chunk_count)
        batch_docs = chunks[start:end]
        batch_embs = embeddings[start:end]
        batch_meta = metadatas[start:end]
        batch_ids = ids[start:end]

        print(f"[INDEX] add batch {start}:{end} size={end-start}")
        collection.add(
            documents=batch_docs,
            embeddings=batch_embs,
            metadatas=batch_meta,
            ids=batch_ids,
        )

        total += (end - start)

    print(f"[INDEX] OK document_id={document_id} | added={total}")

    # 5) Index BM25
    try:
        bm25_add(ids, chunks, metadatas)
        print(f"[INDEX] BM25 OK document_id={document_id} | added={total}")
    except Exception as e:
        print(f"[INDEX][BM25 ERROR] {e}")

    return total
