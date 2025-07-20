# app/services/analyse_service.py

from app.services.llm_service import appeler_llm
from app.services.parsers import parser_factory

async def analyser_document_fichier(filename: str, file_bytes: bytes) -> dict:
    """
    Détecte le format, extrait le texte puis envoie au LLM.
    """
    # 1️⃣ Extraction
    parser = parser_factory(filename)
    contenu = parser.extract(file_bytes)

    # 2️⃣ Prompt LLM
    prompt = f"""
    Tu es un assistant expert en analyse de documents administratifs.
    Voici le contenu à analyser :

    \"\"\"{contenu}\"\"\"

    Donne un résumé en 5 points des éléments importants du document.
    """
    response = await appeler_llm(prompt)

    # 3️⃣ Résultat brut
    return {
        "message": "Analyse terminée",
        "clauses_detectees": [response.strip()]  # TODO : parser proprement
    }
