from __future__ import annotations
from typing import List, Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool
from app.services.llm_service import query_ollama_sync
from app.services.retriever import retrieve_top_chunks
from app.services.chunker import tokenizer
import re

def clean_chunk(text: str, max_tokens: int = 300) -> str:
    """Nettoie et tronque un chunk avant injection."""
    # Suppression des espaces et retours multiples
    text = " ".join(text.split())

    # Tronquage à max_tokens tokens
    tokens = tokenizer.encode(text, add_special_tokens=False)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
        text = tokenizer.decode(tokens)

    return text.strip()

def make_context(chunks: List[str]) -> str:
    """Nettoie + concatène les chunks en un seul contexte texte."""
    cleaned = [clean_chunk(ch) for ch in chunks]
    # Séparateur visuel clair pour aider le LLM à distinguer les extraits
    return "\n\n---\n\n".join(cleaned)

async def generate_answer(
    question: str,
    document_id: Optional[str],
    *,
    chunks: Optional[List[str]] = None,
    metas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    # Utiliser les résultats déjà récupérés si fournis; sinon, appeler le retriever
    if chunks is None or metas is None or ids is None:
        chunks, metas, ids, _ = retrieve_top_chunks(
            question,
            target_doc_id=document_id,
        )

    # Contexte nettoyé et tronqué (ce que le LLM voit)
    context = make_context(chunks)

    qa_prompt = f"""
RÔLE: Assistant AO Risk.
Réponds STRICTEMENT avec le contenu ci-dessous.

CONTEXTE:
{context}

QUESTION:
{question}

Réponse:
""".strip()

    llm_text = await run_in_threadpool(query_ollama_sync, qa_prompt, task="qa")

    # Sélection de source 'evidence-based': choisir le chunk avec le plus d'overlap lexical
    source_obj: Dict[str, Any] = {}
    try:
        if chunks and metas:
            def tok(s: str) -> set[str]:
                return set(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", (s or "").lower()))

            ans_tokens = tok(llm_text if isinstance(llm_text, str) else str(llm_text))
            q_tokens = tok(question)
            best_i = 0
            best_score = -1.0
            for i, ch in enumerate(chunks):
                ct = tok(ch)
                # Overlap réponse + un petit poids sur la question
                overlap_ans = len(ans_tokens & ct)
                overlap_q = len(q_tokens & ct)
                score = overlap_ans + 0.5 * overlap_q
                if score > best_score:
                    best_score = score
                    best_i = i

            m = metas[best_i] if isinstance(metas[best_i], dict) else {}
            doc_type = (m.get("doc_type") if isinstance(m, dict) else None) or "Document"
            section = None
            if isinstance(m, dict):
                section = m.get("section_title") or m.get("article") or m.get("title")
            page = (m.get("page") if isinstance(m, dict) else None)
            doc_id_meta = (m.get("document_id") if isinstance(m, dict) else None)
            parts = [p for p in [doc_type, section, (f"p.{page}" if page else None)] if p]
            label = " > ".join(parts) if parts else None
            url = None
            if doc_id_meta:
                # Lien direct vers le PDF servi derrière le reverse proxy (/api)
                url = f"/api/files/{doc_id_meta}.pdf" + (f"#page={page}" if page else "")
            source_obj = {
                "label": label,
                "url": url,
                "document_id": doc_id_meta,
                "page": page,
            }
    except Exception:
        source_obj = {}

    return {
        "reponse": llm_text if isinstance(llm_text, str) else str(llm_text),
        "used_chunks": len(chunks),
        "source": source_obj,
    }
