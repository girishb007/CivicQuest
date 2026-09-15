"""Seen, discussion, following and moderator-operated complaint escalation."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"


def record_columns():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "seen_confirmations",
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id"), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "report_follows",
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id"), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "report_messages",
        *record_columns(),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("moderated_by", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("moderated_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("kind in ('comment','community_update')"),
        sa.CheckConstraint("state in ('published','restricted','removed')"),
    )
    op.create_index("ix_report_messages_created_at", "report_messages", ["created_at"])
    op.create_index("ix_report_messages_report_id", "report_messages", ["report_id"])
    op.create_table(
        "escalation_cases",
        *record_columns(),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("decision_reason", sa.Text()),
        sa.CheckConstraint("threshold > 0"),
        sa.CheckConstraint("state in ('review','approved','declined','handed_off','closed')"),
        sa.UniqueConstraint("report_id"),
    )
    op.create_index("ix_escalation_cases_created_at", "escalation_cases", ["created_at"])
    op.create_index("ix_escalation_cases_report_id", "escalation_cases", ["report_id"])
    op.create_table(
        "complaints",
        *record_columns(),
        sa.Column("escalation_id", sa.String(36), sa.ForeignKey("escalation_cases.id"), nullable=False),
        sa.Column("official_id", sa.String(120), unique=True),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("receipt_key", sa.String()),
        sa.Column("handed_off_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("escalation_id"),
    )
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])
    op.create_table(
        "complaint_status_events",
        *record_columns(),
        sa.Column("complaint_id", sa.String(36), sa.ForeignKey("complaints.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_note", sa.Text(), nullable=False),
        sa.Column("recorded_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_complaint_status_events_created_at", "complaint_status_events", ["created_at"])
    op.create_index("ix_complaint_status_events_complaint_id", "complaint_status_events", ["complaint_id"])


def downgrade():
    op.drop_table("complaint_status_events")
    op.drop_table("complaints")
    op.drop_table("escalation_cases")
    op.drop_table("report_messages")
    op.drop_table("report_follows")
    op.drop_table("seen_confirmations")
