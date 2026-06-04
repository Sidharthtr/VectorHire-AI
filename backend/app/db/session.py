"""
Database engine + session factory.
Use get_db() as a FastAPI dependency for request-scoped sessions.
Supports SQLite (dev) and PostgreSQL (prod) via DATABASE_URL env var.
"""
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import lru_cache
from app.core.settings import get_settings


@lru_cache()
def get_engine():
    settings = get_settings()
    # SQLite needs check_same_thread=False to work safely with FastAPI threads
    connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
    return create_engine(settings.database_url, connect_args=connect_args, echo=False)


def _make_session_factory():
    # Lazy factory — called once, cached via module-level variable
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


# Session factory — use as: `with SessionLocal() as db:`
# SQLAlchemy 2.0 Session supports context manager protocol.
SessionLocal = _make_session_factory()


def get_db():
    """FastAPI dependency — yields a DB session, closes on exit."""
    with SessionLocal() as db:
        yield db
