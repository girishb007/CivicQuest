"""Require explicit review before displaying representative records."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"


def upgrade():
    op.add_column("representatives", sa.Column("reviewed", sa.Boolean(), nullable=False,
                                              server_default=sa.false()))


def downgrade():
    op.drop_column("representatives", "reviewed")
