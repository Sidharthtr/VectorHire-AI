"""Initial schema — users, resumes, resume_analysis, job_searches, evaluations

Revision ID: 001
Revises:
Create Date: 2026-06-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id",         sa.String(32),  primary_key=True),
        sa.Column("email",      sa.String(255), unique=True, nullable=True),
        sa.Column("created_at", sa.DateTime(),  nullable=False),
    )

    op.create_table(
        "resumes",
        sa.Column("id",               sa.String(32),  primary_key=True),
        sa.Column("user_id",          sa.String(32),  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("filename",         sa.String(255), nullable=False),
        sa.Column("hash",             sa.String(64),  nullable=False),
        sa.Column("parsed_text",      sa.Text(),      nullable=True),
        sa.Column("skills_json",      sa.JSON(),      nullable=True),
        sa.Column("experience_level", sa.String(20),  nullable=True),
        sa.Column("created_at",       sa.DateTime(),  nullable=False),
    )
    op.create_index("ix_resumes_hash", "resumes", ["hash"])

    op.create_table(
        "resume_analysis",
        sa.Column("id",                  sa.String(32), primary_key=True),
        sa.Column("resume_id",           sa.String(32), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("analysis_json",       sa.JSON(),     nullable=False),
        sa.Column("top_match_pct",       sa.Float(),    nullable=True),
        sa.Column("processing_time_ms",  sa.Float(),    nullable=True),
        sa.Column("created_at",          sa.DateTime(), nullable=False),
    )

    op.create_table(
        "job_searches",
        sa.Column("id",             sa.String(32), primary_key=True),
        sa.Column("resume_id",      sa.String(32), sa.ForeignKey("resumes.id"), nullable=True),
        sa.Column("query",          sa.Text(),     nullable=False),
        sa.Column("retrieval_mode", sa.String(20), nullable=False, server_default="hybrid"),
        sa.Column("results_json",   sa.JSON(),     nullable=True),
        sa.Column("result_count",   sa.Integer(),  nullable=False, server_default="0"),
        sa.Column("created_at",     sa.DateTime(), nullable=False),
    )

    op.create_table(
        "evaluations",
        sa.Column("id",                  sa.String(32), primary_key=True),
        sa.Column("search_id",           sa.String(32), sa.ForeignKey("job_searches.id"), nullable=True),
        sa.Column("query",               sa.Text(),     nullable=False),
        sa.Column("faithfulness",        sa.Float(),    nullable=True),
        sa.Column("context_precision",   sa.Float(),    nullable=True),
        sa.Column("context_recall",      sa.Float(),    nullable=True),
        sa.Column("hallucination_score", sa.Float(),    nullable=True),
        sa.Column("evaluator_used",      sa.String(50), nullable=False, server_default="llm_based"),
        sa.Column("created_at",          sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evaluations")
    op.drop_table("job_searches")
    op.drop_table("resume_analysis")
    op.drop_index("ix_resumes_hash", table_name="resumes")
    op.drop_table("resumes")
    op.drop_table("users")
