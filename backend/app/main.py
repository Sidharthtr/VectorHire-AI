"""
VectorHire AI — FastAPI application entry point.

Startup sequence:
1. init_db()             — create SQLite tables if they don't exist
2. get_embedding_model() — warm up sentence-transformers (avoids cold-start lag)
3. Mount all routes

Phase 2 routes added:
  /debug/retrieval  — compare dense vs sparse vs hybrid results
  /debug/db         — verify SQLite connectivity
  /evaluate         — run Ragas + DeepEval on a query/context/response
  /evaluate/history — view past evaluation results
  /ingest           — trigger job ingestion from Adzuna / Arbeitnow
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

    # Initialise SQLite tables (safe to call on every startup)
    try:
        from app.db.init_db import init_db
        init_db()
    except Exception as e:
        logger.warning(f"DB init failed (non-fatal): {e}")

    # Warm up embedding model — avoids 5s cold-start on first request
    try:
        from app.rag.embeddings import get_embedding_model
        get_embedding_model()
        logger.info("Embedding model ready")
    except Exception as e:
        logger.warning(f"Embedding model warm-up failed: {e}")

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
