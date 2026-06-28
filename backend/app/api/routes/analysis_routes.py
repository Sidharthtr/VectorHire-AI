"""
Analysis history + per-analysis follow-up chat.

What it does:
- GET  /analysis/history           — list saved analyses for the current user
- GET  /analysis/{id}              — fetch one saved analysis (owner-checked)
- GET  /analysis/{id}/messages     — chat history for a given analysis
- POST /analysis/{id}/chat         — streaming chat reply; persists both turns

Upstream (who imports this): main.py mounts router under /api/v1 -> public
paths /api/v1/analysis/*. Frontend history page + chat sidebar call these.
Downstream (what this imports): db.models for ORM rows, services.chat_service
for the LLM streaming generator, response/chat schemas for typed payloads,
api.deps.get_current_user for ownership enforcement.
"""
from __future__ import annotations

# datetime: response field type for created_at in AnalysisSummary
from datetime import datetime
# Optional: nullable top_match_pct in the summary schema
from typing import Optional

# APIRouter+Depends+HTTPException: route group, DI, and typed 404/500 errors
from fastapi import APIRouter, Depends, HTTPException
# StreamingResponse: streams the LLM reply token-by-token over HTTP for /chat
from fastapi.responses import StreamingResponse
# BaseModel: declares the AnalysisSummary response schema
from pydantic import BaseModel
# Session: type hint for the DB session injected via Depends(get_db)
from sqlalchemy.orm import Session

# SessionLocal: opens a fresh session inside the streaming generator (request session is already closed)
# get_db: normal request-scoped session for the read endpoints
from app.db.session import SessionLocal, get_db
# ORM models touched here: User (owner), Resume (join target), ResumeAnalysis (history rows), ChatMessage (chat turns)
from app.db.models import User, Resume, ResumeAnalysis, ChatMessage
# get_current_user: every analysis route is gated by JWT auth
from app.api.deps import get_current_user
# AnalysisResponse: schema returned by GET /analysis/{id} (rehydrated from analysis_json blob)
from app.schemas.response_schema import AnalysisResponse
# ChatMessageOut + ChatRequest: response/request shapes for the chat endpoints
from app.schemas.chat_schema import ChatMessageOut, ChatRequest
# stream_reply: generator that yields LLM tokens given history + analysis context
from app.services.chat_service import stream_reply
# get_logger: structured logging for chat/stream errors and persistence events
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
