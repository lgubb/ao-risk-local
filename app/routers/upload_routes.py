from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from typing import List
from app.services.auth import get_user_if_required
from app.services.parsers import extract_text_from_file
from app.services.classifier import classify_piece
from app.services.vector_service import index_document_in_chroma
import uuid
import os
import json

router = APIRouter()

@router.post("/upload-index", dependencies=[Depends(get_user_if_required)])
async def upload_and_index(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Fichier non PDF.")

        # 🔹 Générer un ID unique
        document_id = str(uuid.uuid4())

        # 1️⃣ Extraction texte et pages
        extracted = extract_text_from_file(file)
        full_text = extracted["full_text"]
        pages_data = extracted["pages"]

        # Sauvegarder texte brut
        os.makedirs("storage", exist_ok=True)
        with open(f"storage/{document_id}.txt", "w", encoding="utf-8") as f:
            f.write(full_text)

        # Sauvegarder pages
        with open(f"storage/{document_id}_pages.json", "w", encoding="utf-8") as f:
            json.dump(pages_data, f, ensure_ascii=False, indent=2)

        # Sauvegarder le PDF original pour l'affichage (#page=)
        try:
            file.file.seek(0)
            with open(f"storage/{document_id}.pdf", "wb") as out:
                out.write(file.file.read())
        except Exception as e:
            print(f"[UPLOAD][WARN] Impossible de sauvegarder le PDF original: {e}")

        # 2️⃣ Classification
        doc_type = classify_piece(full_text)

        # 3️⃣ Indexation dans ChromaDB (avec doc_type et retour chunks)
        chunk_count = index_document_in_chroma(document_id, full_text, doc_type, file.filename, pages=pages_data)

        # 4️⃣ Ajouter au résultat
        results.append({
            "filename": file.filename,
            "document_id": document_id,
            "type": doc_type,
            "chunks": chunk_count,  
            "indexed": True
        })

    return {"status": "success", "results": results}
