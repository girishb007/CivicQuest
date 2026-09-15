from alembic import context
from sqlalchemy import create_engine, pool
from civicquest.config import settings
from civicquest.db import Base
from civicquest import models  # noqa: F401

def run():
    with create_engine(settings().database_url, poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
run()
