"""
Vector similarity utilities — cosine math + score-to-percentage helpers.

What it does:
- cosine_similarity(): the dot-product-over-norms classic, used when we have raw
  vectors in hand (e.g. comparing a resume embedding to a candidate list in memory).
- rank_by_similarity(): score + sort a list of {embedding: [...]} dicts.
- similarity_to_percentage(): UI-facing helper that maps cosine [-1, 1] -> 0..100
  for "X% match" displays.
- Sits OUTSIDE the Chroma path — Chroma computes cosine internally; this module
  is for in-app comparisons and for formatting scores for the API response.

Upstream (who imports this): app/services/ranking_service.py,
    app/api/routes/search_routes.py
Downstream (what this imports): numpy
"""
# numpy: vector arithmetic (dot product, L2 norm) for cosine similarity
import numpy as np
# Optional: type hint for the optional top_k parameter in rank_by_similarity
from typing import Optional


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def rank_by_similarity(
    query_embedding: list[float],
    candidates: list[dict],
    embedding_key: str = "embedding",
    top_k: Optional[int] = None,
) -> list[tuple[dict, float]]:
    scored = [
        (candidate, cosine_similarity(query_embedding, candidate[embedding_key]))
        for candidate in candidates
        if embedding_key in candidate
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    if top_k:
        scored = scored[:top_k]
    return scored


def similarity_to_percentage(score: float) -> float:
    """Map cosine similarity [-1, 1] to match percentage [0, 100]."""
    return round(max(0.0, min(100.0, (score + 1) / 2 * 100)), 1)
