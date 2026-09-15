from datetime import timedelta

from civicquest import geo
from civicquest.db import now
from civicquest.models import (
    Category,
    CivicAction,
    Participation,
    Report,
    Resolution,
    User,
    WardGoal,
    XPEvent,
)
from civicquest.ward_goals import projection
from sqlalchemy import func, select
from test_geography import geography  # noqa: F401
from test_journeys import clients  # noqa: F401


def test_unique_outcomes_reconcile_restriction_duplicates_and_cancellation(db, geography):  # noqa: F811
    users = [User(identity_type="registered") for _ in range(3)]
    category = Category(code="goal_waste", name="Goal waste", family="waste", report_type="place")
    db.add_all([*users, category])
    db.flush()
    ward = geography["west-ward"]
    goal = WardGoal(area_id=ward.id, created_by=users[0].id, title="Clean our ward", target=2,
                    starts_at=now()-timedelta(days=2), ends_at=now()+timedelta(days=2), status="published")
    report = Report(reporter_id=users[0].id, report_type="place", category=category.code,
                    location=geo.point(19.1,72.84), area_id=ward.id, status="resolved",
                    visibility="public", resolved_at=now())
    action = CivicAction(created_by=users[0].id, title="Cleanup", description="Synthetic cleanup",
                         organizer="Demo", location_name="Test", location=geo.point(19.1,72.84),
                         starts_at=now()-timedelta(hours=3), ends_at=now()-timedelta(hours=1), status="published")
    db.add_all([goal,report,action])
    db.flush()
    for user in users[1:]:
        db.add(Resolution(report_id=report.id, user_id=user.id, description="Proof", state="verified"))
        db.add(Participation(action_id=action.id,user_id=user.id,state="verified"))
    db.flush()
    xp_before = db.scalar(select(func.count()).select_from(XPEvent))
    assert projection(db,goal)["progress"] == 2  # 2 proposals and 2 participants remain 2 outcomes
    assert projection(db,goal)["completed"]
    assert projection(db,goal)["progress"] == 2  # replay/rebuild is the same authoritative query
    assert db.scalar(select(func.count()).select_from(XPEvent)) == xp_before
    report.visibility = "restricted"
    db.flush()
    assert projection(db,goal)["progress"] == 1
    report.visibility = "public"
    report.duplicate_of = report.id
    db.flush()
    assert projection(db,goal)["progress"] == 1
    action.status = "cancelled"
    db.flush()
    assert projection(db,goal)["progress"] == 0
    report.duplicate_of = None
    report.resolved_at = goal.ends_at
    action.status = "published"
    action.location = geo.point(19.1,72.9)  # shared boundary requires review, never two ward credits
    db.flush()
    assert projection(db,goal)["progress"] == 0


def test_admin_goals_require_auth_csrf_and_idempotency(db, geography, clients):  # noqa: F811
    citizen, _ = clients(True)
    admin, uid = clients(True)
    db.get(User,uid).role = "admin"
    db.flush()
    body = {"title":"Verified cleanup goal", "area_id":geography["west-ward"].id,
            "target":3,"starts_at":now().isoformat(),"ends_at":(now()+timedelta(days=7)).isoformat(),
            "status":"draft"}
    headers={"Idempotency-Key":"create-goal-once"}
    assert citizen.post('/api/v1/admin/ward-goals',json=body,headers=headers).status_code == 403
    created = admin.post('/api/v1/admin/ward-goals',json=body,headers=headers)
    assert created.status_code == 200, created.text
    assert admin.post('/api/v1/admin/ward-goals',json=body,headers=headers).json() == created.json()
    assert citizen.get('/api/v1/ward-goals').json()["items"] == []
    body["status"] = "published"
    path='/api/v1/admin/ward-goals/'+created.json()["id"]
    assert admin.put(path,json=body,headers={"Idempotency-Key":"publish-goal"}).status_code == 200
    assert citizen.get('/api/v1/ward-goals').json()["items"][0]["progress"] == 0
    body["status"] = "cancelled"
    assert admin.put(path,json=body,headers={"Idempotency-Key":"cancel-goal"}).status_code == 200
    assert citizen.get('/api/v1/ward-goals').json()["items"] == []
    admin.headers.pop('x-csrf-token')
    assert admin.put(path,json=body,headers={"Idempotency-Key":"csrf-goal"}).status_code == 403
