"""
Analysis history + follow-up chat routes.

GET  /analysis/history             — list all analyses for the current user
GET  /analysis/{id}                — retrieve a specific saved analysis
GET  /analysis/{id}/messages       — load chat history for an analysis
POST /analysis/{id}/chat           — streaming chat (plain-text), persists turns
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.db.models import User, Resume, ResumeAnalysis, ChatMessage
from app.api.deps import get_current_user
from app.schemas.response_schema import AnalysisResponse
from app.schemas.chat_schema import ChatMessageOut, ChatRequest
from app.services.chat_service import stream_reply
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisSummary(BaseModel):
    id: str
    resume_name: str
    top_match_pct: Optional[float]
    job_count: int
    created_at: datetime


@router.get("/history", response_model=list[AnalysisSummary])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all saved analyses for the authenticated user, newest first."""
    rows = (
        db.query(ResumeAnalysis, Resume.filename)
        .join(Resume, ResumeAnalysis.resume_id == Resume.id)
        .filter(Resume.user_id == current_user.id)
        .order_by(ResumeAnalysis.created_at.desc())
        .all()
    )

    results = []
    for analysis, filename in rows:
        job_count = 0
        if isinstance(analysis.analysis_json, dict):
            job_count = len(analysis.analysis_json.get("top_jobs", []))
        results.append(AnalysisSummary(
            id=analysis.id,
            resume_name=filename,
            top_match_pct=analysis.top_match_pct,
            job_count=job_count,
            created_at=analysis.created_at,
        ))

    return results


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a specific saved analysis. Enforces ownership."""
    analysis = (
        db.query(ResumeAnalysis)
        .join(Resume, ResumeAnalysis.resume_id == Resume.id)
        .filter(
            ResumeAnalysis.id == analysis_id,
            Resume.user_id == current_user.id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    try:
        data = dict(analysis.analysis_json or {})
        data["analysis_id"] = analysis.id   # inject — not stored inside the JSON blob
        return AnalysisResponse.model_validate(data)
    except Exception as e:
        logger.error(f"Failed to deserialise analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Stored analysis could not be loaded")


def _load_owned_analysis(analysis_id: str, user_id: str, db: Session) -> ResumeAnalysis:
    analysis = (
        db.query(ResumeAnalysis)
        .join(Resume, ResumeAnalysis.resume_id == Resume.id)
        .filter(
            ResumeAnalysis.id == analysis_id,
            Resume.user_id == user_id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/{analysis_id}/messages", response_model=list[ChatMessageOut])
def get_messages(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the chat history for one saved analysis, oldest first."""
    _load_owned_analysis(analysis_id, current_user.id, db)
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.analysis_id == analysis_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return rows


@router.post("/{analysis_id}/chat")
def chat(
    analysis_id: str,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streaming chat reply (plain text). The response body is the assistant
    message as it's generated. After streaming completes, both turns are
    persisted to chat_messages.
    """
    analysis = _load_owned_analysis(analysis_id, current_user.id, db)

    # Persist the user turn immediately so we have a record even if the
    # stream fails.
    user_msg = ChatMessage(
        analysis_id=analysis.id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    db.commit()

    # Snapshot history + analysis blob — pass plain dicts so the generator
    # doesn't touch the request-scoped session after it's closed.
    history = [
        {"role": m.role, "content": m.content}
        for m in (
            db.query(ChatMessage)
            .filter(
                ChatMessage.analysis_id == analysis.id,
                ChatMessage.id != user_msg.id,   # current turn is appended by the service
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
    ]
    analysis_json = dict(analysis.analysis_json or {})
    user_content = body.content

    def gen():
        chunks: list[str] = []
        try:
            for tok in stream_reply(analysis_json, history, user_content):
                chunks.append(tok)
                yield tok
        except Exception as e:
            logger.error(f"chat stream failed for analysis {analysis.id}: {e}")
            yield f"\n\n[error: {e}]"
        finally:
            # Persist assistant turn in a fresh session — the request session
            # is already closed by the time StreamingResponse finishes.
            reply = "".join(chunks).strip()
            if reply:
                with SessionLocal() as s:
                    s.add(ChatMessage(
                        analysis_id=analysis_id,
                        role="assistant",
                        content=reply,
                    ))
                    s.commit()

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")
