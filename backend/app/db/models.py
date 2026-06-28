"""
SQLAlchemy ORM models — every relational table the app uses.

What it does:
- Defines User, Resume, ResumeAnalysis, ChatMessage, JobSearch, Evaluation, Job tables.
- Sets up relationships (User→Resume, Resume→Analyses/Searches, JobSearch→Evaluations).
- ChromaDB holds vectors; this module holds metadata + relational links between them.

Upstream (who imports this): app.db.init_db (table creation), app.db.job_repository,
app.api.deps (User lookup), app.api.routes (analysis, debug, resume, auth, evaluation),
app.evaluation.evaluation_service.
Downstream (what this imports): uuid, datetime, sqlalchemy column types + Mapped,
app.db.base.Base.
"""
from __future__ import annotations
# uuid: _new_id() generates 32-char hex primary keys for every row
import uuid
# datetime: default value for created_at / first_seen_at / last_seen_at columns
from datetime import datetime
# Column types: String/Text/Float/DateTime/ForeignKey/JSON/Boolean — every column type used in this file
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON, Boolean
# Mapped + mapped_column: SQLAlchemy 2.0 typed column syntax; relationship: links between tables
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Base: the single DeclarativeBase every model inherits from (shared metadata registry)
from app.db.base import Base


def _new_id() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resumes: Mapped[list["Resume"]] = relationship("Resume", back_populates="user")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    user_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("users.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    hash: Mapped[str] = mapped_column(String(64), index=True)      # sha256 for cache lookup
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # extracted skills list
    experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User | None"] = relationship("User", back_populates="resumes")
    analyses: Mapped[list["ResumeAnalysis"]] = relationship("ResumeAnalysis", back_populates="resume")
    searches: Mapped[list["JobSearch"]] = relationship("JobSearch", back_populates="resume")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analysis"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    resume_id: Mapped[str] = mapped_column(String(32), ForeignKey("resumes.id"))
    analysis_json: Mapped[dict] = mapped_column(JSON)      # full pipeline output
    top_match_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="analyses")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    analysis_id: Mapped[str] = mapped_column(String(32), ForeignKey("resume_analysis.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))   # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class JobSearch(Base):
    __tablename__ = "job_searches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    resume_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("resumes.id"), nullable=True)
    query: Mapped[str] = mapped_column(Text)
    retrieval_mode: Mapped[str] = mapped_column(String(20), default="hybrid")
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume | None"] = relationship("Resume", back_populates="searches")
    evaluations: Mapped[list["Evaluation"]] = relationship("Evaluation", back_populates="search")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    search_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("job_searches.id"), nullable=True)
    query: Mapped[str] = mapped_column(Text)
    faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluator_used: Mapped[str] = mapped_column(String(50), default="llm_based")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    search: Mapped["JobSearch | None"] = relationship("JobSearch", back_populates="evaluations")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)   # MD5(title|company|source)
    source_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    description_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remote: Mapped[bool] = mapped_column(Boolean, default=False)
    experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
