"""
Resume routes — upload (parse only) and analyze (full RAG pipeline).

What it does:
- POST /resume/upload  — parse the PDF and return extracted skills/profile;
  no DB persistence (used for instant feedback in the UI)
- POST /resume/analyze — run the LangGraph workflow (parse -> retrieve ->
  rank -> explain), then upsert a Resume row (deduped by file SHA-256 per
  user) and persist a ResumeAnalysis row tied to current_user

Upstream (who imports this): main.py mounts router under /api/v1 -> paths
become /api/v1/resume/*. Frontend hits these from the upload UI.
Downstream (what this imports): graph.workflow.run_analysis_workflow drives
the actual analysis; services.resume_service does the parse-only path;
db.models for persistence; api.deps + api.dependencies for auth + upload guards.
"""
from __future__ import annotations

# hashlib: SHA-256 of file bytes for the per-user Resume dedupe key
import hashlib
# time: measure wall-clock processing_time_ms for the analyze response
import time
# Optional: typing for nullable query params (search_query, experience_filter)
from typing import Optional

# APIRouter+UploadFile+File: declare PDF multipart upload routes; Depends: DI; HTTPException: 5xx mapping
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
# Session: type hint for the DB session resolved via Depends(get_db)
from sqlalchemy.orm import Session

# validate_pdf_upload: rejects non-PDF / oversize uploads before the handler runs
from app.api.dependencies import validate_pdf_upload
# get_current_user: every resume route is protected — extracts user from JWT
from app.api.deps import get_current_user
# get_db: request-scoped DB session for Resume/ResumeAnalysis persistence
from app.db.session import get_db
# ORM models: User (owner FK), Resume (file metadata), ResumeAnalysis (stored result blob)
from app.db.models import User, Resume, ResumeAnalysis
# run_analysis_workflow: the LangGraph state machine that drives the full pipeline
from app.graph.workflow import run_analysis_workflow
# Response schemas: shape the JSON returned to the client (typed via pydantic)
from app.schemas.response_schema import AnalysisResponse, ResumeUploadResponse
# get_logger: structured logs for upload/analyze events
from app.core.logging import get_logger

router = APIRouter(prefix="/resume", tags=["Resume"])
logger = get_logger(__name__)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    _: UploadFile = Depends(validate_pdf_upload),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full pipeline: parse → extract skills → retrieve jobs → rank → explain.
    Persists Resume (deduped by file hash per user) and ResumeAnalysis rows.
    """
    t_start = time.time()
    content = await file.read()
    filename = file.filename or "resume.pdf"

    # Upsert Resume — reuse if this user already uploaded the same file
    file_hash = hashlib.sha256(content).hexdigest()
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id, Resume.hash == file_hash)
        .first()
    )
    if resume is None:
        resume = Resume(
            user_id=current_user.id,
            filename=filename,
            hash=file_hash,
        )
        db.add(resume)
        db.flush()   # populate resume.id without committing
        logger.info(f"New Resume row: {resume.id} for user {current_user.id}")
    else:
        logger.info(f"Reusing Resume row: {resume.id} (same hash)")

    try:
        final_state = await run_analysis_workflow(
            resume_bytes=content,
            resume_filename=filename,
            search_query=search_query,
            top_k=top_k,
            experience_filter=experience_filter,
        )

        elapsed_ms = round((time.time() - t_start) * 1000, 1)
        explained_jobs = final_state.get("explained_jobs", [])

        response = AnalysisResponse(
            success=True,
            resume_id=resume.id,
            top_jobs=explained_jobs,
            overall_match_summary=final_state.get("overall_summary", ""),
            top_missing_skills=final_state.get("top_missing_skills", []),
            improvement_suggestions=final_state.get("improvement_suggestions", []),
            processing_time_ms=elapsed_ms,
        )

        top_match = max(
            (j.match_percentage for j in explained_jobs), default=0.0
        )
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            analysis_json=response.model_dump(),
            top_match_pct=top_match,
            processing_time_ms=elapsed_ms,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(
            f"Saved ResumeAnalysis {analysis.id} (user={current_user.id}, "
            f"top_match={top_match:.1f}%)"
        )

        response.analysis_id = analysis.id
        return response

    except Exception as e:
        db.rollback()
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
