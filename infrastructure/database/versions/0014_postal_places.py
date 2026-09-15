"""Add sourced post-office points for pincode search."""

import geoalchemy2
import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"


def upgrade():
    op.create_table(
        "postal_places",
        sa.Column("pincode", sa.String(6), nullable=False),
        sa.Column("office_name", sa.String(), nullable=False),
        sa.Column("district", sa.String(), nullable=False),
        sa.Column("location", geoalchemy2.types.Geography("POINT", srid=4326), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("source_version", sa.String(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pincode", "office_name"),
    )
    op.create_index("ix_postal_places_pincode", "postal_places", ["pincode"])


def downgrade():
    op.drop_index("ix_postal_places_pincode", table_name="postal_places")
    op.drop_table("postal_places")
