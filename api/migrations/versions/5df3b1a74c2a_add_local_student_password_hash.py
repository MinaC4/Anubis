"""Add password hashes for local student accounts."""
from alembic import op
import sqlalchemy as sa


revision = "5df3b1a74c2a"
down_revision = "28e42173f0ab"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("local_password_hash", sa.String(length=512), nullable=True))


def downgrade():
    op.drop_column("user", "local_password_hash")
