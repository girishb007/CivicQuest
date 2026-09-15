import base64
import json
import secrets
from datetime import timedelta
from urllib.parse import quote, urlencode, urlparse

import httpx
from authlib.integrations.httpx_client import OAuth2Client
from authlib.jose import JsonWebToken
from fastapi import APIRouter, Depends, Header, Request, Response
from fastapi.responses import RedirectResponse
from geoalchemy2 import Geometry
from sqlalchemy import cast, delete, func, select

from . import attention, geo, progress, reports, schemas
from .auth import current_user, new_session, optional_user, registered
from .common import audit, digest, enqueue, fail, mutation, user_ids
from .config import settings
from .db import get_db, now
from .identity import link_identity
from .media import Storage, authorize_upload, complete_upload
from .models import (
    Area,
    Category,
    Dataset,
    Hotspot,
    Identity,
    Media,
    ModerationCase,
    Notification,
    OAuthState,
    PostalPlace,
    PushSubscription,
    QuestProgress,
    Report,
    Session,
    User,
    Verification,
    Vote,
    XPEvent,
)

router = APIRouter(prefix="/api/v1")


@router.get("/config")
def config(db=Depends(get_db, scope="function")):
    s = settings()
    google_ready = bool(s.google_client_id and s.google_client_secret)
    return {
        "demo_mode": s.demo_mode,
        "catches_public": s.catches_public,
        "maptiler_key": s.maptiler_key,
        # Keep the boolean for older clients and expose a structured provider
        # status so the UI can explain local setup without hiding sign-in.
        "google_enabled": google_ready,
        "google": {
            "enabled": google_ready,
            "callback_url": s.origin + "/api/v1/auth/google/callback",
        },
        "push_public_key": s.vapid_public_key,
        "categories": [
            {"code": c.code, "name": c.name, "report_type": c.report_type, "family": c.family}
            for c in db.scalars(select(Category).where(Category.active.is_(True)))
        ],
        "xp_rules": {
            "place": {"low": 15, "medium": 25, "high": 50},
            "civic_catch": 0,
            "action": 120,
        },
        "languages": ["en"],
        "portraits": schemas.PORTRAITS,
    }


@router.post("/sessions/guest")
def guest_session(response: Response, request: Request, db=Depends(get_db, scope="function")):
    token = request.cookies.get("cq_session")
    if token:
        old = db.scalar(
            select(Session).where(
                Session.token_hash == digest(token), Session.revoked.is_(False), Session.expires_at > now()
            )
        )
        if old:
            return {"id": old.user_id}
    user = User()
    db.add(user)
    db.flush()
    new_session(db, user, response)
    return {"id": user.id}


@router.get("/me")
def me(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return progress.profile(db, user)


@router.post("/auth/logout")
def logout(
    request: Request, response: Response, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    request.state.session.revoked = True
    response.delete_cookie("cq_session")
    response.delete_cookie("cq_csrf")
    return {"ok": True}


@router.post("/auth/demo/{persona}")
def demo_login(
    persona: str,
    request: Request,
    response: Response,
    user=Depends(current_user),
    db=Depends(get_db, scope="function"),
):
    if not settings().demo_mode or settings().env not in {"local", "test"}:
        fail("NOT_FOUND", "Not found", 404)
    if persona not in {"maya", "arjun", "admin", "moderator"}:
        fail("INVALID_PERSONA", "Unknown demo persona")
    target = db.scalar(select(Identity).where(Identity.provider == "demo", Identity.subject == persona))
    if not target:
        fail("DEMO_NOT_SEEDED", "Run the demo seed command", 409)
    claimed = link_identity(db, user, "demo", persona)
    request.state.session.revoked = True
    new_session(db, claimed, response)
    return progress.profile(db, claimed)


@router.post("/auth/link/google")
def google_start(request: Request, user=Depends(current_user), db=Depends(get_db, scope="function")):
    cfg = settings()
    if not cfg.google_client_id or not cfg.google_client_secret:
        fail("PROVIDER_UNAVAILABLE", "Google sign-in is not configured in this environment", 503)
    state, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    db.add(
        OAuthState(
            session_id=request.state.session.id,
            state_hash=digest(state),
            nonce=nonce,
            verifier=verifier,
            expires_at=now() + timedelta(minutes=10),
        )
    )
    challenge = base64.urlsafe_b64encode(bytes.fromhex(digest(verifier))).rstrip(b"=").decode()
    params = {
        "client_id": cfg.google_client_id,
        "redirect_uri": cfg.origin + "/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return {"url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)}


@router.get("/auth/google/callback")
def google_callback(
    state: str, code: str, request: Request, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    cfg = settings()
    stored = db.scalar(
        select(OAuthState)
        .where(
            OAuthState.state_hash == digest(state),
            OAuthState.session_id == request.state.session.id,
            OAuthState.consumed.is_(False),
            OAuthState.expires_at > now(),
        )
        .with_for_update()
    )
    if not stored:
        fail("INVALID_AUTH_STATE", "Restart Google sign-in", 400)
    stored.consumed = True
    with OAuth2Client(
        cfg.google_client_id,
        cfg.google_client_secret,
        redirect_uri=cfg.origin + "/api/v1/auth/google/callback",
        timeout=10,
    ) as client:
        token = client.fetch_token(
            "https://oauth2.googleapis.com/token", code=code, code_verifier=stored.verifier
        )
    keys = httpx.get("https://www.googleapis.com/oauth2/v3/certs", timeout=10).json()
    claims = JsonWebToken(["RS256"]).decode(
        token["id_token"],
        keys,
        claims_options={
            "iss": {"essential": True, "values": ["https://accounts.google.com", "accounts.google.com"]},
            "aud": {"essential": True, "value": cfg.google_client_id},
            "exp": {"essential": True},
            "nonce": {"essential": True, "value": stored.nonce},
        },
    )
    claims.validate(leeway=30)
    if not claims.get("email_verified"):
        fail("EMAIL_NOT_VERIFIED", "Use a verified Google account")
    target = link_identity(db, user, "google", claims["sub"], claims.get("email"), claims.get("name"))
    request.state.session.revoked = True
    response = RedirectResponse("/profile", status_code=303)
    new_session(db, target, response)
    return response


@router.get("/categories")
def categories(db=Depends(get_db, scope="function")):
    return config(db)["categories"]


@router.get("/administrative-areas/lookup")
def area_lookup(lat: float, lng: float, db=Depends(get_db, scope="function")):
    schemas.Point(lat=lat, lng=lng)
    area, matches = geo.coverage(db, lat, lng)
    return {
        "area_id": area.id if area else None,
        "ambiguous": len([a for a in matches if a.area_type == "ward"]) > 1,
        "areas": [{"id": a.id, "name": a.name, "type": a.area_type} for a in matches],
    }


@router.get("/accountability/resolve")
def resolve(lat: float, lng: float, category_id: str, db=Depends(get_db, scope="function")):
    cat = db.get(Category, category_id)
    if not cat:
        fail("INVALID_CATEGORY", "Unknown category")
    return geo.accountability(db, lat, lng, cat)


@router.get("/geography")
def geography(db=Depends(get_db, scope="function")):
    rows = db.execute(select(Area, func.ST_AsGeoJSON(Area.boundary), Dataset.synthetic)
                      .join(Dataset, Dataset.id == Area.dataset_id).where(*geo.current_areas()))
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": json.loads(g),
                "properties": {
                    "id": a.id,
                    "name": a.name,
                    "type": a.area_type,
                    "synthetic": synthetic,
                },
            }
            for a, g, synthetic in rows
        ],
    }


@router.get("/areas/{area_id}")
def area_detail(area_id: str, user=Depends(optional_user), db=Depends(get_db, scope="function")):
    return geo.area_details(db, area_id, user)


@router.get("/places/search")
def search_places(q: str = "", db=Depends(get_db, scope="function")):
    if len(q) > 100:
        fail("QUERY_TOO_LONG", "Use a shorter search")
    if settings().maptiler_key and q:
        response = httpx.get(
            "https://api.maptiler.com/geocoding/" + quote(q, safe="") + ".json",
            params={"key": settings().maptiler_key, "bbox": "72.75,18.85,73.05,19.35", "limit": 6},
            timeout=5,
        )
        response.raise_for_status()
        return {
            "items": [
                {
                    "name": f.get("place_name", f.get("text", "Mumbai")),
                    "lng": f["center"][0],
                    "lat": f["center"][1],
                }
                for f in response.json()["features"]
            ]
        }
    postal = db.execute(
        select(PostalPlace, func.ST_Y(cast(PostalPlace.location, Geometry("POINT", srid=4326))),
               func.ST_X(cast(PostalPlace.location, Geometry("POINT", srid=4326))))
        .where(PostalPlace.active.is_(True),
               (PostalPlace.pincode == q.strip()) | PostalPlace.office_name.ilike("%" + q + "%"))
        .order_by(PostalPlace.pincode, PostalPlace.office_name).limit(10)
    ) if q.strip() else []
    postal_items = [{"id": place.id, "name": f"{place.pincode} · {place.office_name}",
                     "pincode": place.pincode, "area_type": "postal_place", "lat": lat, "lng": lng,
                     "demo": False, "source_url": place.source_url} for place, lat, lng in postal]
    rows = db.execute(
        select(Area, func.ST_Y(func.ST_Centroid(Area.boundary)), func.ST_X(func.ST_Centroid(Area.boundary)))
        .where(*geo.current_areas(), Area.name.ilike("%" + q + "%"))
        .order_by(Area.name, Area.id)
        .limit(10)
    )
    area_items = [{"id": a.id, "name": a.name, "area_type": a.area_type,
                       "lat": lat, "lng": lng, "demo": db.get(Dataset, a.dataset_id).synthetic}
                      for a, lat, lng in rows]
    return {"items": (postal_items + area_items)[:10]}


def report_page(db, user, kind=None, cursor=None, limit=24, area_id=None):
    limit = max(1, min(limit, 100))
    query = select(Report).where(*reports.public_filter())
    if kind:
        query = query.where(Report.report_type == kind)
    if area_id:
        query = query.where(Report.area_id == area_id)
    if cursor:
        try:
            timestamp, rid = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            from datetime import datetime

            at = datetime.fromisoformat(timestamp)
        except Exception:
            fail("INVALID_CURSOR", "Invalid page cursor")
        query = query.where((Report.created_at < at) | ((Report.created_at == at) & (Report.id < rid)))
    rows = list(db.scalars(query.order_by(Report.created_at.desc(), Report.id.desc()).limit(limit + 1)))
    nxt = (
        base64.urlsafe_b64encode(
            json.dumps([rows[limit - 1].created_at.isoformat(), rows[limit - 1].id]).encode()
        ).decode()
        if len(rows) > limit
        else None
    )
    return {"items": reports.serialize_many(db, rows[:limit], user), "next_cursor": nxt}


@router.get("/feed/{feed}")
def feed(
    feed: str,
    cursor: str | None = None,
    area_id: str | None = None,
    limit: int = 24,
    user=Depends(optional_user),
    db=Depends(get_db, scope="function"),
):
    if feed not in {"places", "civic-catches", "trending"}:
        fail("NOT_FOUND", "Unknown feed", 404)
    return report_page(
        db,
        user,
        "place" if feed == "places" else "civic_catch" if feed == "civic-catches" else None,
        cursor,
        limit,
        area_id,
    )


@router.get("/reports")
def list_reports(
    cursor: str | None = None, user=Depends(optional_user), db=Depends(get_db, scope="function")
):
    return report_page(db, user, cursor=cursor)


@router.get("/me/reports")
def my_reports(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return {
        "items": [
            reports.serialize(db, r, user)
            for r in db.scalars(
                select(Report)
                .where(Report.reporter_id.in_(user_ids(db, user.id)))
                .order_by(Report.created_at.desc())
                .limit(100)
            )
        ]
    }


@router.get("/explore")
def explore(
    bbox: str | None = None,
    lat: float = 19.076,
    lng: float = 72.878,
    radius_m: int = 5000,
    types: str = "place,action,hotspot",
    zoom: int = 12,
    status: str = "all",
    family: str | None = None,
    user=Depends(optional_user),
    db=Depends(get_db, scope="function"),
):
    query = select(Report).where(*reports.public_filter())
    if bbox:
        try:
            a, b, c, d = map(float, bbox.split(","))
            if not (-180 <= a < c <= 180 and -90 <= b < d <= 90):
                raise ValueError()
        except ValueError:
            fail("INVALID_BOUNDS", "Use minLng,minLat,maxLng,maxLat")
        query = query.where(func.ST_Intersects(Report.location, func.ST_MakeEnvelope(a, b, c, d, 4326)))
    else:
        schemas.Point(lat=lat, lng=lng)
        query = query.where(
            func.ST_DWithin(Report.location, geo.point(lat, lng), max(100, min(radius_m, 60000)))
        )
    allowed = types.split(",")
    query = query.where(Report.report_type.in_(allowed))
    if status not in {"all", "active", "resolved"}:
        fail("INVALID_FILTER", "Choose all, active or resolved reports")
    if status != "all":
        query = query.where(Report.status == "resolved" if status == "resolved" else Report.status != "resolved")
    if family:
        query = query.join(Category).where(Category.family == family)
    matching = query.subquery()
    counts = dict(db.execute(select(matching.c.status, func.count()).group_by(matching.c.status)).all())
    total = sum(counts.values())
    return {
        "summary": {"total": total, "resolved": counts.get("resolved", 0),
                    "active": total-counts.get("resolved", 0), "limit": 200, "truncated": total > 200},
        "reports": reports.serialize_many(
            db, db.scalars(query.order_by(Report.created_at.desc(), Report.id).limit(200)), user
        ),
        "hotspots": [
            attention.hotspot_data(db, h)
            for h in db.scalars(select(Hotspot).where(Hotspot.active.is_(True)).limit(100))
        ]
        if "hotspot" in allowed
        else [],
    }


@router.post("/reports/drafts")
def draft(
    body: schemas.Draft,
    user=Depends(current_user),
    db=Depends(get_db, scope="function"),
    idempotency_key: str | None = Header(default=None),
):
    return mutation(
        db, user, "draft", idempotency_key, body.model_dump(), lambda: reports.create_draft(db, user, body)
    )


@router.patch("/reports/{report_id}")
def edit_draft(
    report_id: str, body: schemas.Draft, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    r = reports.get_report(db, report_id, user, True)
    if r.status != "draft":
        fail("DRAFT_CLOSED", "Submitted reports cannot be edited", 409)
    cat = db.get(Category, body.category)
    if not cat or cat.report_type != body.report_type:
        fail("INVALID_CATEGORY", "Choose a matching category")
    owner = geo.accountability(db, body.lat, body.lng, cat)
    r.category = body.category
    r.report_type = body.report_type
    r.title = body.title
    r.description = body.description
    r.address = body.address
    r.severity = reports.SEVERITY_TO_VALUE[body.severity]
    r.location = geo.point(body.lat, body.lng)
    r.area_id = owner["area"]["id"] if owner["area"] else None
    return {"id": r.id, "status": r.status}


@router.get("/reports/by-code/{public_code}")
def report_by_code(
    public_code: str, user=Depends(optional_user), db=Depends(get_db, scope="function")
):
    code = public_code.strip().upper()
    r = db.scalar(select(Report).where(Report.public_code == code))
    if not r:
        fail("REPORT_NOT_VISIBLE", "This report is not available", 404)
    return reports.serialize(db, reports.get_report(db, r.id, user), user, True)


@router.get("/reports/{report_id}")
def report_detail(report_id: str, user=Depends(optional_user), db=Depends(get_db, scope="function")):
    return reports.serialize(db, reports.get_report(db, report_id, user), user, True)


@router.post("/reports/{report_id}/media/presign")
def presign(
    report_id: str, body: schemas.Upload, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    r = reports.get_report(db, report_id, user, True)
    if r.status != "draft":
        fail("DRAFT_CLOSED", "Submitted evidence is immutable", 409)
    if db.scalar(select(func.count()).select_from(Media).where(Media.report_id == r.id)) >= 3:
        fail("PHOTO_LIMIT", "Use at most three photos")
    return authorize_upload(db, user, body, report_id=r.id)


@router.put("/media/{media_id}/upload")
async def upload_file(
    media_id: str,
    token: str,
    request: Request,
    user=Depends(current_user),
    db=Depends(get_db, scope="function"),
):
    if settings().storage != "filesystem":
        fail("NOT_FOUND", "Use the authorized storage URL", 404)
    m = db.scalar(select(Media).where(Media.id == media_id).with_for_update())
    if (
        not m
        or m.owner_id != user.id
        or m.state != "awaiting_upload"
        or m.upload_expires < now()
        or not secrets.compare_digest(digest(token), m.upload_token_hash)
    ):
        fail("INVALID_UPLOAD", "Upload is expired or unauthorized", 403)
    data = bytearray()
    async for part in request.stream():
        data.extend(part)
        if len(data) > min(m.size, settings().max_upload_bytes):
            fail("UPLOAD_TOO_LARGE", "Upload exceeds its authorized size", 413)
    Storage().put(m.original_key, bytes(data), m.content_type)
    return {"ok": True}


@router.post("/media/{media_id}/complete")
def finish_upload(media_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    m = db.scalar(select(Media).where(Media.id == media_id).with_for_update())
    if not m:
        fail("NOT_FOUND", "Upload not found", 404)
    complete_upload(db, m, user)
    return {"id": m.id, "state": m.state}


@router.get("/media/{media_id}/view")
def media_view(media_id: str, user=Depends(optional_user), db=Depends(get_db, scope="function")):
    m = db.get(Media, media_id)
    if not m or not m.public_key or m.state != "processed":
        fail("NOT_FOUND", "Photo not available", 404)
    allowed = bool(user and (m.owner_id in user_ids(db, user.id) or user.role in {"moderator", "admin"}))
    if m.report_id:
        media_report = db.get(Report, m.report_id)
        allowed = allowed or reports.is_public(media_report) or (
            media_report.report_type == "civic_catch"
            and media_report.visibility == "public"
            and bool(db.get(User, media_report.reporter_id).handle)
        )
    if not allowed:
        fail("NOT_FOUND", "Photo not available", 404)
    return Response(
        Storage().get(m.public_key),
        media_type=m.flags.get("public_content_type", "image/jpeg"),
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/reports/{report_id}/finalize")
def finalize(
    report_id: str,
    user=Depends(current_user),
    db=Depends(get_db, scope="function"),
    idempotency_key: str | None = Header(default=None),
):
    r = reports.get_report(db, report_id, user, True)
    return mutation(
        db, user, "finalize", idempotency_key, {"id": report_id}, lambda: reports.finalize(db, user, r)
    )


@router.get("/reports/{report_id}/processing-status")
def processing(report_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    r = reports.get_report(db, report_id, user)
    return {"id": r.id, "status": r.status, "visibility": r.visibility, "verification": r.verification}


@router.post("/reports/{report_id}/classification")
def classification(report_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    r = reports.get_report(db, report_id, user, True)
    enqueue(db, "classify_draft", {"report_id": r.id}, f"classify:{r.id}")
    return {"status": "queued", "category": r.category}


@router.post("/reports/{report_id}/upvotes")
def vote(report_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    r = reports.get_report(db, report_id, user)
    db.scalar(select(Report).where(Report.id == r.id).with_for_update())
    if not reports.is_public(r):
        fail("REPORT_NOT_PUBLIC", "This report is not open for voting", 403)
    if r.reporter_id in user_ids(db, user.id):
        fail("SELF_VOTE", "You cannot upvote your own report", 403)
    if not db.get(Vote, (r.id, user.id)):
        db.add(Vote(report_id=r.id, user_id=user.id))
    enqueue(db, "hotspots", {}, f"vote:{r.id}:{user.id}:{now().isoformat()}")
    return {"voted": True}


@router.delete("/reports/{report_id}/upvotes")
def unvote(report_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    db.execute(delete(Vote).where(Vote.report_id == report_id, Vote.user_id == user.id))
    enqueue(db, "hotspots", {}, f"unvote:{report_id}:{user.id}:{now().isoformat()}")
    return {"voted": False}


@router.post("/reports/{report_id}/verify")
def verify(
    report_id: str,
    body: schemas.VerificationInput,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
):
    r = reports.get_report(db, report_id, user)
    db.scalar(select(Report).where(Report.id == r.id).with_for_update())
    if r.report_type != "place" or not reports.is_public(r):
        fail("VERIFICATION_UNAVAILABLE", "This report requires moderator review", 403)
    if r.reporter_id in user_ids(db, user.id):
        fail("SELF_VERIFICATION", "Ask another citizen to verify", 403)
    old = db.scalar(
        select(Verification).where(Verification.report_id == r.id, Verification.user_id == user.id)
    )
    if old:
        if old.result != body.result:
            fail("ALREADY_VERIFIED", "Use the abuse or appeal flow to dispute your earlier verification", 409)
        return {"verification": r.verification}
    v = Verification(report_id=r.id, user_id=user.id, result=body.result)
    db.add(v)
    db.flush()
    if body.result != "confirmed":
        db.add(ModerationCase(report_id=r.id, user_id=user.id, kind="dispute", priority=1))
        reports.invalidate_cards(db)
        if r.verification == "community":
            progress.invalidate_report(db, r)
    else:
        dispute = db.scalar(
            select(Verification.id).where(Verification.report_id == r.id, Verification.result != "confirmed")
        )
        count = db.scalar(
            select(func.count())
            .select_from(Verification)
            .where(Verification.report_id == r.id, Verification.result == "confirmed")
        )
        if count >= 2 and not dispute:
            progress.verify_report(db, r, "community")
            reports.milestone(db, r.id, "community_verified", actor_id=user.id)
        if r.verification in {"community", "moderator"}:
            v.accepted = True
            progress.award(db, user.id, "report_verification", "report", r.id, 2)
    audit(db, user.id, "report", r.id, "community_" + body.result, public=True)
    return {"verification": r.verification}


@router.get("/hotspots")
def hotspots(db=Depends(get_db, scope="function")):
    return {
        "items": [
            attention.hotspot_data(db, h)
            for h in db.scalars(
                select(Hotspot).where(Hotspot.active.is_(True)).order_by(Hotspot.score.desc()).limit(100)
            )
        ]
    }


@router.get("/hotspots/{hotspot_id}")
def hotspot(hotspot_id: str, db=Depends(get_db, scope="function")):
    h = db.get(Hotspot, hotspot_id)
    if not h or not h.active:
        fail("NOT_FOUND", "Hotspot not available", 404)
    return attention.hotspot_data(db, h)


@router.get("/gamification/me")
def gamification(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return progress.profile(db, user)


@router.get("/users/me/xp-events")
def xp_events(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": e.id,
                "points": e.points,
                "event_type": e.event_type,
                "created_at": e.created_at.isoformat(),
            }
            for e in db.scalars(
                select(XPEvent)
                .where(XPEvent.user_id.in_(user_ids(db, user.id)))
                .order_by(XPEvent.created_at.desc())
                .limit(100)
            )
        ]
    }


@router.get("/quests")
@router.get("/quests/me")
def quests(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return {"items": progress.quests(db, user)}


@router.post("/quests/{code}/claim")
def claim_quest(code: str, user=Depends(registered), db=Depends(get_db, scope="function")):
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    q = next((q for q in progress.quests(db, user) if q["code"] == code), None)
    if not q:
        fail("NOT_FOUND", "Quest not found", 404)
    if q["completed"]:
        return {"claimed": True}
    if not q["claimable"]:
        fail("QUEST_INCOMPLETE", "Complete the verified contributions first", 409)
    db.merge(
        QuestProgress(
            user_id=user.id, code=code, period=q["period_key"], progress=q["target"], completed=True
        )
    )
    progress.award(db, user.id, "quest", "quest", code + ":" + q["period_key"], q["xp"])
    return {"claimed": True}


@router.post("/profiles/me/handle")
def set_handle(body: schemas.Handle, user=Depends(registered), db=Depends(get_db, scope="function")):
    exists = db.scalar(select(User).where(User.handle == body.handle, User.id != user.id))
    if exists:
        fail("HANDLE_TAKEN", "Choose another civic handle", 409)
    user.handle = body.handle
    user.display_name = body.display_name
    return progress.profile(db, user)


@router.put("/profiles/me/portrait")
def set_portrait(body: schemas.Portrait, user=Depends(current_user), db=Depends(get_db, scope="function")):
    # Absolute assignment is idempotent, available to guests, and cannot grant rewards.
    user.portrait_id = body.portrait_id
    return progress.profile(db, user)


@router.get("/profiles/{handle}")
def public_profile(handle: str, db=Depends(get_db, scope="function")):
    user = db.scalar(
        select(User).where(User.handle == handle, User.status == "active", User.identity_type == "registered")
    )
    if not user:
        fail("NOT_FOUND", "Profile not available", 404)
    return progress.profile(db, user, True)


@router.get("/leaderboards/{scope}")
def leaderboard(
    scope: str, period: str = "month", area_id: str | None = None, db=Depends(get_db, scope="function")
):
    if scope not in {"mumbai", "local"} or period not in {"month", "all"}:
        fail("INVALID_SCOPE", "Choose Mumbai or local, month or all")
    if scope == "local" and not area_id:
        fail("AREA_REQUIRED", "Choose an administrative ward")
    query = select(User).where(
        User.status == "active", User.identity_type == "registered", User.handle.is_not(None)
    )
    if scope == "local":
        query = query.where(User.home_area_id == area_id)
    entries = []
    for u in db.scalars(query):
        xp = select(func.coalesce(func.sum(XPEvent.points), 0)).where(XPEvent.user_id.in_(user_ids(db, u.id)))
        if period == "month":
            xp = xp.where(
                XPEvent.local_date >= now().astimezone(progress.TZ).date().replace(day=1).isoformat()
            )
        entries.append({"handle": u.handle, "display_name": u.display_name, "xp": db.scalar(xp)})
    entries.sort(key=lambda e: (-e["xp"], e["handle"]))
    return {"items": [{**e, "rank": i + 1} for i, e in enumerate(entries[:100])], "period": period}


@router.get("/civicdex")
def dex_definitions(db=Depends(get_db, scope="function")):
    return {
        "items": [
            {"code": c.code, "name": c.name, "rarity": "common" if c.report_type == "place" else "uncommon"}
            for c in db.scalars(select(Category))
        ]
    }


@router.get("/civicdex/me")
def my_dex(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return {"items": progress.profile(db, user)["civicdex"]}


@router.get("/notifications")
def notifications(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "href": n.href,
                "read": bool(n.read_at),
                "created_at": n.created_at.isoformat(),
            }
            for n in db.scalars(
                select(Notification)
                .where(Notification.user_id.in_(user_ids(db, user.id)))
                .order_by(Notification.created_at.desc())
                .limit(100)
            )
        ]
    }


@router.get("/notification-preferences")
def notification_preferences(user=Depends(current_user)):
    return {
        "report_updates": user.notify_report_updates,
        "action_reminders": user.notify_action_reminders,
        "push": user.notify_push,
    }


@router.put("/notification-preferences")
def save_notification_preferences(
    body: schemas.NotificationPreferences,
    user=Depends(current_user),
    db=Depends(get_db, scope="function"),
):
    user.notify_report_updates = body.report_updates
    user.notify_action_reminders = body.action_reminders
    user.notify_push = body.push and user.identity_type == "registered"
    audit(
        db,
        user.id,
        "user",
        user.id,
        "notification_preferences_updated",
        after={
            "report_updates": user.notify_report_updates,
            "action_reminders": user.notify_action_reminders,
            "push": user.notify_push,
        },
    )
    return notification_preferences(user)


@router.post("/notifications/{notification_id}/read")
def read_notification(notification_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    n = db.get(Notification, notification_id)
    if not n or n.user_id not in user_ids(db, user.id):
        fail("NOT_FOUND", "Notification not found", 404)
    n.read_at = now()
    return {"ok": True}


@router.post("/push/subscriptions")
def subscribe(body: schemas.Push, user=Depends(registered), db=Depends(get_db, scope="function")):
    parsed = urlparse(body.endpoint)
    allowed = (
        "fcm.googleapis.com",
        "updates.push.services.mozilla.com",
        "web.push.apple.com",
        "wns.windows.com",
    )
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not any(parsed.hostname == h or parsed.hostname.endswith("." + h) for h in allowed)
        or parsed.port not in {None, 443}
    ):
        fail("INVALID_PUSH_ENDPOINT", "Unsupported browser push endpoint")
    if set(body.keys) != {"p256dh", "auth"} or any(len(v) > 256 for v in body.keys.values()):
        fail("INVALID_PUSH_KEYS", "Invalid subscription")
    existing = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == body.endpoint))
    if existing and existing.user_id != user.id:
        fail("SUBSCRIPTION_OWNED", "Subscription already belongs to another session", 409)
    if not existing:
        db.add(PushSubscription(user_id=user.id, endpoint=body.endpoint, keys=body.keys))
    return {"ok": True}


@router.delete("/push/subscriptions/{subscription_id}")
def unsubscribe(subscription_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    db.execute(
        delete(PushSubscription).where(
            PushSubscription.id == subscription_id, PushSubscription.user_id == user.id
        )
    )
    return {"ok": True}
