# app/routers/analyse.py

# app/routers/analyse.py

from fastapi import APIRouter, UploadFile, File
from app.schemas.analyse import AnalyseResponse
from app.services.parsers import parser_factory
from app.services.analyse_service import analyser_document_fichier

router = APIRouter(tags=["Analyse"])

@router.post(
    "/analyse",
    response_model=AnalyseResponse,
    summary="Analyser un fichier",
    description="Envoie un fichier (PDF, Word, texte…) à la LLM et reçoit un résumé + clauses critiques."
)
async def analyser_fichier(file: UploadFile = File(...)):
    # 1️⃣ on lit le fichier
    file_bytes = await file.read()

    # 2️⃣ on appelle le service avec le nom et le contenu
    return await analyser_document_fichier(file.filename, file_bytes)

