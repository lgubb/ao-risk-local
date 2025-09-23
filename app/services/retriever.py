from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional
from app.services.embedder import embed_query
from app.services.vector_service import get_chroma_collection
from app.services.bm25_service import bm25_query  # ⚡ import BM25

collection = get_chroma_collection()

def adjust_retrieval_params(total_chunks: int) -> Tuple[int, int, float]:
    if total_chunks <= 30:
        return 8, 4, 0.29
    elif total_chunks <= 80:
        return 14, 5, 0.32
    else:
        return 17, 6, 0.36

def reciprocal_rank_fusion(vec_results, bm25_results, k: int = 60):
    """RRF fusion entre résultats vectoriels et BM25."""
    scores = {}
    # Vector part
    for rank, (doc, dist, meta, hid) in enumerate(vec_results, start=1):
        scores[hid] = scores.get(hid, 0) + 1 / (k + rank)
    # BM25 part
    for rank, r in enumerate(bm25_results, start=1):
        hid = r["id"]
        doc, meta = r["document"], r["metadata"]
        scores[hid] = scores.get(hid, 0) + 1 / (k + rank)
    # Fusion
    fused = []
    for hid, score in scores.items():
        # retrouver doc/meta depuis l’une des sources
        match_vec = next(((d, m) for (d, _, m, i) in vec_results if i == hid), None)
        if match_vec:
            fused.append((match_vec[0], score, match_vec[1], hid))
        else:
            match_bm25 = next((r for r in bm25_results if r["id"] == hid), None)
            if match_bm25:
                fused.append((match_bm25["document"], score, match_bm25["metadata"], hid))
    return sorted(fused, key=lambda x: x[1], reverse=True)

def retrieve_top_chunks(
    query: str,
    target_doc_id: Optional[str] = None,
    base_top_k: Optional[int] = None,
    min_keep: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
):
    # Ne jamais utiliser de fallback implicite: si aucun document_id fourni,
    # la recherche se fait sur l'ensemble de la collection (comportement explicite).
    # Pour éviter les mélanges, l'API peut exiger un document_id côté routeur.
    where_filter = {"document_id": target_doc_id} if target_doc_id else None

    # Compter chunks
    if target_doc_id:
        res = collection.get(where=where_filter)
        ids_field = res.get("ids", [])
        total_chunks = sum(len(sub) for sub in ids_field) if ids_field and isinstance(ids_field[0], list) else len(ids_field)
    else:
        total_chunks = collection.count()

    auto_base_top_k, auto_min_keep, auto_similarity_threshold = adjust_retrieval_params(total_chunks)
    base_top_k = base_top_k or auto_base_top_k
    min_keep = min_keep or auto_min_keep
    similarity_threshold = similarity_threshold or auto_similarity_threshold

    print(f"[RAG] Params → base_top_k={base_top_k}, min_keep={min_keep}, threshold={similarity_threshold}, where={where_filter}")

    # 1) Vector search
    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=base_top_k,
        where=where_filter
    )
    docs_vec = results["documents"][0]
    dists_vec = results["distances"][0]
    metas_vec = results["metadatas"][0]
    ids_vec = results["ids"][0]
    ranked_vec = sorted(zip(docs_vec, dists_vec, metas_vec, ids_vec), key=lambda x: x[1])

    # 2) BM25 search
    bm25_results = bm25_query(query, top_k=base_top_k)
    # Filtrer BM25 sur le document ciblé si défini
    if target_doc_id:
        bm25_results = [
            r for r in bm25_results
            if r.get("metadata", {}).get("document_id") == target_doc_id
        ]

    # 3) Fusion RRF
    fused = reciprocal_rank_fusion(ranked_vec, bm25_results)

    # 4) Prendre top N limité
    MAX_CHUNKS = 10  # ⚡ plafond dur
    top_slice = fused[:min(MAX_CHUNKS, max(min_keep, len(fused)))]

    top_chunks = [doc for (doc, _, _, _) in top_slice]
    top_metadatas = [meta for (_, _, meta, _) in top_slice]
    top_ids = [hid for (_, _, _, hid) in top_slice]

    return top_chunks, top_metadatas, top_ids, {
        "base_top_k": base_top_k,
        "min_keep": min_keep,
        "similarity_threshold": similarity_threshold,
        "hybrid": True,
    }
