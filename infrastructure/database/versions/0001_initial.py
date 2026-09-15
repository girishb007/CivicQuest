"""Initial source records and ledger integrity guards."""
from alembic import op
import json
from pathlib import Path
revision = '0001'
down_revision = None

def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    # Frozen DDL keeps this migration stable when application models evolve.
    for statement in json.loads(Path(__file__).with_name('0001_schema.json').read_text()):
        op.execute(statement)
    op.execute("""CREATE FUNCTION cq_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN RAISE EXCEPTION 'CivicQuest audit/XP history is append-only'; END; $$""")
    for table in ['xp_events', 'audit_events']:
        op.execute(f'CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION cq_immutable()')

def downgrade():
    raise RuntimeError('Initial schema downgrade would destroy civic records. Restore a backup instead.')
