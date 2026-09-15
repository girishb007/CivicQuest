from datetime import date, timedelta
from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from sqlalchemy import select

from . import schemas
from .auth import admin
from .common import audit, fail
from .db import get_db, now
from .models import Area, Authority, CommunityGroup, Officer

router = APIRouter(prefix="/api/v1")


def safe_url(value, field="link"):
    if value and urlparse(value).scheme not in {"https", "tel", "mailto"}:
        fail("INVALID_LINK", f"{field} must use HTTPS, telephone or email")
    return value


def group_data(db, group):
    area = db.get(Area, group.area_id) if group.area_id else None
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "coverage": group.coverage_text,
        "area": {"id": area.id, "name": area.name} if area else None,
        "contact_url": group.contact_url,
        "provenance": {
            "source_name": group.source_name,
            "source_url": group.source_url,
            "verified_at": group.verified_at.isoformat(),
            "review_due": group.verified_at <= now() - timedelta(days=90),
        },
        "statistics": group.statistics,
    }


def admin_group_data(db, group):
    data = group_data(db, group)
    return {**data, "area_id": group.area_id, "coverage_text": group.coverage_text,
            "source_url": group.source_url, "source_name": group.source_name,
            "verified_at": group.verified_at.isoformat(), "reviewed": group.reviewed,
            "status": group.status}


@router.get("/community-groups")
def groups(area_id: str | None = None, db=Depends(get_db, scope="function")):
    query = select(CommunityGroup).where(
        CommunityGroup.reviewed.is_(True), CommunityGroup.status == "active"
    )
    if area_id:
        query = query.where(CommunityGroup.area_id == area_id)
    return {
        "items": [group_data(db, item) for item in db.scalars(query.order_by(CommunityGroup.name))]
    }


@router.get("/community-groups/{group_id}")
def group(group_id: str, db=Depends(get_db, scope="function")):
    item = db.get(CommunityGroup, group_id)
    if not item or not item.reviewed or item.status != "active":
        fail("NOT_FOUND", "Community Group not available", 404)
    return group_data(db, item)


@router.get("/admin/community-groups")
def admin_groups(user=Depends(admin), db=Depends(get_db, scope="function")):
    del user
    return {"items": [admin_group_data(db, item) for item in db.scalars(
        select(CommunityGroup).order_by(CommunityGroup.status, CommunityGroup.name))]}


@router.post("/admin/community-groups")
def create_group(
    body: schemas.CommunityGroupInput,
    user=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    safe_url(body.contact_url, "Contact link")
    safe_url(body.source_url, "Source link")
    if body.area_id and not db.get(Area, body.area_id):
        fail("INVALID_AREA", "Choose an existing administrative area")
    item = CommunityGroup(**body.model_dump())
    db.add(item)
    db.flush()
    audit(db, user.id, "community_group", item.id, "created")
    return group_data(db, item)


@router.put("/admin/community-groups/{group_id}")
def update_group(
    group_id: str,
    body: schemas.CommunityGroupInput,
    user=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    item = db.scalar(select(CommunityGroup).where(CommunityGroup.id == group_id).with_for_update())
    if not item:
        fail("NOT_FOUND", "Community Group not found", 404)
    safe_url(body.contact_url, "Contact link")
    safe_url(body.source_url, "Source link")
    if body.area_id and not db.get(Area, body.area_id):
        fail("INVALID_AREA", "Choose an existing administrative area")
    before = admin_group_data(db, item)
    for key, value in body.model_dump().items():
        setattr(item, key, value)
    db.flush()
    audit(db, user.id, "community_group", item.id, "updated", before=before,
          after=admin_group_data(db, item))
    return admin_group_data(db, item)


def officer_data(officer):
    return {
        "id": officer.id,
        "name": officer.name,
        "title": officer.title,
        "department": officer.department,
        "area_id": officer.area_id,
        "category_family": officer.category_family,
        "reason": officer.reason,
        "source_url": officer.source_url,
        "verified_at": officer.verified_at.isoformat(),
        "effective_to": officer.effective_to.isoformat() if officer.effective_to else None,
        "reviewed": officer.reviewed,
        "contacts": {
            "phone": officer.phone,
            "whatsapp": officer.whatsapp,
            "email": officer.email,
            "official": officer.official_url,
        },
    }


@router.get("/officers")
def officers(
    area_id: str | None = None,
    family: str | None = None,
    db=Depends(get_db, scope="function")