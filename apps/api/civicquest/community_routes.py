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
    db=Depends(get_db, scope="function"),
):
    query = select(Officer).where(
        Officer.reviewed.is_(True),
        (Officer.effective_to.is_(None) | (Officer.effective_to > now())),
    )
    if area_id:
        query = query.where(Officer.area_id == area_id)
    if family:
        query = query.where(Officer.category_family == family)
    return {"items": [officer_data(item) for item in db.scalars(query.order_by(Officer.name))]}


@router.get("/officers/{officer_id}")
def officer(officer_id: str, db=Depends(get_db, scope="function")):
    item = db.get(Officer, officer_id)
    if not item or not item.reviewed or (item.effective_to and item.effective_to <= now()):
        fail("NOT_FOUND", "Officer record not available", 404)
    return officer_data(item)


@router.get("/admin/officers")
def admin_officers(user=Depends(admin), db=Depends(get_db, scope="function")):
    del user
    return {"items": [officer_data(item) for item in db.scalars(
        select(Officer).order_by(Officer.area_id, Officer.category_family, Officer.created_at))]}


@router.post("/admin/officers")
def create_officer(
    body: schemas.OfficerInput,
    user=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    for value in (body.source_url, body.official_url):
        safe_url(value, "Official link")
    item = Officer(**body.model_dump())
    db.add(item)
    db.flush()
    audit(db, user.id, "officer", item.id, "created")
    return officer_data(item)


@router.put("/admin/officers/{officer_id}")
def update_officer(
    officer_id: str,
    body: schemas.OfficerInput,
    user=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    item = db.scalar(select(Officer).where(Officer.id == officer_id).with_for_update())
    if not item:
        fail("NOT_FOUND", "Officer record not found", 404)
    if body.area_id and not db.get(Area, body.area_id):
        fail("INVALID_AREA", "Choose an existing administrative area")
    for value in (body.source_url, body.official_url):
        safe_url(value, "Official link")
    before = officer_data(item)
    for key, value in body.model_dump().items():
        setattr(item, key, value)
    db.flush()
    audit(db, user.id, "officer", item.id, "updated", before=before, after=officer_data(item))
    return officer_data(item)


def authority_data(db, item):
    area = db.get(Area, item.area_id)
    return {
        "id": item.id,
        "name": item.name,
        "department": item.department,
        "area": {"id": area.id, "name": area.name, "code": area.code} if area else None,
        "area_id": item.area_id,
        "category_family": item.category_family,
        "source_url": item.source_url,
        "effective_from": item.effective_from,
        "effective_to": item.effective_to,
        "reviewed": item.reviewed,
    }


@router.get("/authorities")
def authorities(area_id: str | None = None, family: str | None = None,
                db=Depends(get_db, scope="function")):
    query = select(Authority).where(Authority.reviewed.is_(True))
    if area_id:
        query = query.where(Authority.area_id == area_id)
    if family:
        query = query.where(Authority.category_family == family)
    today = now().date().isoformat()
    query = query.where(Authority.effective_from <= today,
                        (Authority.effective_to.is_(None) | (Authority.effective_to >= today)))
    return {"items": [authority_data(db, item) for item in db.scalars(
        query.order_by(Authority.category_family, Authority.name, Authority.id))]}


@router.get("/admin/authorities")
def admin_authorities(user=Depends(admin), db=Depends(get_db, scope="function")):
    del user
    return {"items": [authority_data(db, item) for item in db.scalars(
        select(Authority).order_by(Authority.area_id, Authority.category_family, Authority.created_at))]}


def validate_authority(db, body, authority_id=None):
    area = db.scalar(select(Area).where(Area.id == body.area_id).with_for_update())
    if not area or not area.active or area.area_type != "ward":
        fail("INVALID_AREA", "Choose an active BMC administrative ward")
    safe_url(body.source_url, "Source link")
    try:
        start = date.fromisoformat(body.effective_from)
        end = date.fromisoformat(body.effective_to) if body.effective_to else None
    except ValueError:
        fail("INVALID_EFFECTIVE_DATES", "Use valid calendar dates")
    if end and start > end:
        fail("INVALID_EFFECTIVE_DATES", "Effective start must not follow effective end")
    if body.reviewed:
        query = select(Authority).where(
            Authority.area_id == body.area_id,
            Authority.category_family == body.category_family,
            Authority.reviewed.is_(True),
            Authority.effective_from <= (body.effective_to or "9999-12-31"),
            Authority.effective_to.is_(None) | (Authority.effective_to >= body.effective_from),
        )
        if authority_id:
            query = query.where(Authority.id != authority_id)
        if db.scalar(query.limit(1)):
            fail("OWNERSHIP_RULE_OVERLAP", "Expire the existing reviewed rule before publishing another", 409)


@router.post("/admin/authorities")
def create_authority(body: schemas.AuthorityInput, user=Depends(admin),
                     db=Depends(get_db, scope="function")):
    validate_authority(db, body)
    item = Authority(**body.model_dump())
    db.add(item)
    db.flush()
    audit(db, user.id, "authority", item.id, "created", after=authority_data(db, item))
    return authority_data(db, item)


@router.put("/admin/authorities/{authority_id}")
def update_authority(authority_id: str, body: schemas.AuthorityInput,
                     user=Depends(admin), db=Depends(get_db, scope="function")):
    item = db.scalar(select(Authority).where(Authority.id == authority_id).with_for_update())
    if not item:
        fail("NOT_FOUND", "Operational ownership rule not found", 404)
    validate_authority(db, body, authority_id)
    before = authority_data(db, item)
    for key, value in body.model_dump().items():
        setattr(item, key, value)
    db.flush()
    audit(db, user.id, "authority", item.id, "updated", before=before,
          after=authority_data(db, item))
    return authority_data(db, item)
