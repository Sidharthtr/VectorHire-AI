import numpy as np
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
