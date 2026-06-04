"""
Database initialisation helper.
Called once at app startup to create all tables if they don't exist.
Safe to call multiple times (CREATE TABLE IF NOT EXISTS).
"""
from app.db.base import Base
from app.db.session import get_engine
from app.db import models  # noqa: F401 — import triggers model registration
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_db() -> None:
    """Create all tables. Safe to call on every startup."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialised")
