"""Optional character portraits; existing citizens keep their initials."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"


def upgrade():
    op.add_column("users", sa.Column("portrait_id", sa.String(32), nullable=True))


def downgrade():
    op.drop_column("users", "portrait_id")
