"""Add course description and external link.

Revision ID: a4d1cf1f2e79
Revises: 5786747278fd
"""
import sqlalchemy as sa
from alembic import op


revision = "a4d1cf1f2e79"
down_revision = "5786747278fd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("course", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("course", sa.Column("course_url", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("course", "course_url")
    op.drop_column("course", "description")
