import json
from pathlib import Path
from app.rag.vectordb import get_jobs_collection, upsert_documents
from app.rag.embeddings import embed_batch
from app.rag.chunking import chunk_document
from app.schemas.job_schema import JobDocument
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
