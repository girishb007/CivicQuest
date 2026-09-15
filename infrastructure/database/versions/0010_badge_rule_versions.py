"""Version the twelve verified V1 badge projections."""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"


def upgrade():
    op.add_column(
        "user_badges",
        sa.Column("rule_version", sa.String(), nullable=False, server_default="v1-mobile"),
    )


def downgrade():
    op.drop_column("user_badges", "rule_version")
