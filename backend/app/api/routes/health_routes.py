"""
Health check endpoint — reports liveness of every backing service.

What it does:
- GET /health — probes ChromaDB, the SQL database, Redis, the embedding lib,
  and whether the LLM key is configured, then returns "ok" or "degraded"
- Treats Redis as optional (its failure does not flip the overall status)
- Used by Docker HEALTHCHECK and external monitoring tools

Upstream (who imports this): main.py mounts router under settings.api_prefix
(/api/v1), so the final path is GET /api/v1/health.
Downstream (what this imports): core.settings for version/keys; lazy imports
inside the handler keep startup fast and avoid hard failures if a sub-service
is unavailable (rag.vectordb, db.session, core.redis_client, sentence_transformers).
"""
# APIRouter: groups the /health endpoint so main.py can mount it under /api/v1
from fastapi import APIRouter
# get_settings: pulls app_version and openrouter_api_key for the response payload
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
