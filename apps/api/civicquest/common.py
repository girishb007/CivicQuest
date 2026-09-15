import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select

from .models import Audit, Mutation, Notification, Outbox, User


def fail(code, message, status=400):
    raise HTTPException(status_code=status, detail={"code": code, "message": message})


def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def user_ids(db, user_id):
    return list(db.scalars(select(User.id).where((User.id == user_id) | (User.merged_into == user_id))))


def audit(db, actor, target_type, target_id, action, reason="", before=None, after=None, public=False):
    db.add(
        Audit(
            actor_id=actor,
            target_type=target_type,
            target_id=target_id,
            action=action,
            reason=reason,
            before=before or {},
            after=after or {},
            public=public,
        )
    )


def enqueue(db, kind, payload, key):
    existing = db.scalar(select(Outbox).where(Outbox.dedupe_key == key))
    if not existing:
        db.add(Outbox(kind=kind, payload=payload, dedupe_key=key))


def notify(db, user_id, title, body, href, key):
    if not db.scalar(select(Notification).where(Notification.dedupe_key == key)):
        item = Notification(user_id=user_id, title=title, body=body, href=href, dedupe_key=key)
        db.add(item)
        db.flush()
        enqueue(db, "push", {"notification_id": item.id}, f"push:{item.id}")


def mutation(db, user, operation, key, payload, fn):
    if not key or len(key) > 120:
        fail("IDEMPOTENCY_KEY_REQUIRED", "Supply an Idempotency-Key header")
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    hashed = digest(json.dumps(payload, sort_keys=True, default=str))
    old = db.scalar(
        select(Mutation).where(
            Mutation.user_id == user.id, Mutation.operation == operation, Mutation.key == key
        )
    )
    if old:
        if old.request_hash != hashed:
            fail("IDEMPOTENCY_CONFLICT", "This key was used for a different request", 409)
        return old.result
    result = fn()
    db.add(Mutation(user_id=user.id, operation=operation, key=key, request_hash=hashed, result=result))
    return result
