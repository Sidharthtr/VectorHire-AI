from fastapi import APIRouter
from app.schemas.response_schema import HealthResponse
from app.core.settings import get_settings
from app.rag.vectordb import get_jobs_collection

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    settings = get_settings()
    services = {}

    try:
        col = get_jobs_collection()
        services["chromadb"] = col.count() >= 0
    except Exception:
        services["chromadb"] = False

    try:
        services["embedding_model"] = True
    except Exception:
        services["embedding_model"] = False

    services["gemini_configured"] = bool(settings.gemini_api_key)

    return HealthResponse(
        status="ok" if all(services.values()) else "degraded",
        version=settings.app_version,
        services=services,
    )
