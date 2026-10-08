"""Add external course content links to lecture notes."""
import sqlalchemy as sa
from alembic import op


revision = "c1f8d20a6e43"
down_revision = "a4d1cf1f2e79"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lecture_notes", sa.Column("external_url", sa.Text(), nullable=True))
    op.alter_column(
        "lecture_notes",
        "static_file_id",
        existing_type=sa.String(length=36),
        existing_nullable=False,
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "lecture_notes",
        "static_file_id",
        existing_type=sa.String(length=36),
        existing_nullable=True,
        nullable=False,
    )
    op.drop_column("lecture_notes", "external_url")
