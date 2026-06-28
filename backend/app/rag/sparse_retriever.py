"""
Sparse (keyword) retriever — BM25 half of the hybrid RAG pipeline.

What it does:
- Lazily loads every job from ChromaDB, tokenises descriptions, and builds an in-memory
  BM25Okapi index that scores queries by classic lexical match (TF, IDF, length norm).
- Sits parallel to dense_retriever; hybrid_retriever calls both and fuses with RRF.
- Index is invalidated via reset_sparse_index() after ingestion / cleanup so new jobs
  show up on the next query.

Upstream (who imports this): app/rag/hybrid_retriever.py, app/rag/cleanup.py,
    app/ingestion/job_embedder.py
Downstream (what this imports): rank_bm25, app.rag.vectordb, app.schemas.job_schema
"""
from __future__ import annotations

# re: regex-based tokeniser — strips punctuation before BM25 sees the text
import re
# Optional: type hint for the optional experience_level filter argument
from typing import Optional

# BM25Okapi: the actual sparse scoring algorithm (Okapi BM25 variant)
from rank_bm25 import BM25Okapi

# get_jobs_collection: source of the BM25 corpus — we materialise all jobs from Chroma
from app.rag.vectordb import get_jobs_collection
# JobDocument: typed shape returned alongside each BM25 score
from app.schemas.job_schema import JobDocument
# DEFAULT_TOP_K: shared result-size default with the dense side
from app.core.constants import DEFAULT_TOP_K
# get_logger: logs index (re)build events and corpus size
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level cache — built once, reused across requests.
_bm25_index: BM25Okapi | None = None
_indexed_jobs: list[JobDocument] = []


def _tokenise(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()


def _load_all_jobs() -> list[JobDocument]:
    """Fetch every job stored in ChromaDB to build the BM25 corpus."""
    collection = get_jobs_collection()
    count = collection.count()
    if count == 0:
        return []

    results = collection.get(
        limit=count,
        include=["documents", "metadatas"],
    )

    jobs: list[JobDocument] = []
    for doc_id, document, meta in zip(
        results.get("ids", []),
        results.get("documents", []),
        results.get("metadatas", []),
    ):
        skills_raw = meta.get("skills", [])
        skills = (
            skills_raw
            if isinstance(skills_raw, list)
            else [s.strip() for s in skills_raw.split(",") if s.strip()]
        )
        try:
            jobs.append(JobDocument(
                id=meta.get("job_id", doc_id),
                title=meta.get("title", ""),
                company=meta.get("company", ""),
                location=meta.get("location", ""),
                experience_level=meta.get("experience_level", "entry"),
                employment_type=meta.get("employment_type", "full-time"),
                skills=skills,
                description=document or "",
                remote=bool(meta.get("remote", False)),
                salary_range=meta.get("salary_range"),
            ))
        except Exception as e:
            logger.warning(f"Skipping malformed job {doc_id}: {e}")
    return jobs


def _get_index() -> tuple[BM25Okapi, list[JobDocument]]:
    """Return cached index, building it on first call."""
    global _bm25_index, _indexed_jobs
    if _bm25_index is None:
        logger.info("Building BM25 index from ChromaDB...")
        _indexed_jobs = _load_all_jobs()
        if not _indexed_jobs:
            logger.warning("BM25 index empty — no jobs in ChromaDB")
            _bm25_index = BM25Okapi([[]])
        else:
            corpus = [_tokenise(j.description + " " + " ".join(j.skills)) for j in _indexed_jobs]
            _bm25_index = BM25Okapi(corpus)
            logger.info(f"BM25 index built: {len(_indexed_jobs)} documents")
    return _bm25_index, _indexed_jobs


def reset_sparse_index() -> None:
    """Force-rebuild the BM25 index on next query (call after ingestion)."""
    global _bm25_index, _indexed_jobs
    _bm25_index = None
    _indexed_jobs = []
    logger.info("BM25 index cleared — will rebuild on next query")


def sparse_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    experience_level: Optional[str] = None,
    remote_only: bool = False,
) -> list[tuple[JobDocument, float, int]]:
    """
    BM25 keyword search over job descriptions.
    Returns list of (JobDocument, normalised_score, rank) sorted best-first.
    Scores are normalised to [0, 1] so they're comparable to dense scores.
    """
    bm25, all_jobs = _get_index()
    if not all_jobs:
        return []

    tokens = _tokenise(query)
    raw_scores = bm25.get_scores(tokens)

    max_score = max(raw_scores) if max(raw_scores) > 0 else 1.0
    norm_scores = [float(s) / max_score for s in raw_scores]

    scored = list(zip(all_jobs, norm_scores))

    if experience_level:
        scored = [(j, s) for j, s in scored if j.experience_level == experience_level]
    if remote_only:
        scored = [(j, s) for j, s in scored if j.remote]

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    return [(job, score, rank + 1) for rank, (job, score) in enumerate(top)]
