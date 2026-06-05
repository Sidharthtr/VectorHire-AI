"""
Health check endpoint — reports status of all services.
Used by Docker HEALTHCHECK and monitoring tools.

GET /api/v1/health
Response:
  {
    "status": "ok" | "degraded",
    "version": "0.1.0",
    "services": {
      "chromadb":        true,
      "database":        true,
      "redis":           true,   // false if REDIS_URL not set
      "embedding_model": true,
      "llm_configured":  true
    }
  }
"""
from fastapi import APIRouter
from app.core.settings import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    settings = get_settings()
    services: dict[str, bool] = {}

    # ChromaDB
    try:
        from app.rag.vectordb import get_jobs_collection
        col = get_jobs_collection()
        col.count()
        services["chromadb"] = True
    except Exception:
        services["chromadb"] = False

    # Database (SQLite or PostgreSQL)
    try:
        from app.db.session import SessionLocal
        with SessionLocal() as db:
            db.execute(__import__("sqlalchemy").text("SELECT 1"))
        services["database"] = True
    except Exception:
        services["database"] = False

    # Redis
    try:
        from app.core.redis_client import ping
        services["redis"] = ping()
    except Exception:
        services["redis"] = False

    # Embedding model — just verify the package is installed, don't trigger
    # a full model load/download here (that belongs on first real request).
    try:
        import sentence_transformers  # noqa: F401
        services["embedding_model"] = True
    except ImportError:
        services["embedding_model"] = False

    # LLM
    services["llm_configured"] = bool(settings.openrouter_api_key)

    # Overall status — Redis is optional so exclude it from "required" services
    required = {k: v for k, v in services.items() if k != "redis"}
    status = "ok" if all(required.values()) else "degraded"

    return {
        "status": status,
        "version": settings.app_version,
        "services": services,
    }
