from fastapi import APIRouter
from app.services import vector_db

router = APIRouter()

@router.post("/vector-test")
def vector_test():
    vector_db.insert_document(
        doc_id="doc1",
        content="Le marché public concerne la rénovation d’un bâtiment.",
        metadata={"type": "test"}  # 👈 toujours un champ
    )

    result = vector_db.query_similar("travaux de rénovation")
    return result

