
"""In-memory RAG store with optional Qdrant hook (self-contained fallback)."""
from __future__ import annotations

import math
import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class MemoryStore:
    def __init__(self) -> None:
        self._docs: list[tuple[str, str]] = []  # id, text

    def upsert(self, doc_id: str, text: str) -> None:
        self._docs = [(i, t) for i, t in self._docs if i != doc_id]
        self._docs.append((doc_id, text))

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        if not self._docs:
            return []
        q = Counter(_tokens(query))
        scored: list[tuple[float, str]] = []
        for _, text in self._docs:
            d = Counter(_tokens(text))
            # cosine on bag-of-words
            dot = sum(q[t] * d[t] for t in q)
            nq = math.sqrt(sum(v * v for v in q.values())) or 1.0
            nd = math.sqrt(sum(v * v for v in d.values())) or 1.0
            scored.append((dot / (nq * nd), text))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for s, t in scored[:k] if s > 0]


# Process-local store for demo
STORE = MemoryStore()
