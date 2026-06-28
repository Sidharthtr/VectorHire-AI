"""
Reciprocal Rank Fusion: combine BM25 + dense rankings into one ordered list.

What it does:
- Implements the Cormack et al. (2009) RRF formula: score = Σ 1/(k+rank_i), k=60.
- Sits between the two retrievers and the orchestrator — hybrid_retriever calls
  this AFTER dense_retrieve and sparse_retrieve to merge their rankings.

Why RRF: parameter-free, works on ranks (not raw scores) so it doesn't care that
dense scores are cosine [0,1] and BM25 scores are unbounded. Documents ranked high
in both lists get the biggest boost.

Upstream (who imports this): app/rag/hybrid_retriever.py
Downstream (what this imports): app.schemas.job_schema (just for the JobDocument type)
"""
from __future__ import annotations

# JobDocument: typed payload threaded through the fused output tuples
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
