"""Add a course-platform link to assignments."""
import sqlalchemy as sa
from alembic import op


revision = "28e42173f0ab"
down_revision = "c1f8d20a6e43"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assignment", sa.Column("external_url", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("assignment", "external_url")
