"""
Startup helper that creates every table the ORM knows about.

What it does:
- init_db() calls Base.metadata.create_all(engine) — idempotent CREATE-IF-NOT-EXISTS.
- Importing app.db.models has the side-effect of registering classes onto Base.metadata.
- Called from app.main during FastAPI startup so a fresh clone "just works".

Upstream (who imports this): app.main (only caller — runs once at server boot).
Downstream (what this imports): app.db.base.Base, app.db.session.get_engine,
app.db.models (imported for registration side-effect), app.core.logging.
"""
# Base: provides .metadata.create_all() which emits the DDL for every model
from app.db.base import Base
# get_engine: the cached SQLAlchemy Engine create_all binds to
from app.db.session import get_engine
# models: side-effect import — class definitions must run so they attach to Base.metadata
from app.db import models  # noqa: F401 — import triggers model registration
# get_logger: log "tables initialised" after create_all completes
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_db() -> None:
    """Create all tables. Safe to call on every startup."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialised")
