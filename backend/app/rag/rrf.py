"""
Reciprocal Rank Fusion (RRF).

RRF is a simple, parameter-free technique for merging multiple ranked lists
into one combined ranking. It was introduced by Cormack et al. (2009) and
has become the default fusion strategy for hybrid retrieval systems.

Formula for each document:
    rrf_score = Σ  1 / (k + rank_i)
where k=60 (recommended by the original paper) and rank_i is the 1-indexed
rank of the document in retrieval system i.

Key properties:
- Documents that appear high in BOTH lists get a large boost.
- Documents that only appear in one list are still included but ranked lower.
- k=60 controls how much early ranks dominate — higher k = flatter curve.
"""
from __future__ import annotations

from app.schemas.job_schema import JobDocument

# Recommended constant from the original RRF paper.
_K = 60


def reciprocal_rank_fusion(
    dense_results: list[tuple[JobDocument, float, int]],
    sparse_results: list[tuple[JobDocument, float, int]],
    top_k: int = 10,
) -> list[tuple[JobDocument, float, float, float]]:
    """
    Merge dense and sparse ranked lists using RRF.

    Args:
        dense_results:  list of (JobDocument, dense_score, dense_rank)
        sparse_results: list of (JobDocument, sparse_score, sparse_rank)
        top_k:          how many results to return

    Returns:
        list of (JobDocument, dense_score, sparse_score, rrf_score)
        sorted by rrf_score descending.
    """
    # Index dense results by job id
    dense_by_id: dict[str, tuple[JobDocument, float, int]] = {
        job.id: (job, score, rank) for job, score, rank in dense_results
    }
    sparse_by_id: dict[str, tuple[JobDocument, float, int]] = {
        job.id: (job, score, rank) for job, score, rank in sparse_results
    }

    all_job_ids = set(dense_by_id) | set(sparse_by_id)

    fused: list[tuple[JobDocument, float, float, float]] = []

    for job_id in all_job_ids:
        # Dense contribution: 1/(k+rank) or 0 if not in dense results
        if job_id in dense_by_id:
            job, d_score, d_rank = dense_by_id[job_id]
            dense_contrib = 1.0 / (_K + d_rank)
        else:
            # Use the job from sparse if not in dense
            job = sparse_by_id[job_id][0]
            d_score = 0.0
            dense_contrib = 0.0

        # Sparse contribution
        if job_id in sparse_by_id:
            _, s_score, s_rank = sparse_by_id[job_id]
            sparse_contrib = 1.0 / (_K + s_rank)
        else:
            s_score = 0.0
            sparse_contrib = 0.0

        rrf_score = dense_contrib + sparse_contrib
        fused.append((job, d_score, s_score, round(rrf_score, 6)))

    fused.sort(key=lambda x: x[3], reverse=True)
    return fused[:top_k]
