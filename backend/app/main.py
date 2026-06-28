"""
VectorHire AI FastAPI entry point — wires settings, DB, Redis, CORS, and routes.

What it does:
- Boot sequence: load Settings -> run init_db() -> ping Redis -> register routers -> apply CORS
- lifespan() handles startup/shutdown hooks (DB tables, Redis health, embedding warm-up notes)
- create_app() composes the FastAPI instance and mounts every /api/v1 router
- Module-level `app` is what uvicorn imports (uvicorn app.main:app)

Upstream (who imports this): uvicorn / ASGI runner (entry binary)
Downstream (what this imports): fastapi, app.core.{settings,logging}, app.api.routes.*, app.db.init_db, app.core.redis_client
"""
# FastAPI: the ASGI app class we configure and expose as `app`
from fastapi import FastAPI
# CORSMiddleware: allow the frontend (different origin) to call this API
from fastapi.middleware.cors import CORSMiddleware
# asynccontextmanager: builds the lifespan handler for startup/shutdown hooks
from contextlib import asynccontextmanager
# get_settings: cached Settings (env vars, CORS origins, API prefix, app name/version)
from app.core.settings import get_settings
# logger: shared structured logger for startup/shutdown diagnostics
from app.core.logging import logger
# Route modules: each exposes a `router` mounted under settings.api_prefix
from app.api.routes import (
    health_routes,
    resume_routes,
    search_routes,
    debug_routes,
    evaluation_routes,
    ingestion_routes,
    auth_routes,
    analysis_routes,
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
    app.include_router(auth_routes.router,       prefix=prefix)
    app.include_router(resume_routes.router,     prefix=prefix)
    app.include_router(analysis_routes.router,   prefix=prefix)
    app.include_router(search_routes.router,     prefix=prefix)
    app.include_router(debug_routes.router,      prefix=prefix)
    app.include_router(evaluation_routes.router, prefix=prefix)
    app.include_router(ingestion_routes.router,  prefix=prefix)

    return app


app = create_app()
