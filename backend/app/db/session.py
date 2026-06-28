"""
Database engine + session factory — the only place we open DB connections.

What it does:
- get_engine() builds (and caches) the SQLAlchemy Engine from settings.database_url.
- SessionLocal is the sessionmaker every request session is spawned from.
- get_db() is the FastAPI dependency that yields a session and closes it after.

Upstream (who imports this): app.api.deps (get_db for routes), app.db.init_db,
app.api.routes (analysis, ingestion, debug, resume, auth, evaluation, health),
app.ingestion.job_pipeline, app.evaluation.evaluation_service.
Downstream (what this imports): sqlalchemy (create_engine, sessionmaker),
functools.lru_cache, app.core.settings.
"""
from __future__ import annotations
# create_engine: builds the SQLAlchemy Engine that talks to SQLite or Postgres
from sqlalchemy import create_engine
# sessionmaker: factory function used to spawn per-request Session objects
from sqlalchemy.orm import sessionmaker
# lru_cache: ensure exactly one Engine exists per process (connection pool reuse)
from functools import lru_cache
# get_settings: reads settings.database_url to pick SQLite vs Postgres at runtime
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
