"""Ordered public-report index for feeds and radius queries."""
from alembic import op
from sqlalchemy import text

revision = '0002'
down_revision = '0001'


def upgrade():
    op.create_index('report_public_recent', 'reports', ['created_at', 'id'],
                    postgresql_where=text("visibility = 'public' AND duplicate_of IS NULL AND status NOT IN ('draft','processing','rejected')"))


def downgrade():
    op.drop_index('report_public_recent', table_name='reports')
