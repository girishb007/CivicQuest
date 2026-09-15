"""Persist opt-in notification channels."""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"


def upgrade():
    op.add_column(
        "users",
        sa.Column("notify_report_updates", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "users",
        sa.Column("notify_action_reminders", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "users",
        sa.Column("notify_push", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("users", "notify_push")
    op.drop_column("users", "notify_action_reminders")
    op.drop_column("users", "notify_report_updates")
