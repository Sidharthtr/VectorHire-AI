"""Add jobs table

Revision ID: 002
Revises: 001
Create Date: 2026-06-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id",               sa.String(16),  primary_key=True),
        sa.Column("source_job_id",    sa.String(255), nullable=True),
        sa.Column("source",           sa.String(50),  nullable=False),
        sa.Column("title",            sa.String(255), nullable=False),
        sa.Column("company",          sa.String(255), nullable=False),
        sa.Column("location",         sa.String(255), nullable=False),
        sa.Column("description_hash", sa.String(64),  nullable=True),
        sa.Column("remote",           sa.Boolean(),   nullable=False, server_default="false"),
        sa.Column("experience_level", sa.String(20),  nullable=True),
        sa.Column("employment_type",  sa.String(50),  nullable=True),
        sa.Column("salary_range",     sa.String(100), nullable=True),
        sa.Column("first_seen_at",    sa.DateTime(),  nullable=False),
        sa.Column("last_seen_at",     sa.DateTime(),  nullable=False),
    )
    op.create_index("ix_jobs_source",        "jobs", ["source"])
    op.create_index("ix_jobs_source_job_id", "jobs", ["source_job_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_source_job_id", table_name="jobs")
    op.drop_index("ix_jobs_source",        table_name="jobs")
    op.drop_table("jobs")
