"""At-least-once delivery, transactional receipts, retry backoff and dead letters."""

import json
import logging
import time
from datetime import timedelta

import boto3
from pywebpush import WebPushException, webpush
from sqlalchemy import select

from .config import settings
from .db import SessionLocal, now
from .models import Media, Notification, Outbox, PushSubscription, Receipt, ShareCard, User

log = logging.getLogger("civicquest.worker")


def handle(db, event):
    if event.kind == "process_report":
        from .reports import process_report

        process_report(db, event.payload["report_id"])
    elif event.kind == "hotspots":
        from .attention import rebuild_hotspots

        rebuild_hotspots(db)
    elif event.kind == "share_card":
        from .sharing import render_card

        render_card(db, db.get(ShareCard, event.payload["id"]))
    elif event.kind == "classify_draft":
        from .media import classify

        for m in db.scalars(
            select(Media).where(Media.report_id == event.payload["report_id"], Media.state == "processed")
        ):
            m.flags = classify(m)
    elif event.kind == "push":
        cfg = settings()
        if not cfg.vapid_private_key:
            return
        n = db.get(Notification, event.payload["notification_id"])
        if not n:
            return
        recipient = db.get(User, n.user_id)
        if not recipient or not recipient.notify_push:
            return
        for s in list(db.scalars(select(PushSubscription).where(PushSubscription.user_id == n.user_id))):
            try:
                webpush(
                    subscription_info={"endpoint": s.endpoint, "keys": s.keys},
                    data=json.dumps(
                        {
                            "title": "CivicQuest update",
                            "body": "You have a new update. Open CivicQuest to view it.",
                            "href": "/notifications",
                            "tag": n.id,
                        }
                    ),
                    vapid_private_key=cfg.vapid_private_key,
                    vapid_claims={"sub": cfg.vapid_subject},
                    timeout=10,
                )
            except WebPushException as exc:
                if exc.response is not None and exc.response.status_code in {404, 410}:
                    db.delete(s)
                else:
                    raise
    else:
        raise ValueError("Unknown job kind")


def process(event_id):
    try:
        with SessionLocal.begin() as db:
            e = db.scalar(select(Outbox).where(Outbox.id == event_id).with_for_update())
            if not e or db.get(Receipt, event_id) or e.state == "dead":
                return True
            handle(db, e)
            db.add(Receipt(event_id=e.id))
            e.state = "complete"
            e.completed_at = now()
            e.error = None
        return True
    except Exception as exc:
        with SessionLocal.begin() as db:
            e = db.scalar(select(Outbox).where(Outbox.id == event_id).with_for_update())
            if e:
                e.attempts += 1
                e.error = type(exc).__name__
                e.state = "dead" if e.attempts >= 5 else "pending"
                e.available_at = now() + timedelta(seconds=min(300, 2**e.attempts))
                e.dispatched_at = None
        log.error(json.dumps({"event": "job_failed", "id": event_id, "error_type": type(exc).__name__}))
        return False


def sqs():
    cfg = settings()
    kwargs = {"region_name": cfg.aws_region}
    if cfg.sqs_endpoint:
        kwargs.update(endpoint_url=cfg.sqs_endpoint, aws_access_key_id="local", aws_secret_access_key="local")
    return boto3.client("sqs", **kwargs)


def dispatch(client):
    with SessionLocal.begin() as db:
        due = list(
            db.scalars(
                select(Outbox)
                .where(
                    Outbox.state.in_(["pending", "dispatched"]),
                    Outbox.available_at <= now(),
                    (Outbox.dispatched_at.is_(None)) | (Outbox.dispatched_at < now() - timedelta(minutes=5)),
                )
                .order_by(Outbox.created_at)
                .limit(20)
                .with_for_update(skip_locked=True)
            )
        )
        for e in due:
            client.send_message(QueueUrl=settings().queue_url, MessageBody=json.dumps({"event_id": e.id}))
            e.state = "dispatched"
            e.dispatched_at = now()


def drain(max_jobs=100):
    count = 0
    while count < max_jobs:
        with SessionLocal() as db:
            ids = list(
                db.scalars(
                    select(Outbox.id).where(Outbox.state == "pending", Outbox.available_at <= now()).limit(20)
                )
            )
        if not ids:
            break
        for eid in ids:
            process(eid)
            count += 1
    return count


def main():
    logging.basicConfig(level=logging.INFO)
    client = sqs() if settings().queue_mode == "sqs" else None
    while True:
        try:
            if client:
                dispatch(client)
                response = client.receive_message(
                    QueueUrl=settings().queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=10,
                    VisibilityTimeout=120,
                )
                for m in response.get("Messages", []):
                    if process(json.loads(m["Body"])["event_id"]):
                        client.delete_message(QueueUrl=settings().queue_url, ReceiptHandle=m["ReceiptHandle"])
            else:
                drain()
                time.sleep(1)
        except Exception as exc:
            log.error(json.dumps({"event": "worker_loop_failed", "error_type": type(exc).__name__}))
            time.sleep(3)


if __name__ == "__main__":
    main()
