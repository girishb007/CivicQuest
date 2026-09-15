"""Reviewed officer contacts and admin-curated Community Groups."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"


def upgrade():
    op.create_table(
        "officers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=False),
        sa.Column("area_id", sa.String(36), sa.ForeignKey("administrative_areas.id")),
        sa.Column("category_family", sa.String()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("phone", sa.String()),
        sa.Column("whatsapp", sa.String()),
        sa.Column("email", sa.String()),
        sa.Column("official_url", sa.String()),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_officers_created_at", "officers", ["created_at"])
    op.create_index("ix_officers_area_id", "officers", ["area_id"])
    op.create_table(
        "community_groups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("area_id", sa.String(36), sa.ForeignKey("administrative_areas.id")),
        sa.Column("coverage_text", sa.String(), nullable=False),
        sa.Column("contact_url", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("statistics", sa.JSON(), nullable=False),
        sa.CheckConstraint("status in ('active','inactive')"),
    )
    op.create_index("ix_community_groups_created_at", "community_groups", ["created_at"])
    op.create_index("ix_community_groups_area_id", "community_groups", ["area_id"])


def downgrade():
    op.drop_table("community_groups")
    op.drop_table("officers")
