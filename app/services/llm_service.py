# app/services/llm_service.py
import httpx

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL_NAME  = "mistral"

async def appeler_llm(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    # ▶︎ 60 s de timeout (ou None si tu veux illimité)
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()["response"]
