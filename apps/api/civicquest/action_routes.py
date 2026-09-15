import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select

from . import geo, progress, schemas
from .auth import admin, optional_user, registered
from .common import audit, digest, fail, mutation, notify, user_ids
from .db import get_db, now
from .media import authorize_upload
from .models import Challenge, CivicAction, Media, Participation, User, XPEvent

router = APIRouter(prefix="/api/v1")


def get_action(db, aid, user=None, locked=False):
    query = select(CivicAction).where(CivicAction.id == aid)
    if locked:
        query = query.with_for_update()
    a = db.scalar(query)
    if not a or (a.status == "draft" and not (user and user.role == "admin")):
        fail("NOT_FOUND", "Civic Action not found", 404)
    return a


def action_data(db, a, user=None):
    p = db.get(Participation, (a.id, user.id)) if user else None
    return {
        "id": a.id,
        "title": a.title,
        "description": a.description,
        "organizer": a.organizer,
        "location_name": a.location_name,
        **geo.coords(a.location),
        "starts_at": a.starts_at.isoformat(),
        "ends_at": a.ends_at.isoformat(),
        "capacity": a.capacity,
        "participants": db.scalar(
            select(func.count()).select_from(Participation).where(Participation.action_id == a.id)
        ),
        "status": a.status,
        "xp": 120,
        "demo": a.demo,
        "participation": {"state": p.state, "checked_in": bool(p.checked_in_at)} if p else None,
    }


@router.get("/civic-actions")
def actions(user=Depends(optional_user), db=Depends(get_db, scope="function")):
    query = select(CivicAction).where(CivicAction.status != "draft").order_by(CivicAction.starts_at)
    return {"items": [action_data(db, a, user) for a in db.scalars(query.limit(100))]}


@router.get("/civic-actions/{aid}")
def action(aid: str, user=Depends(optional_user), db=Depends(get_db, scope="function")):
    return action_data(db, get_action(db, aid, user), user)


@router.post("/admin/actions")
def create_action(
    body: schemas.ActionInput,
    user=Depends(admin),
    db=Depends(get_db, scope="function"),
    idempotency_key: str | None = Header(default=None),
):
    def create():
        geo.coverage(db, body.lat, body.lng)
        a = CivicAction(
            created_by=user.id,
            location=geo.point(body.lat, body.lng),
            **body.model_dump(exclude={"lat", "lng", "accuracy_m"}),
        )
        db.add(a)
        db.flush()
        audit(db, user.id, "action", a.id, "created")
        return {"id": a.id}

    return mutation(db, user, "action_create", idempotency_key, body.model_dump(mode="json"), create)


@router.patch("/admin/actions/{aid}")
def edit_action(
    aid: str, body: schemas.ActionInput, user=Depends(admin), db=Depends(get_db, scope="function")
):
    a = get_action(db, aid, user, True)
    geo.coverage(db, body.lat, body.lng)
    count = db.scalar(select(func.count()).select_from(Participation).where(Participation.action_id == aid))
    if body.capacity < count:
        fail("CAPACITY_TOO_SMALL", "Capacity cannot be below existing participants", 409)
    for key, value in body.model_dump(exclude={"lat", "lng", "accuracy_m"}).items():
        setattr(a, key, value)
    a.location = geo.point(body.lat, body.lng)
    audit(db, user.id, "action", aid, "updated", after={"status": a.status})
    if a.status == "cancelled":
        for p in db.scalars(select(Participation).where(Participation.action_id == aid)):
            notify(
                db,
                p.user_id,
                "Civic Action cancelled",
                a.title,
                "/actions/" + aid,
                "cancelled:" + aid + ":" + p.user_id,
            )
    return action_data(db, a, user)


@router.post("/civic-actions/{aid}/join")
def join(aid: str, user=Depends(registered), db=Depends(get_db, scope="function")):
    a = get_action(db, aid, user, True)
    p = db.get(Participation, (aid, user.id))
    if p:
        return {"state": p.state}
    if a.status != "published" or a.ends_at < now():
        fail("ACTION_CLOSED", "This event is not accepting participants", 409)
    count = db.scalar(select(func.count()).select_from(Participation).where(Participation.action_id == aid))
    if count >= a.capacity:
        fail("ACTION_FULL", "This event has reached capacity", 409)
    db.add(Participation(action_id=aid, user_id=user.id))
    audit(db, user.id, "action", aid, "joined")
    return {"state": "joined"}


@router.post("/civic-actions/{aid}/check-in/challenge")
def challenge(aid: str, user=Depends(registered), db=Depends(get_db, scope="function")):
    get_action(db, aid, user)
    if not db.get(Participation, (aid, user.id)):
        fail("JOIN_FIRST", "Join this event before checking in")
    token = secrets.token_urlsafe(32)
    db.add(
        Challenge(
            action_id=aid, user_id=user.id, token_hash=digest(token), expires_at=now() + timedelta(minutes=5)
        )
    )
    return {"challenge": token, "expires_in": 300}


@router.post("/civic-actions/{aid}/check-in")
def checkin(aid: str, body: schemas.Checkin, user=Depends(registered), db=Depends(get_db, scope="function")):
    a = get_action(db, aid, user, True)
    p = db.get(Participation, (aid, user.id))
    if not p:
        fail("JOIN_FIRST", "Join this event first")
    c = db.scalar(
        select(Challenge)
        .where(
            Challenge.action_id == aid,
            Challenge.user_id == user.id,
            Challenge.token_hash == digest(body.challenge),
            Challenge.used.is_(False),
            Challenge.expires_at > now(),
        )
        .with_for_update()
    )
    if not c:
        fail("CHECKIN_CHALLENGE_INVALID", "Request a fresh check-in challenge", 409)
    if p.checked_in_at:
        fail("ALREADY_CHECKED_IN", "You already checked in", 409)
    if a.status != "published" or not (
        a.starts_at - timedelta(minutes=30) <= now() <= a.ends_at + timedelta(minutes=60)
    ):
        fail("OUTSIDE_EVENT_WINDOW", "Check-in is only available around the event time")
    if body.accuracy_m is None or body.accuracy_m > 50:
        fail("LOCATION_INACCURATE", "Wait for GPS accuracy of 50 metres or better")
    if not db.scalar(
        select(func.ST_DWithin(CivicAction.location, geo.point(body.lat, body.lng), 100)).where(
            CivicAction.id == aid
        )
    ):
        fail("OUTSIDE_GEOFENCE", "Move within 100 metres of the event")
    c.used = True
    p.checked_in_at = now()
    p.state = "checked_in"
    audit(db, user.id, "action", aid, "checked_in")
    return {"state": p.state}


@router.post("/admin/actions/{aid}/participants/{participant_id}/check-in")
def manual_checkin(
    aid: str,
    participant_id: str,
    body: schemas.Reason,
    user=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    a = get_action(db, aid, user, True)
    p = db.get(Participation, (aid, participant_id))
    if not p or a.status == "cancelled":
        fail("NOT_FOUND", "Active participation not found", 404)
    if participant_id == user.id:
        fail("SELF_APPROVAL", "Another admin must approve your participation", 403)
    if p.checked_in_at:
        return {"state": p.state}
    p.checked_in_at = now()
    p.state = "checked_in"
    audit(db, user.id, "action", aid, "manual_checkin", body.reason, after={"participant_id": participant_id})
    return {"state": p.state}


@router.post("/civic-actions/{aid}/proof/presign")
def proof_upload(
    aid: str, body: schemas.Upload, user=Depends(registered), db=Depends(get_db, scope="function")
):
    a = get_action(db, aid, user)
    p = db.get(Participation, (aid, user.id))
    if not p or not p.checked_in_at or p.state in {"verified", "rejected"} or a.status == "cancelled":
        fail("PROOF_UNAVAILABLE", "Check in before uploading evidence")
    if body.role not in {"before", "after", "team"}:
        fail("INVALID_PROOF_ROLE", "Choose before, after, or team proof")
    if (
        db.scalar(
            select(func.count()).select_from(Media).where(Media.action_id == aid, Media.owner_id == user.id)
        )
        >= 6
    ):
        fail("PHOTO_LIMIT", "Use at most six proof photos")
    return authorize_upload(db, user, body, action_id=aid)


@router.post("/civic-actions/{aid}/complete")
def complete(
    aid: str,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
    idempotency_key: str | None = Header(default=None),
):
    def submit():
        a = get_action(db, aid, user, True)
        p = db.get(Participation, (aid, user.id))
        if not p or not p.checked_in_at or a.status == "cancelled":
            fail("CHECKIN_REQUIRED", "Check in before submitting proof")
        roles = set(
            db.scalars(
                select(Media.role).where(
                    Media.action_id == aid, Media.owner_id == user.id, Media.state == "processed"
                )
            )
        )
        if not {"before", "after"}.issubset(roles):
            fail("PROOF_REQUIRED", "Upload both before and after photos")
        if p.state not in {"verified", "rejected"}:
            p.state = "pending"
        return {"state": p.state}

    return mutation(db, user, "action_complete", idempotency_key, {"id": aid}, submit)


@router.get("/admin/actions/{aid}/participants")
def participants(aid: str, user=Depends(admin), db=Depends(get_db, scope="function")):
    get_action(db, aid, user)
    return {
        "items": [
            {
                "user_id": p.user_id,
                "name": db.get(User, p.user_id).display_name,
                "state": p.state,
                "checked_in": bool(p.checked_in_at),
                "media": [
                    {"id": m.id, "role": m.role, "url": f"/api/v1/media/{m.id}/view"}
                    for m in db.scalars(
                        select(Media).where(
                            Media.action_id == aid, Media.owner_id == p.user_id, Media.state == "processed"
                        )
                    )
                ],
            }
            for p in db.scalars(select(Participation).where(Participation.action_id == aid))
        ]
    }


@router.post("/admin/actions/{aid}/verify/{participant_id}")
def approve_participant(
    aid: str,
    participant_id: str,
    body: schemas.Decision,
    user=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    a = get_action(db, aid, user, True)
    p = db.get(Participation, (aid, participant_id))
    if not p:
        fail("NOT_FOUND", "Participation not found", 404)
    if participant_id in user_ids(db, user.id):
        fail("SELF_APPROVAL", "Another admin must verify your participation", 403)
    if p.state == "verified" and body.approved:
        return {"state": "verified"}
    if p.state not in {"pending", "verified"} or (body.approved and a.status == "cancelled"):
        fail("PROOF_NOT_READY", "Participation must have submitted proof", 409)
    p.state = "verified" if body.approved else "rejected"
    p.reviewed_by = user.id
    p.review_reason = body.reason
    if body.approved:
        source = aid
        for event, points in [("action_checkin", 20), ("action_completed", 50), ("action_impact", 50)]:
            progress.award(db, participant_id, event, "action", source, points, capped=False)
        progress.rebuild_progress(db, participant_id)
    else:
        for event in db.scalars(
            select(XPEvent).where(
                XPEvent.user_id.in_(user_ids(db, participant_id)),
                XPEvent.source_type == "action",
                XPEvent.source_id == aid,
            )
        ):
            progress.reverse(db, event, "participation_invalidated")
        progress.rebuild_progress(db, participant_id)
    audit(
        db,
        user.id,
        "action",
        aid,
        "participation_" + p.state,
        body.reason,
        after={"participant_id": participant_id},
    )
    notify(
        db,
        participant_id,
        "Civic Action proof reviewed",
        "Your participation is " + p.state,
        "/actions/" + aid,
        f"action_review:{aid}:{participant_id}:{p.state}",
    )
    return {"state": p.state}
