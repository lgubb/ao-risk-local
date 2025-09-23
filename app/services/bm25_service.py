from __future__ import annotations
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import re

# Tokenizer simple FR/EN
_tok = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", re.UNICODE)

class BM25Store:
    def __init__(self):
        self.docs: List[str] = []
        self.metas: List[Dict[str, Any]] = []
        self.ids: List[str] = []
        self._bm25: BM25Okapi | None = None

    def _tokenize(self, s: str) -> List[str]:
        return [w.lower() for w in _tok.findall(s)]

    def add_batch(self, ids: List[str], docs: List[str], metas: List[Dict[str, Any]]):
        self.ids.extend(ids)
        self.docs.extend(docs)
        self.metas.extend(metas)
        tokenized = [self._tokenize(d) for d in self.docs]
        self._bm25 = BM25Okapi(tokenized)

    def query(self, text: str, top_k: int = 20):
        if not self._bm25 or not self.docs:
            return []
        tokens = self._tokenize(text)
        scores = self._bm25.get_scores(tokens)
        # top_k indices
        idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [{"id": self.ids[i], "score": float(scores[i]), "metadata": self.metas[i], "document": self.docs[i]} for i in idxs]

BM25_GLOBAL = BM25Store()

def bm25_add(ids: List[str], docs: List[str], metas: List[Dict[str, Any]]):
    BM25_GLOBAL.add_batch(ids, docs, metas)

def bm25_query(q: str, top_k: int = 20):
    return BM25_GLOBAL.query(q, top_k=top_k)
