from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# Interactive spatial reads should not spawn multiple PostgreSQL workers per
# citizen request; under concurrency their startup overhead dominates latency.
engine = create_engine(
    settings().database_url,
    pool_pre_ping=True,
    connect_args={"options": "-c max_parallel_workers_per_gather=0"},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
