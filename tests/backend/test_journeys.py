import uuid
from pathlib import Path

import pytest
from civicquest.db import get_db
from civicquest.geo import point
from civicquest.main import app
from civicquest.models import Area, Category, EscalationCase, Report, ShareCard, User
from civicquest.sharing import render_card
from fastapi.testclient import TestClient
from sqlalchemy import select


@pytest.fixture
def clients(db):
    app.dependency_overrides[get_db] = lambda: db
    opened = []

    def make(registered=False):
        c = TestClient(app, base_url="http://localhost:3000")
        response = c.post("/api/v1/sessions/guest")
        assert response.status_code == 200, response.text
        c.headers["x-csrf-token"] = c.cookies["cq_csrf"]
        if registered:
            db.get(User, response.json()["id"]).identity_type = "registered"
            db.flush()
        opened.append(c)
        return c, response.json()["id"]

    yield make
    for c in opened:
        c.close()
    app.dependency_overrides.clear()


def new_report(db, author, report_type="place"):
    code = "test_" + uuid.uuid4().hex
    db.add(Category(code=code, name="Synthetic test category", report_type=report_type, family="roads"))
    db.flush()
    report = Report(
        reporter_id=author,
        category=code,
        report_type=report_type,
        title="Synthetic test report",
        location=point(19.1, 72.9),
        status="open",
        visibility="public",
    )
    db.add(report)
    db.flush()
    return report


def test_guest_vote_csrf_and_two_independent_verifiers(db, clients):
    reporter, reporter_id = clients()
    first, _ = clients(True)
    second, _ = clients(True)
    report = new_report(db, reporter_id)
    path = f"/api/v1/reports/{report.id}"
    assert reporter.post(path + "/upvotes").status_code == 403
    assert first.post(path + "/upvotes").status_code == 200
    assert first.post(path + "/upvotes").status_code == 200
    assert first.get(path).json()["upvotes"] == 1
    assert first.delete(path + "/upvotes").status_code == 200
    assert first.get(path).json()["upvotes"] == 0
    assert reporter.post(path + "/verify", json={"result": "confirmed"}).status_code == 403
    assert first.post(path + "/verify", json={"result": "confirmed"}).json()["verification"] == "unverified"
    assert reporter.get("/api/v1/me").json()["xp"] == 0
    assert second.post(path + "/verify", json={"result": "confirmed"}).json()["verification"] == "community"
    assert reporter.get("/api/v1/me").json()["xp"] == 25
    assert second.post(path + "/verify", json={"result": "confirmed"}).status_code == 200
    assert reporter.get("/api/v1/me").json()["xp"] == 25
    first.headers.pop("x-csrf-token")
    assert first.post(path + "/upvotes").status_code == 403


def test_public_code_lookup_and_seen_threshold_create_one_internal_case(db, clients):
    author, author_id = clients()
    report = new_report(db, author_id)
    by_code = author.get(f"/api/v1/reports/by-code/{report.public_code.lower()}")
    assert by_code.status_code == 200
    assert by_code.json()["id"] == report.id
    viewers = [clients()[0] for _ in range(10)]
    path = f"/api/v1/reports/{report.id}/seen"
    for index, viewer in enumerate(viewers, 1):
        response = viewer.post(path)
        assert response.status_code == 200
        assert response.json()["seen_count"] == index
        assert viewer.post(path).json()["seen_count"] == index
    assert db.scalar(select(EscalationCase).where(EscalationCase.report_id == report.id))
    assert len(list(db.scalars(select(EscalationCase).where(EscalationCase.report_id == report.id)))) == 1
    reviewer, reviewer_id = clients(True)
    db.get(User, reviewer_id).role = "moderator"
    db.flush()
    queue = reviewer.get("/api/v1/admin/escalation-cases")
    assert queue.status_code == 200
    case = next(item for item in queue.json()["items"] if item["report_id"] == report.id)
    assert case["report_code"] == report.public_code
    assert case["complaint"] is None
    assert reviewer.post(
        f"/api/v1/admin/escalation-cases/{case['id']}/decision",
        json={"approved": True, "reason": "Synthetic evidence reviewed for test handoff."},
    ).json()["state"] == "approved"
    handed_off = reviewer.post(
        f"/api/v1/admin/escalation-cases/{case['id']}/handoff",
        json={
            "source_name": "Synthetic official test portal",
            "source_url": "https://example.invalid/complaints",
            "official_id": "TEST-OFFICIAL-1",
            "receipt_key": None,
        },
    )
    assert handed_off.status_code == 200
    refreshed = reviewer.get("/api/v1/admin/escalation-cases").json()["items"]
    refreshed_case = next(item for item in refreshed if item["id"] == case["id"])
    assert refreshed_case["complaint"]["official_id"] == "TEST-OFFICIAL-1"
    assert viewers[-1].delete(path).json()["seen_count"] == 9


def test_catches_are_hidden_even_with_public_visibility(db, clients):
    author, author_id = clients()
    stranger, _ = clients(True)
    report = new_report(db, author_id, "civic_catch")
    assert author.get(f"/api/v1/reports/{report.id}").status_code == 200
    assert stranger.get(f"/api/v1/reports/{report.id}").status_code == 404
    assert stranger.post(f"/api/v1/reports/{report.id}/upvotes").status_code == 404
    assert stranger.get("/api/v1/feeds/civic-catches").status_code in {200, 404}


def test_live_catch_photo_is_profile_only_and_awards_zero_xp(db, clients):
    owner, owner_id = clients(True)
    owner_user = db.get(User, owner_id)
    owner_user.handle = "catch_" + uuid.uuid4().hex[:10]
    if not db.get(Category, "littering"):
        db.add(Category(code="littering", name="Littering", report_type="civic_catch", family="behavior"))
    db.flush()
    session = owner.post(
        "/api/v1/catches/capture-sessions",
        json={"lat": 19.018, "lng": 72.842, "accuracy_m": 12},
    )
    assert session.status_code == 200
    session_id = session.json()["id"]
    photo = Path("data/samples/garbage_dump.jpg").read_bytes()
    signed = owner.post(
        f"/api/v1/catches/capture-sessions/{session_id}/media/presign",
        json={"content_type": "image/jpeg", "size": len(photo), "role": "evidence"},
    )
    assert signed.status_code == 200
    media = signed.json()
    assert owner.put(media["upload_url"], content=photo, headers=media["headers"]).status_code == 200
    assert owner.post(
        f"/api/v1/catches/capture-sessions/{session_id}/media/{media['id']}/complete"
    ).status_code == 200
    posted = owner.post(
        f"/api/v1/catches/capture-sessions/{session_id}/finalize",
        json={
            "category": "littering",
            "description": "An observable synthetic demonstration for automated testing.",
            "address": "Demo central neighborhood",
        },
    )
    assert posted.status_code == 200
    assert posted.json() == {
        "id": posted.json()["id"],
        "visibility": "public",
        "status": "open",
        "xp": 0,
    }
    assert owner.get("/api/v1/me").json()["xp"] == 0
    stranger, _ = clients()
    assert all(
        item["report_type"] == "place"
        for item in stranger.get("/api/v1/feed/places").json()["items"]
    )
    wall = stranger.get(f"/api/v1/profiles/{owner_user.handle}/catches")
    assert wall.status_code == 200
    assert wall.json()["items"][0]["location"]["lat"] == pytest.approx(19.018)


def test_comments_and_follows_require_linked_account(db, clients):
    author, author_id = clients()
    guest, _ = clients()
    member, _ = clients(True)
    report = new_report(db, author_id)
    path = f"/api/v1/reports/{report.id}"
    assert guest.post(path + "/follow").status_code == 403
    assert guest.post(path + "/comments", json={"body": "Still visible", "kind": "comment"}).status_code == 403
    assert member.post(path + "/follow").json()["following"] is True
    made = member.post(path + "/comments", json={"body": "Still visible", "kind": "comment"})
    assert made.status_code == 200
    message_id = made.json()["id"]
    assert made.json()["can_report"] is False
    visible = guest.get(path + "/comments").json()["items"][0]
    assert visible["body"] == "Still visible"
    assert visible["can_report"] is True
    concern = guest.post(path + f"/comments/{message_id}/abuse", json={"reason": "Contains harmful context."})
    assert concern.status_code == 200
    assert guest.post(path + f"/comments/{message_id}/abuse",
                      json={"reason": "Contains harmful context."}).json()["id"] == concern.json()["id"]
    assert member.post(path + f"/comments/{message_id}/abuse",
                       json={"reason": "My own comment."}).status_code == 403
    reviewer, reviewer_id = clients(True)
    db.get(User, reviewer_id).role = "moderator"
    db.flush()
    queue = reviewer.get("/api/v1/admin/moderation/cases").json()["items"]
    case = next(item for item in queue if item["id"] == concern.json()["id"])
    assert case["details"]["comment"] == "Still visible"
    removed = reviewer.post(f"/api/v1/admin/moderation/cases/{case['id']}/comment-decision",
                            json={"decision": "remove", "reason": "Community rules reviewed."})
    assert removed.json()["message_state"] == "removed"
    assert guest.get(path + "/comments").json()["items"] == []
    assert member.get("/api/v1/me").json()["xp"] == 0


def test_notification_preferences_are_persisted_and_push_requires_linked_account(db, clients):
    guest, _ = clients()
    saved = guest.put(
        "/api/v1/notification-preferences",
        json={"report_updates": False, "action_reminders": True, "push": True},
    )
    assert saved.status_code == 200
    assert saved.json() == {"report_updates": False, "action_reminders": True, "push": False}
    member, _ = clients(True)
    assert member.put(
        "/api/v1/notification-preferences",
        json={"report_updates": True, "action_reminders": False, "push": True},
    ).json() == {"report_updates": True, "action_reminders": False, "push": True}
    assert member.get("/api/v1/notification-preferences").json()["push"] is True


def test_civic_card_uses_public_profile_and_report_variants_require_resolution(db, clients):
    member, member_id = clients(True)
    db.get(User, member_id).handle = "share_" + uuid.uuid4().hex[:10]
    db.flush()
    created = member.post(
        "/api/v1/share-cards",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={"kind": "civic_card"},
    )
    assert created.status_code == 200
    card = db.get(ShareCard, created.json()["id"])
    render_card(db, card)
    db.flush()
    assert member.get(f"/api/v1/share-cards/{card.id}/image").headers["content-type"] == "image/png"
    unresolved = new_report(db, member_id)
    rejected = member.post(
        "/api/v1/share-cards",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={"kind": "resolved_fix", "report_id": unresolved.id},
    )
    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "VERIFIED_RESOLUTION_REQUIRED"


def test_guest_cannot_assign_role(db, clients):
    guest, _ = clients()
    assert guest.post("/api/v1/admin/actions", json={"role": "admin"}).status_code == 403


def test_account_deletion_hides_history_and_revokes_sessions(db, clients):
    owner, owner_id = clients(True)
    stranger, _ = clients()
    report = new_report(db, owner_id)
    user = db.get(User, owner_id)
    user.email = "synthetic@example.invalid"
    user.portrait_id = "explorer"
    user.handle = "delete_" + uuid.uuid4().hex[:12]
    db.flush()
    assert stranger.get(f"/api/v1/reports/{report.id}").status_code == 200
    assert owner.delete("/api/v1/account").status_code == 200
    assert owner.get("/api/v1/me").status_code == 401
    assert stranger.get(f"/api/v1/reports/{report.id}").status_code == 404
    assert user.email is None
    assert user.handle is None
    assert user.status == "deleted"
    assert user.portrait_id is None


def test_optional_portrait_is_private_until_handle_and_never_awards_xp(db, clients):
    owner, owner_id = clients()
    stranger, _ = clients()
    path = "/api/v1/profiles/me/portrait"
    assert owner.get("/api/v1/me").json()["portrait_id"] is None
    for _ in range(2):
        response = owner.put(path, json={"portrait_id": "observer"})
        assert response.status_code == 200
        assert response.json()["portrait_id"] == "observer"
        assert response.json()["xp"] == 0
    assert stranger.get("/api/v1/me").json()["portrait_id"] is None
    assert owner.put(path, json={"portrait_id": "../../private"}).status_code == 422
    assert owner.put(path, json={"portrait_id": "maker", "user_id": owner_id}).status_code == 422
    assert owner.put(path, json={"portrait_id": None}).json()["portrait_id"] is None
    owner.headers.pop("x-csrf-token")
    assert owner.put(path, json={"portrait_id": "maker"}).status_code == 403


def test_portrait_survives_linking_and_existing_account_choice_wins(db):
    from civicquest.identity import link_identity

    guest = User(portrait_id="explorer")
    db.add(guest)
    db.flush()
    subject = uuid.uuid4().hex
    linked = link_identity(db, guest, "test", subject)
    assert linked.portrait_id == "explorer"
    returning = User(portrait_id="observer")
    db.add(returning)
    db.flush()
    assert link_identity(db, returning, "test", subject).portrait_id == "explorer"
    linked.portrait_id = None
    new_guest = User(portrait_id="maker")
    db.add(new_guest)
    db.flush()
    assert link_identity(db, new_guest, "test", subject).portrait_id == "maker"


def test_area_detail_uses_public_projection_and_provenance(db, clients):
    visitor, visitor_id = clients()
    area = db.scalar(select(Area).where(Area.code == "demo-central"))
    report = new_report(db, visitor_id)
    report.area_id = area.id
    report.location = point(19.02, 72.84)
    report.title = "Visible area detail test"
    db.flush()
    response = visitor.get(f"/api/v1/areas/{area.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == area.id
    assert body["synthetic"] is True
    assert body["provenance"]["version"] == "1"
    visible = next(item for item in body["reports"] if item["title"] == "Visible area detail test")
    assert visible["area_id"] == area.id
    before = body["statistics"]["total_reports"]
    report.visibility = "restricted"
    db.flush()
    hidden = visitor.get(f"/api/v1/areas/{area.id}").json()
    assert hidden["statistics"]["total_reports"] == before - 1
    assert "Visible area detail test" not in [item["title"] for item in hidden["reports"]]
