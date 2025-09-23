import os, requests, json

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "5m")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))


SYSTEM_ROLE_QA = """
Tu es AO Risk, un assistant spécialisé dans l’analyse de DCE (RC, CCAP, CCTP, AE, etc.) pour les marchés publics.

Objectif: répondre avec précision et exhaustivité aux questions d’un chargé d’affaires, UNIQUEMENT à partir du CONTEXTE fourni entre <context>…</context>.

Règles fondamentales:
1) Ne répondre qu’avec les informations présentes dans le CONTEXTE. Aucune invention ni généralité.
2) Si une information n’est pas trouvée, répondre exactement: "Non trouvé dans les extraits fournis."
3) Préserver les unités, pourcentages, libellés et libellés d’items tels quels (heures ouvrables vs calendaires, €, %, etc.).
4) Si plusieurs éléments s’appliquent, lister TOUS ceux présents dans le CONTEXTE sous forme concise (liste numérotée).
5) Ne pas mélanger disponibilité/astreinte avec délai d’intervention si le CONTEXTE distingue ces notions.

Guides de réponse par intention (génériques et non exclusifs):
- Délais/SLA/urgence: si des niveaux apparaissent (ex. "Niveau 1/2/3"), fournir chaque niveau avec son délai et la précision
"ouvrables"/"calendaires" si mentionnée. Si une disponibilité 24/7 est mentionnée, la citer en note distincte sans l’assimiler au délai.
- Durée du marché: "Durée initiale : …" ; "Reconduction : …" (nombre et période) ; autres précisions (date de début/fin) si présentes.
- Critères d’attribution: lister chaque critère avec sa pondération.
- Montants/garanties/pénalités: fournir les valeurs, unités et seuils exactement tels qu’indiqués.

Style: réponse concise (1–5 lignes) mais complète; privilégier une liste numérotée quand il y a plusieurs points.

<context>
{{CONTEXT}}
</context>

Question : {{QUESTION}}
Réponds maintenant.
"""


def query_ollama_sync(prompt: str, *, model: str | None = None, task: str = "qa") -> str | dict:
    model = model or OLLAMA_MODEL
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_ROLE_QA},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
        },
    }
    try:
        # Streaming: on accumule le contenu et on renvoie le texte final
        resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=body, stream=True, timeout=None)
        resp.raise_for_status()
        full_text_parts: list[str] = []
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except Exception:
                continue
            msg = chunk.get("message") or {}
            content = msg.get("content")
            if isinstance(content, str) and content:
                full_text_parts.append(content)
            if chunk.get("done") is True:
                break
        return ("".join(full_text_parts)).strip()
    except Exception as e:
        return {"error": f"❌ Erreur Ollama sync: {str(e)}"}
