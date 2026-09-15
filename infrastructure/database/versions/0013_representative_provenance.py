"""Add auditable elected-representative source fields."""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"


def upgrade():
    op.add_column("representatives", sa.Column("source_name", sa.String(), nullable=True))
    op.add_column("representatives", sa.Column("source_id", sa.String(120), nullable=True))
    op.add_column("representatives", sa.Column("party", sa.String(), nullable=True))
    op.add_column("representatives", sa.Column("photo_url", sa.String(), nullable=True))
    op.add_column("representatives", sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_representatives_source_id", "representatives", ["source_id"])


def downgrade():
    op.drop_index("ix_representatives_source_id", table_name="representatives")
    for name in ("fetched_at", "photo_url", "party", "source_id", "source_name"):
        op.drop_column("representatives", name)
