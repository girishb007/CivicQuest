from contextlib import contextmanager

from civicquest import worker
from civicquest.models import Outbox, Receipt
from sqlalchemy import select


def test_outbox_duplicate_delivery_runs_handler_once(db, monkeypatch):
    class Factory:
        @staticmethod
        @contextmanager
        def begin():
            with db.begin_nested():
                yield db

    monkeypatch.setattr(worker, "SessionLocal", Factory)
    calls = []
    monkeypatch.setattr(worker, "handle", lambda session, event: calls.append(event.id))
    event = Outbox(kind="test", payload={}, dedupe_key="test-duplicate-delivery")
    db.add(event)
    db.flush()
    assert worker.process(event.id)
    assert worker.process(event.id)
    assert calls == [event.id]
    assert db.get(Receipt, event.id)
    assert event.state == "complete"


def test_failed_job_rolls_back_domain_effects_before_retry(db, monkeypatch):
    class Factory:
        @staticmethod
        @contextmanager
        def begin():
            with db.begin_nested():
                yield db

    monkeypatch.setattr(worker, "SessionLocal", Factory)
    event = Outbox(kind="test", payload={}, dedupe_key="test-failed-delivery")
    db.add(event)
    db.flush()

    def fail(session, current):
        session.add(Outbox(kind="must_rollback", payload={}, dedupe_key="never-persist"))
        session.flush()
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(worker, "handle", fail)
    for _ in range(5):
        assert not worker.process(event.id)
    assert not db.scalar(select(Outbox).where(Outbox.dedupe_key == "never-persist"))
    assert not db.get(Receipt, event.id)
    assert event.state == "dead"
    assert event.attempts == 5
