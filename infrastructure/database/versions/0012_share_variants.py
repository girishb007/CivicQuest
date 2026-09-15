"""Bind share-card variants to their safe public sources."""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"


def upgrade():
    op.add_column("share_cards", sa.Column("report_id", sa.String(36), nullable=True))
    op.add_column("share_cards", sa.Column("area_id", sa.String(36), nullable=True))
    op.create_foreign_key("share_cards_report_fk", "share_cards", "reports", ["report_id"], ["id"])
    op.create_foreign_key(
        "share_cards_area_fk", "share_cards", "administrative_areas", ["area_id"], ["id"]
    )
    op.create_index("ix_share_cards_report_id", "share_cards", ["report_id"])
    op.create_index("ix_share_cards_area_id", "share_cards", ["area_id"])


def downgrade():
    op.drop_index("ix_share_cards_area_id", table_name="share_cards")
    op.drop_index("ix_share_cards_report_id", table_name="share_cards")
    op.drop_constraint("share_cards_area_fk", "share_cards", type_="foreignkey")
    op.drop_constraint("share_cards_report_fk", "share_cards", type_="foreignkey")
    op.drop_column("share_cards", "area_id")
    op.drop_column("share_cards", "report_id")
