from app.rag.embeddings import embed_text, embed_batch
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
