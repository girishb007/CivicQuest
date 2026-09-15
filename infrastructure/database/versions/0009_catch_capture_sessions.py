"""Live-only Civic Catch capture sessions and media linkage."""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision = "0009"
down_revision = "0008"


def upgrade():
    op.create_table(
        "catch_capture_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("location", Geography("POINT", srid=4326), nullable=False),
        sa.Column("accuracy_m", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id"), unique=True),
    )
    op.create_index("ix_catch_capture_sessions_created_at", "catch_capture_sessions", ["created_at"])
    op.create_index("ix_catch_capture_sessions_user_id", "catch_capture_sessions", ["user_id"])
    op.add_column(
        "media",
        sa.Column(
            "capture_session_id",
            sa.String(36),
            sa.ForeignKey("catch_capture_sessions.id"),
        ),
    )
    op.create_index("ix_media_capture_session_id", "media", ["capture_session_id"])


def downgrade():
    op.drop_column("media", "capture_session_id")
    op.drop_table("catch_capture_sessions")
