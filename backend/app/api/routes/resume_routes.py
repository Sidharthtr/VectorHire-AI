import time
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.api.dependencies import validate_pdf_upload
from app.graph.workflow import run_analysis_workflow
from app.schemas.response_schema import AnalysisResponse, ResumeUploadResponse
from app.core.logging import get_logger
from typing import Optional

router = APIRouter(prefix="/resume", tags=["Resume"])
logger = get_logger(__name__)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    _: UploadFile = Depends(validate_pdf_upload),
):
    """Parse a resume PDF and return extracted skills and profile."""
    from app.services.resume_service import get_resume_service
    content = await file.read()
    service = get_resume_service()
    try:
        resume_id, parsed = service.process_upload(content, file.filename or "resume.pdf")
        return ResumeUploadResponse(
            success=True,
            message="Resume parsed successfully",
            resume_id=resume_id,
            parsed_resume=parsed,
        )
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    _: UploadFile = Depends(validate_pdf_upload),
    search_query: Optional[str] = None,
    top_k: int = 10,
    experience_filter: Optional[str] = None,
):
    """
    Full pipeline: upload resume → parse → extract skills → retrieve jobs →
    rank matches → generate explanations. Returns complete analysis.
    """
    t_start = time.time()
    content = await file.read()

    try:
        final_state = await run_analysis_workflow(
            resume_bytes=content,
            resume_filename=file.filename or "resume.pdf",
            search_query=search_query,
            top_k=top_k,
            experience_filter=experience_filter,
        )

        elapsed_ms = (time.time() - t_start) * 1000
        missing = final_state.get("top_missing_skills", [])

        return AnalysisResponse(
            success=True,
            resume_id=final_state.get("resume_id", ""),
            top_jobs=final_state.get("explained_jobs", []),
            overall_match_summary=final_state.get("overall_summary", ""),
            top_missing_skills=missing,
            improvement_suggestions=final_state.get("improvement_suggestions", []),
            processing_time_ms=round(elapsed_ms, 1),
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
