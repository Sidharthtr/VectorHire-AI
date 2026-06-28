"""
Bulk-ingest job postings from JSON into the ChromaDB vector store.

What it does:
- Loads a JSON file of raw job dicts, validates each into a JobDocument, and upserts to ChromaDB.
- Chunks each job's full text and embeds every chunk in one batched call (much faster than per-chunk).
- Attaches metadata (title, company, skills, experience_level...) so ChromaDB 'where' filters work at query time.

Upstream (who imports this): app/api/routes/analysis_routes.py (and any CLI / admin script that triggers ingestion)
Downstream (what this imports): json, pathlib, app.rag (vectordb, embeddings, chunking), JobDocument schema, logging
"""
# json: parse the input file of job postings
import json
# Path: typed file path argument; ingestion runs from a local jobs JSON file
from pathlib import Path
# get_jobs_collection: returns the ChromaDB collection handle; upsert_documents: idempotent insert/update by id
from app.rag.vectordb import get_jobs_collection, upsert_documents
# embed_batch: vectorise all chunks of a job in one SentenceTransformer call
from app.rag.embeddings import embed_batch
# chunk_document: splits long job text into overlapping windows so embeddings stay within model context
from app.rag.chunking import chunk_document
# JobDocument: Pydantic validation of raw JSON dicts before they hit the vector store
from app.schemas.job_schema import JobDocument
# get_logger: log per-job ingestion failures and final ingested/total tally
from app.core.logging import get_logger

logger = get_logger(__name__)


class IngestionService:
    def ingest_jobs_from_json(self, jobs_json_path: Path) -> int:
        with open(jobs_json_path, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)

        collection = get_jobs_collection()
        ingested = 0

        for job_data in jobs_data:
            try:
                job = JobDocument(**job_data)
                self._ingest_job(collection, job)
                ingested += 1
            except Exception as e:
                logger.error(f"Failed to ingest job {job_data.get('id', '?')}: {e}")

        logger.info(f"Ingested {ingested}/{len(jobs_data)} jobs into ChromaDB")
        return ingested

    def _ingest_job(self, collection, job: JobDocument) -> None:
        full_text = self._build_job_text(job)
        chunks = chunk_document(
            doc_id=job.id,
            text=full_text,
            metadata={
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "experience_level": job.experience_level,
                "employment_type": job.employment_type,
                "skills": ", ".join(job.skills),
                "remote": job.remote,
                "salary_range": job.salary_range or "",
            },
        )
        texts = [c["text"] for c in chunks]
        embeddings = embed_batch(texts)
        upsert_documents(
            collection=collection,
            ids=[c["id"] for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c["metadata"] for c in chunks],
        )

    def _build_job_text(self, job: JobDocument) -> str:
        parts = [
            f"Job Title: {job.title}",
            f"Company: {job.company}",
            f"Location: {job.location}",
            f"Experience Level: {job.experience_level}",
            f"Employment Type: {job.employment_type}",
            f"Required Skills: {', '.join(job.skills)}",
            f"Description: {job.description}",
        ]
        if job.responsibilities:
            parts.append("Responsibilities: " + " ".join(job.responsibilities))
        if job.requirements:
            parts.append("Requirements: " + " ".join(job.requirements))
        return "\n".join(parts)


def get_ingestion_service() -> IngestionService:
    return IngestionService()
