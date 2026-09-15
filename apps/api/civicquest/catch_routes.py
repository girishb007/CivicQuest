import re
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select

from . import schemas
from .auth import registered
from .common import audit, fail
from .db import get_db, now
from .geo import coords, point
from .media import Storage, authorize_upload, classify, complete_catch_upload
from .models import CatchCaptureSession, Category, Media, Report, User

router = APIRouter(prefix="/api/v1")


def owned_session(db, session_id, user, lock=False):
    query = select(CatchCaptureSession).where(CatchCaptureSession.id == session_id)
    session = db.scalar(query.with_for_update() if lock else query)
    if not session or session.user_id != user.id:
        fail("NOT_FOUND", "Live capture session not found", 404)
    if session.expires_at < now() or session.used_at:
        fail("CAPTURE_SESSION_EXPIRED", "Start a new live capture session", 410)
    return session


@router.post("/catches/capture-sessions")
def start_capture(
    body: schemas.Point,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
):
    if not user.handle:
        fail("PUBLIC_PROFILE_REQUIRED", "Create a public handle before posting a Civic Catch", 403)
    if body.accuracy_m is None:
        fail("LOCATION_ACCURACY_REQUIRED", "Live capture requires GPS accuracy", 422)
    session = CatchCaptureSession(
        user_id=user.id,
        location=point(body.lat, body.lng),
        accuracy_m=body.accuracy_m,
        expires_at=now() + timedelta(minutes=10),
    )
    db.add(session)
    db.flush()
    audit(db, user.id, "catch_capture_session", session.id, "started")
    return {
        "id": session.id,
        "server_started_at": session.created_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
        "location": {"lat": body.lat, "lng": body.lng, "accuracy_m": body.accuracy_m},
    }


@router.post("/catches/capture-sessions/{session_id}/media/presign")
def catch_presign(
    session_id: str,
    body: schemas.CatchUpload,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
):
    owned_session(db, session_id, user)
    existing = db.scalar(select(Media).where(Media.capture_session_id == session_id))
    if existing:
        fail("CAPTURE_MEDIA_EXISTS", "This live session already has media", 409)
    return authorize_upload(db, user, body, capture_session_id=session_id)


@router.post("/catches/capture-sessions/{session_id}/media/{media_id}/complete")
def catch_complete(
    session_id: str,
    media_id: str,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
):
    owned_session(db, session_id, user)
    media = db.scalar(select(Media).where(Media.id == media_id).with_for_update())
    if not media or media.capture_session_id != session_id:
        fail("NOT_FOUND", "Capture media not found", 404)
    complete_catch_upload(db, media, user)
    return {"id": media.id, "state": media.state, "kind": "video" if media.content_type.startswith("video/") else "photo"}


@router.post("/catches/capture-sessions/{session_id}/finalize")
def finalize_catch(
    session_id: str,
    body: schemas.CatchFinalize,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
):
    session = owned_session(db, session_id, user, True)
    if re.search(r"(?:@\w+)|(?:\+?\d[\d\s-]{7,}\d)|(?:[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,})", body.description):
        fail("PERSONAL_INFORMATION", "Remove names, handles, phone numbers and email addresses", 422)
    category = db.get(Category, body.category)
    if not category or category.report_type != "civic_catch":
        fail("INVALID_CATEGORY", "Choose a supported Civic Catch category")
    media = db.scalar(select(Media).where(Media.capture_session_id == session.id))
    if not media or media.state != "processed":
        fail("MEDIA_PROCESSING", "Finish processing the live capture before posting", 409)
    safety = (
        classify(media)
        if not media.content_type.startswith("video/")
        else {"safe": False, "flags": ["video_safety_provider_unavailable"]}
    )
    media.flags = {**media.flags, "safety_result": safety}
    location = coords(session.location)
    report = Report(
        reporter_id=user.id,
        report_type="civic_catch",
        category=category.code,
        title=category.name,
        description=body.description,
        location=point(location["lat"], location["lng"]),
        accuracy_m=session.accuracy_m,
        address=body.address,
        status="open",
        visibility="public" if safety.get("safe") else "pending",
        severity=1,
        finalized_at=now(),
    )
    db.add(report)
    db.flush()
    media.report_id = report.id
    session.report_id = report.id
    session.used_at = now()
    audit(
        db,
        user.id,
        "report",
        report.id,
        "catch_published" if report.visibility == "public" else "catch_processing_review",
    )
    return {"id": report.id, "visibility": report.visibility, "status": report.status, "xp": 0}


def catch_data(db, report):
    media = db.scalar(select(Media).where(Media.report_id == report.id, Media.state == "processed"))
    author = db.get(User, report.reporter_id)
    location = coords(report.location)
    return {
        "id": report.id,
        "public_code": report.public_code,
        "description": report.description,
        "category": report.category,
        "captured_at": report.finalized_at.isoformat(),
        "location": {**location, "address": report.address},
        "author": author.handle,
        "media": {
            "url": f"/api/v1/media/{media.id}/view",
            "kind": "video" if media.content_type.startswith("video/") else "photo",
            "poster_url": f"/api/v1/catches/{report.id}/poster" if media.flags.get("poster_key") else None,
            "duration_seconds": media.flags.get("duration_seconds"),
        },
    }


@router.get("/profiles/{handle}/catches")
def profile_catches(handle: str, db=Depends(get_db, scope="function")):
    author = db.scalar(select(User).where(User.handle == handle, User.status == "active"))
    if not author:
        fail("NOT_FOUND", "Public profile not found", 404)
    items = db.scalars(
        select(Report)
        .where(
            Report.reporter_id == author.id,
            Report.report_type == "civic_catch",
            Report.visibility == "public",
        )
        .order_by(Report.finalized_at.desc())
    )
    return {"items": [catch_data(db, item) for item in items]}


@router.get("/catches/{report_id}/poster")
def catch_poster(report_id: str, db=Depends(get_db, scope="function")):
    report = db.get(Report, report_id)
    media = db.scalar(select(Media).where(Media.report_id == report_id)) if report else None
    if not report or report.visibility != "public" or not media or not media.flags.get("poster_key"):
        fail("NOT_FOUND", "Catch poster not available", 404)
    from fastapi import Response

    return Response(Storage().get(media.flags["poster_key"]), media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@router.delete("/catches/{report_id}")
def remove_catch(report_id: str, user=Depends(registered), db=Depends(get_db, scope="function")):
    report = db.scalar(select(Report).where(Report.id == report_id).with_for_update())
    if not report or report.report_type != "civic_catch" or report.reporter_id != user.id:
        fail("NOT_FOUND", "Civic Catch not found", 404)
    report.visibility = "removed"
    media = db.scalar(select(Media).where(Media.report_id == report.id))
    if media and media.public_key:
        Storage().delete(media.public_key)
        Storage().delete(media.flags.get("poster_key"))
        media.public_key = None
    audit(db, user.id, "report", report.id, "catch_removed")
    return {"removed": True}
