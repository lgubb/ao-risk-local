import os
import re
from transformers import CamembertTokenizer

tokenizer = CamembertTokenizer.from_pretrained("camembert-base")

def split_by_structure(text: str) -> list[str]:
    """
    Découpe un DCE par structure :
    - Articles (ex: "Article 4 – Délais d’exécution")
    - Sections en majuscules (ex: "CAHIER DES CLAUSES...")
    - Retourne une liste de blocs textuels bruts.
    """
    # Normaliser les séparateurs
    text = re.sub(r"\n{2,}", "\n\n", text)

    # Split par repères structurels
    parts = re.split(r"(?=Article\s+\d+)|(?=CAHIER)|(?=RÈGLEMENT)|(?=ACTE D'ENGAGEMENT)", text, flags=re.IGNORECASE)

    # Nettoyer les morceaux vides
    parts = [p.strip() for p in parts if p.strip()]
    return parts

def chunk_text(text: str, max_tokens: int = 480, overlap_tokens: int = 50) -> list[str]:
    """
    Chunker hybride :
    1. Découpe d'abord par structure DCE (articles, sections).
    2. Si une section est trop longue (> max_tokens), on la re-chunke par sliding window.
    """
    structured_chunks = split_by_structure(text)
    final_chunks = []

    for section in structured_chunks:
        tokens = tokenizer.encode(section, add_special_tokens=False)
        if len(tokens) <= max_tokens:
            final_chunks.append(section)
        else:
            # Sliding window sur les longues sections
            i = 0
            while i < len(tokens):
                chunk_tokens = tokens[i:i + max_tokens]
                chunk_text_str = tokenizer.decode(chunk_tokens)
                final_chunks.append(chunk_text_str)
                i += max_tokens - overlap_tokens

    # Debug (activable via DEBUG_CHUNKER=1)
    if os.getenv("DEBUG_CHUNKER") == "1":
        print(f"[DEBUG] Total structured chunks créés : {len(final_chunks)}")
        for idx, ch in enumerate(final_chunks):
            t_count = len(tokenizer.encode(ch, add_special_tokens=False))
            print(f"[DEBUG] Chunk {idx}: {t_count} tokens | Début: {ch[:60]}...")

    return final_chunks
