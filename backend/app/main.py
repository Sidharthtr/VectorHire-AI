"""
VectorHire AI — FastAPI application entry point.

Startup sequence:
1. init_db()             — create DB tables (or run Alembic in Docker via CMD)
2. Redis ping            — confirm cache is reachable (non-fatal if absent)
3. get_embedding_model() — warm up sentence-transformers on first worker start

Routes:
  /api/v1/health            — liveness + service status
  /api/v1/resume/upload     — PDF upload
  /api/v1/resume/analyze    — full pipeline (parse → match → explain)
  /api/v1/search/jobs       — job search by query
  /api/v1/debug/retrieval   — compare dense vs sparse vs hybrid
  /api/v1/debug/db          — DB connectivity check
  /api/v1/evaluate          — RAG quality metrics
  /api/v1/evaluate/history  — past evaluation results
  /api/v1/ingest            — trigger job ingestion from external APIs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.settings import get_settings
from app.core.logging import logger
from app.api.routes import (
    health_routes,
    resume_routes,
    search_routes,
    debug_routes,
    evaluation_routes,
    ingestion_routes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # 1. DB tables — safe to call every startup (CREATE TABLE IF NOT EXISTS)
    #    In Docker the Dockerfile CMD runs `alembic upgrade head` before uvicorn,
    #    so this is a no-op there. Useful for local dev without Docker.
    try:
        from app.db.init_db import init_db
        init_db()
    except Exception as e:
        logger.warning(f"DB init skipped (non-fatal): {e}")

    # 2. Redis connectivity check
    try:
        from app.core.redis_client import ping
        if ping():
            logger.info("Redis connected and ready")
        else:
            logger.info("Redis not configured — caching disabled (set REDIS_URL to enable)")
    except Exception as e:
        logger.warning(f"Redis check failed: {e}")

    # Embedding model is pre-cached in the Docker image (see Dockerfile).
    # Lazy-loading on first request takes ~2s from disk — no startup block needed.

    yield
    logger.info("Shutting down VectorHire AI")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Agentic AI-powered career copilot platform",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    app.include_router(health_routes.router,     prefix=prefix)
    app.include_router(resume_routes.router,     prefix=prefix)
    app.include_router(search_routes.router,     prefix=prefix)
    app.include_router(debug_routes.router,      prefix=prefix)
    app.include_router(evaluation_routes.router, prefix=prefix)
    app.include_router(ingestion_routes.router,  prefix=prefix)

    return app


app = create_app()
