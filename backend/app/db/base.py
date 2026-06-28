"""
SQLAlchemy 2.0 declarative Base — the single registry every ORM model attaches to.

What it does:
- Defines `Base = DeclarativeBase` so models can do `class Resume(Base): ...`.
- Centralising the Base prevents two metadata registries (which would break create_all).

Upstream (who imports this): app.db.models (all ORM tables), app.db.init_db
(calls Base.metadata.create_all at startup).
Downstream (what this imports): sqlalchemy.orm.DeclarativeBase only.
"""
# DeclarativeBase: SQLAlchemy 2.0 typed base class — replaces the legacy declarative_base()
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
