import secrets
from datetime import timedelta

from fastapi import Depends, Request, Response
from sqlalchemy import select

from .common import digest, fail
from .config import settings
from .db import get_db, now
from .models import Session, User


def new_session(db, user, response: Response):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    ttl = timedelta(hours=8) if user.role != "citizen" else timedelta(days=30)
    session = Session(
        user_id=user.id, token_hash=digest(token), csrf_hash=digest(csrf), expires_at=now() + ttl
    )
    db.add(session)
    secure = settings().origin.startswith("https://")
    response.set_cookie(
        "cq_session",
        token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=int(ttl.total_seconds()),
        path="/",
    )
    response.set_cookie(
        "cq_csrf",
        csrf,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=int(ttl.total_seconds()),
        path="/",
    )
    return session


def optional_user(request: Request, db=Depends(get_db, scope="function")):
    token = request.cookies.get("cq_session", "")
    session = (
        db.scalar(
            select(Session).where(
                Session.token_hash == digest(token), Session.revoked.is_(False), Session.expires_at > now()
            )
        )
        if token
        else None
    )
    request.state.session = session
    if not session:
        return None
    user = db.get(User, session.user_id)
    if not user or user.status != "active" or user.merged_into:
        return None
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        csrf = request.headers.get("x-csrf-token", "")
        if not secrets.compare_digest(digest(csrf), session.csrf_hash):
            fail("CSRF_FAILED", "Refresh the page and try again", 403)
    return user


def current_user(user=Depends(optional_user)):
    if not user:
        fail("SESSION_REQUIRED", "Start a guest session to continue", 401)
    return user


def registered(user=Depends(current_user)):
    if user.identity_type != "registered":
        fail("ACCOUNT_REQUIRED", "Save your progress with Google to continue", 403)
    return user


def moderator(user=Depends(registered)):
    if user.role not in {"moderator", "admin"}:
        fail("FORBIDDEN", "Moderator access required", 403)
    return user


def admin(user=Depends(registered)):
    if user.role != "admin":
        fail("FORBIDDEN", "Admin access required", 403)
    return user
