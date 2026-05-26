from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.settings import get_settings
from app.core.logging import logger
from app.api.routes import health_routes, resume_routes, search_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Warm up embedding model on startup
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
    app.include_router(health_routes.router, prefix=prefix)
    app.include_router(resume_routes.router, prefix=prefix)
    app.include_router(search_routes.router, prefix=prefix)

    return app


app = create_app()
