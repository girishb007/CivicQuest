"""Account privacy and recoverable operator jobs."""

from datetime import timedelta

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select

from .auth import current_user, moderator
from .common import audit, fail, user_ids
from .config import settings
from .db import get_db, now
from .media import Storage
from .models import Dataset, Identity, Media, Outbox, PushSubscription, Report, Session, ShareCard, User

router = APIRouter(prefix="/api/v1")


@router.delete("/sessions")
def revoke_sessions(response: Response, user=Depends(current_user), db=Depends(get_db, scope="function")):
    for session in db.scalars(select(Session).where(Session.user_id.in_(user_ids(db, user.id)))):
        session.revoked = True
    response.delete_cookie("cq_session")
    response.delete_cookie("cq_csrf")
    audit(db, user.id, "user", user.id, "sessions_revoked")
    return {"revoked": True}


@router.delete("/account")
def delete_account(response: Response, user=Depends(current_user), db=Depends(get_db, scope="function")):
    ids = user_ids(db, user.id)
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    for member in db.scalars(select(User).where(User.id.in_(ids))):
        member.status = "deleted"
        member.email = None
        member.handle = None
        member.display_name = "Deleted account"
        member.portrait_id = None
    for session in db.scalars(select(Session).where(Session.user_id.in_(ids))):
        session.revoked = True
    db.execute(delete(Identity).where(Identity.user_id.in_(ids)))
    db.execute(delete(PushSubscription).where(PushSubscription.user_id.in_(ids)))
    for report in db.scalars(select(Report).where(Report.reporter_id.in_(ids))):
        report.visibility = "removed"
        report.resolved_at = report.resolved_at or now()
    for card in db.scalars(select(ShareCard).where(ShareCard.user_id.in_(ids))):
        card.state = "revoked"
    audit(db, user.id, "user", user.id, "account_deleted")
    response.delete_cookie("cq_session")
    response.delete_cookie("cq_csrf")
    return {"deleted": True, "original_retention_days": settings().original_retention_days}


@router.get("/admin/jobs")
def jobs(user=Depends(moderator), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": event.id,
                "kind": event.kind,
                "state": event.state,
                "attempts": event.attempts,
                "error_type": event.error,
                "available_at": event.available_at.isoformat(),
            }
            for event in db.scalars(
                select(Outbox).where(Outbox.state != "complete").order_by(Outbox.created_at).limit(100)
            )
        ]
    }


@router.post("/admin/jobs/{event_id}/retry")
def retry(event_id: str, user=Depends(moderator), db=Depends(get_db, scope="function")):
    event = db.scalar(select(Outbox).where(Outbox.id == event_id).with_for_update())
    if not event or event.state != "dead":
        fail("NOT_RETRYABLE", "Only a dead job can be manually retried", 409)
    event.state = "pending"
    event.attempts = 0
    event.available_at = now()
    event.dispatched_at = None
    audit(db, user.id, "job", event.id, "retried")
    return {"state": event.state}


@router.get("/admin/datasets")
def datasets(user=Depends(moderator), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "version": item.version,
                "source_url": item.source_url,
                "license": item.license,
                "reviewed": item.reviewed,
                "synthetic": item.synthetic,
                "checksum": item.checksum,
            }
            for item in db.scalars(select(Dataset).order_by(Dataset.created_at.desc()))
        ]
    }


def retain_originals(db):
    cutoff = now() - timedelta(days=settings().original_retention_days)
    store = Storage()
    count = 0
    query = (
        select(Media)
        .join(Report, Report.id == Media.report_id)
        .where(Report.resolved_at < cutoff, Media.purged_at.is_(None), Media.state == "processed")
    )
    for media in db.scalars(query.with_for_update(skip_locked=True)):
        store.delete(media.original_key)
        media.purged_at = now()
        count += 1
    return count
