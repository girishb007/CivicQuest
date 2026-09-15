from datetime import timedelta

import pytest
from civicquest.action_routes import approve_participant, challenge, checkin, join
from civicquest.db import now
from civicquest.geo import point
from civicquest.models import CivicAction, Participation, User
from civicquest.progress import profile
from civicquest.schemas import Checkin, Decision
from fastapi import HTTPException


def test_action_geofence_replay_approval_and_invalidation(db):
    citizen = User(identity_type="registered")
    admin = User(identity_type="registered", role="admin")
    db.add_all([citizen, admin])
    db.flush()
    event = CivicAction(
        created_by=admin.id,
        title="Synthetic cleanup",
        description="Synthetic cleanup event",
        organizer="Test",
        location_name="Test",
        location=point(19.02, 72.84),
        starts_at=now() - timedelta(minutes=5),
        ends_at=now() + timedelta(hours=2),
        capacity=1,
        status="published",
    )
    db.add(event)
    db.flush()
    join(event.id, citizen, db)
    db.flush()
    token = challenge(event.id, citizen, db)["challenge"]
    db.flush()
    with pytest.raises(HTTPException):
        checkin(event.id, Checkin(lat=19.2, lng=72.84, accuracy_m=10, challenge=token), citizen, db)
    checkin(event.id, Checkin(lat=19.02, lng=72.84, accuracy_m=10, challenge=token), citizen, db)
    db.flush()
    with pytest.raises(HTTPException):
        checkin(event.id, Checkin(lat=19.02, lng=72.84, accuracy_m=10, challenge=token), citizen, db)
    assert profile(db, citizen)["xp"] == 0
    participation = db.get(Participation, (event.id, citizen.id))
    participation.state = "pending"
    db.flush()
    approve_participant(
        event.id, citizen.id, Decision(approved=True, reason="Reviewed before and after proof"), admin, db
    )
    approve_participant(event.id, citizen.id, Decision(approved=True, reason="Repeated approval"), admin, db)
    assert profile(db, citizen)["xp"] == 120
    assert "first_verified_action" in profile(db, citizen)["badges"]
    from civicquest.routes import claim_quest

    claim_quest("cleanup", citizen, db)
    assert profile(db, citizen)["xp"] == 145
    approve_participant(
        event.id, citizen.id, Decision(approved=False, reason="Proof invalidated after review"), admin, db
    )
    assert profile(db, citizen)["xp"] == 0
    assert "first_verified_action" not in profile(db, citizen)["badges"]
