"""Add per-user lecture progress.

Revision ID: 2e834b6c9171
Revises: 5df3b1a74c2a
Create Date: 2026-10-10
"""
import sqlalchemy as sa
from alembic import op


revision = "2e834b6c9171"
down_revision = "5df3b1a74c2a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lecture_progress",
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("lecture_id", sa.String(length=128), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lecture_id"], ["lecture_notes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("owner_id", "lecture_id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_general_ci",
    )


def downgrade():
    op.drop_table("lecture_progress")
