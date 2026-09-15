import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


@pytest.fixture
def db():
    url = os.environ.get("CQ_TEST_DATABASE_URL")
    if not url:
        pytest.skip("CQ_TEST_DATABASE_URL must point to an isolated migrated PostGIS database")
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        assert connection.scalar(text("SELECT PostGIS_Version()"))
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()
    engine.dispose()
