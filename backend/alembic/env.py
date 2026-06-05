"""
Alembic environment — wires our SQLAlchemy models into the migration engine.

How to use:
  cd backend

  # Create a new migration after changing models.py:
  alembic revision --autogenerate -m "add_column_xyz"

  # Apply pending migrations:
  alembic upgrade head

  # Roll back one migration:
  alembic downgrade -1

  # See current migration version:
  alembic current

The DATABASE_URL is read from app settings (which reads from .env),
so you never need to hardcode it here.
"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Make sure app/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import our models so Alembic can see them for autogenerate
from app.db.base import Base
from app.db import models  # noqa: F401 — registers all ORM models with Base

# Alembic config object (reads alembic.ini)
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object that autogenerate inspects
target_metadata = Base.metadata


def get_url() -> str:
    """Pull DATABASE_URL from app settings (reads .env)."""
    from app.core.settings import get_settings
    return get_settings().database_url


def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection.
    Generates SQL scripts you can review before applying.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no pooling during migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # detect column type changes
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
