"""Add chat_messages table for follow-up chat on saved analyses

Revision ID: 004
Revises: 003
Create Date: 2026-06-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.String(32),
            sa.ForeignKey("resume_analysis.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_chat_messages_analysis_id", "chat_messages", ["analysis_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_analysis_id", table_name="chat_messages")
    op.drop_table("chat_messages")
