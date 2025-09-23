from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.services.retriever import retrieve_top_chunks
from app.services.rag_engine import generate_answer

router = APIRouter()

# Schémas I/O

class QueryRequest(BaseModel):
    question: str
    document_id: str  

class QueryResponse(BaseModel):
    question: str
    answer: Dict[str, Any]
    sources: list[Dict[str, Any]]

# Endpoint

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(payload: QueryRequest):
    try:
        if not payload.document_id:
            raise HTTPException(status_code=400, detail="document_id requis")
        # 1) Récupération des chunks pertinents (une seule fois ici)
        chunks, metadatas, ids, params = retrieve_top_chunks(
            payload.question,
            target_doc_id=payload.document_id,
        )

        if not chunks:
            return QueryResponse(
                question=payload.question,
                answer={"reponse": "❌ Aucun extrait trouvé", "used_chunks": 0},
                sources=[]
            )

        # 2) Génération de la réponse via RAG sans re-récupérer
        answer = await generate_answer(
            payload.question,
            payload.document_id,
            chunks=chunks,
            metas=metadatas,
            ids=ids,
        )

        # 3) Préparation des sources
        sources = []
        for meta, cid in zip(metadatas, ids):
            sources.append({
                "id": cid,
                "filename": meta.get("filename", "inconnu"),
                "document_id": meta.get("document_id", "inconnu"),
                "chunk_index": meta.get("chunk_index"),
                "doc_type": meta.get("doc_type", "non précisé"),
            })

        return QueryResponse(
            question=payload.question,
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
