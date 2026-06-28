"""
Thin service wrapper over the low-level embedding functions.

What it does:
- Adds resume- and query-shaped helpers (embed_resume, embed_job_query) that join skills into the input string.
- Keeps the rest of the app from importing app.rag directly so the embedding backend can be swapped here.
- Stateless; all caching happens inside app.rag.embeddings.

Upstream (who imports this): app/api/routes/analysis_routes.py (and any caller wanting embeddings via the service layer)
Downstream (what this imports): app.rag.embeddings (embed_text, embed_batch), logging
"""
# embed_text / embed_batch: single- and batched-call entry points into the SentenceTransformer backend
from app.rag.embeddings import embed_text, embed_batch
# get_logger: kept for parity with other services; embedding errors propagate from the rag layer
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def embed(self, text: str) -> list[float]:
        return embed_text(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return embed_batch(texts)

    def embed_resume(self, resume_text: str, skills: list[str]) -> list[float]:
        combined = f"{resume_text[:1500]} Skills: {', '.join(skills)}"
        return embed_text(combined)

    def embed_job_query(self, query: str, skills: list[str] | None = None) -> list[float]:
        if skills:
            combined = f"{query} Skills needed: {', '.join(skills)}"
        else:
            combined = query
        return embed_text(combined)


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
