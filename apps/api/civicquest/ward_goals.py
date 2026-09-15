"""Shared progress is a live projection, not another reward ledger or cached counter."""
from typing import Literal

from fastapi import APIRouter, Depends, Header
from geoalchemy2 import Geometry
from pydantic import AwareDatetime, BaseModel, Field, model_validator
from sqlalchemy import cast, func, select

from . import geo
from .auth import admin, optional_user
from .common import audit, fail, mutation
from .db import get_db, now
from .models import Area, Category, CivicAction, Dataset, Participation, Report, Resolution, WardGoal

router = APIRouter(prefix="/api/v1")


class GoalInput(BaseModel):
    area_id: str
    title: str = Field(min_length=3, max_length=160)
    target: int = Field(ge=1, le=10000)
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    status: Literal["draft", "published", "cancelled"] = "draft"

    @model_validator(mode="after")
    def period(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("Goal end must follow start")
        return self


def ward(db, area_id):
    area = db.scalar(select(Area).where(Area.id == area_id, Area.area_type == "ward", *geo.current_areas()))
    if not area:
        fail("WARD_NOT_AVAILABLE", "Choose a current administrative ward", 400)
    return area


def projection(db, goal):
    area = ward(db, goal.area_id)
    # Resolution dates use the accepted decision; Action dates use the completed
    # event's end. A late approval updates the appropriate historical period.
    resolved = db.scalar(select(func.count()).select_from(Report).join(Category).where(
        *geo.area_reports(area), Report.area_id == area.id, Report.status == "resolved",
        Category.family == "waste", Report.resolved_at >= goal.starts_at, Report.resolved_at < goal.ends_at,
        select(Resolution.id).where(Resolution.report_id == Report.id, Resolution.state == "verified").exists(),
    ))
    location = cast(CivicAction.location, Geometry("POINT", srid=4326))
    # Never assign an event on a shared ward edge to two ward goals.
    covering_wards = select(func.count()).select_from(Area).where(
        *geo.current_areas(), Area.area_type == "ward", func.ST_Covers(Area.boundary, location),
    ).correlate(CivicAction).scalar_subquery()
    actions = db.scalar(select(func.count()).select_from(CivicAction).where(
        CivicAction.status == "published", CivicAction.ends_at >= goal.starts_at,
        CivicAction.ends_at < goal.ends_at, CivicAction.ends_at <= now(),
        func.ST_Covers(area.boundary, location), covering_wards == 1,
        select(Participation.action_id).where(Participation.action_id == CivicAction.id,
                                              Participation.state == "verified").exists(),
    ))
    total = resolved + actions
    return {"id": goal.id, "area_id": goal.area_id, "area_name": area.name, "title": goal.title,
            "target": goal.target, "starts_at": goal.starts_at.isoformat(), "ends_at": goal.ends_at.isoformat(),
            "status": goal.status, "progress": total, "resolved_reports": resolved, "completed_actions": actions,
            "completed": total >= goal.target, "synthetic": db.get(Dataset, area.dataset_id).synthetic,
            "rule_version": "ward-outcomes-v1", "xp": 0,
            "counting_note": "Each verified waste resolution and completed, approved Civic Action counts once. "
                             "Multiple participants do not multiply an Action. Personal XP is separate."}


@router.get("/ward-goals")
def goals(area_id: str | None = None, user=Depends(optional_user), db=Depends(get_db, scope="function")):
    query = select(WardGoal).join(Area).where(*geo.current_areas()).order_by(WardGoal.starts_at.desc(), WardGoal.id)
    if not user or user.role != "admin":
        query = query.where(WardGoal.status == "published")
    if area_id:
        query = query.where(WardGoal.area_id == area_id)
    return {"items": [projection(db, goal) for goal in db.scalars(query.limit(100))]}


@router.post("/admin/ward-goals")
def create(body: GoalInput, user=Depends(admin), db=Depends(get_db, scope="function"),
           idempotency_key: str | None = Header(default=None)):
    def save():
        ward(db, body.area_id)
        goal = WardGoal(created_by=user.id, **body.model_dump())
        db.add(goal)
        db.flush()
        audit(db, user.id, "ward_goal", goal.id, "created", after=body.model_dump(mode="json"))
        return {"id": goal.id}
    return mutation(db, user, "ward_goal_create", idempotency_key, body.model_dump(mode="json"), save)


@router.put("/admin/ward-goals/{goal_id}")
def edit(goal_id: str, body: GoalInput, user=Depends(admin), db=Depends(get_db, scope="function"),
         idempotency_key: str | None = Header(default=None)):
    def save():
        goal = db.scalar(select(WardGoal).where(WardGoal.id == goal_id).with_for_update())
        if not goal:
            fail("GOAL_NOT_FOUND", "Ward goal not found", 404)
        ward(db, body.area_id)
        before = {key: str(getattr(goal, key)) for key in GoalInput.model_fields}
        for key, value in body.model_dump().items():
            setattr(goal, key, value)
        audit(db, user.id, "ward_goal", goal.id, "updated", before=before, after=body.model_dump(mode="json"))
        return {"id": goal.id}
    return mutation(db, user, "ward_goal_edit", idempotency_key,
                    {"id": goal_id, **body.model_dump(mode="json")}, save)
