"""Admin-managed ward targets, with progress derived from accepted outcomes."""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"


def upgrade():
    op.create_table("ward_goals",
                    sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("created_at", sa.DateTime(timezone=True)),
                    sa.Column("area_id", sa.String(36), sa.ForeignKey("administrative_areas.id"), nullable=False),
                    sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
                    sa.Column("title", sa.String(160), nullable=False),
                    sa.Column("target", sa.Integer(), nullable=False),
                    sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("status", sa.String(), nullable=False),
                    sa.CheckConstraint("target > 0"), sa.CheckConstraint("ends_at > starts_at"),
                    sa.CheckConstraint("status in ('draft','published','cancelled')"))
    op.create_index("ix_ward_goals_area_id", "ward_goals", ["area_id"])
    op.create_index("ix_ward_goals_created_at", "ward_goals", ["created_at"])


def downgrade():
    op.drop_table("ward_goals")
