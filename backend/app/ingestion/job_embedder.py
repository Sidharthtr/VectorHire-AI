"""
Embeds JobDocuments and upserts them into ChromaDB with rich metadata.

What it does:
- _build_embed_text(): concatenates title + skills + description for the embedding model
- embed_and_store_jobs(): vectorises a batch, upserts to ChromaDB, resets BM25 sparse index
- Embedder step in the data flow: adapter -> normalizer -> embedder (this file) -> pipeline (orchestrator)

Upstream (who imports this): app/ingestion/job_pipeline.py
Downstream (what this imports): app.schemas.job_schema (JobDocument), app.rag.embeddings, app.rag.vectordb, app.rag.sparse_retriever, app.core.logging
"""
from __future__ import annotations

# time: Unix timestamp stamped on each row for TTL cleanup of stale jobs
import time

# JobDocument: input type — already-normalised job records
from app.schemas.job_schema import JobDocument
# embed_text: sentence-transformers wrapper that returns a 384-dim vector
from app.rag.embeddings import embed_text
# get_jobs_collection / upsert_documents: Chroma handle + batch upsert helper
from app.rag.vectordb import get_jobs_collection, upsert_documents
# reset_sparse_index: BM25 cache is invalidated after new docs land
from app.rag.sparse_retriever import reset_sparse_index
# get_logger: report per-batch storage counts and per-job embed errors
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_embed_text(job: JobDocument) -> str:
    """
    Build the text that gets embedded into the vector space.
    We combine title + skills + description because:
      - Title gives strong semantic signal for role matching.
      - Skills keywords help BM25 and dense search both.
      - Description provides rich context for nuanced queries.
    """
    skills_str = ", ".join(job.skills) if job.skills else ""
    return f"{job.title}. {skills_str}. {job.description}"[:2000]


def embed_and_store_jobs(jobs: list[JobDocument]) -> int:
    """
    Embed a batch of jobs and upsert into ChromaDB.

    Args:
        jobs: list of validated JobDocuments to store

    Returns:
        Number of jobs successfully stored.
    """
    if not jobs:
        return 0

    collection = get_jobs_collection()
    ids, embeddings, documents, metadatas = [], [], [], []

    for job in jobs:
        try:
            text = _build_embed_text(job)
            vector = embed_text(text)

            ids.append(job.id)
            embeddings.append(vector)
            documents.append(job.description[:4000])  # Chroma stores document for BM25 fallback
            metadatas.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "experience_level": job.experience_level,
                "employment_type": job.employment_type,
                "skills": ", ".join(job.skills),  # ChromaDB metadata must be scalar
                "remote": job.remote,
                "salary_range": job.salary_range or "",
                "description": job.description[:500],  # truncated for metadata
                "ingested_at": int(time.time()),  # Unix timestamp — used for TTL cleanup
            })
        except Exception as e:
            logger.warning(f"Skipping job '{job.title}' ({job.id}): embed error: {e}")

    if ids:
        upsert_documents(collection, ids, embeddings, documents, metadatas)
        # BM25 index is now stale — clear it so it rebuilds on next query
        reset_sparse_index()
        logger.info(f"Stored {len(ids)} jobs in ChromaDB")

    return len(ids)
