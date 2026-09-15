import io

import pytest
from civicquest.geo import point
from civicquest.media import Storage, decode
from civicquest.models import Category, Identity, Report, User, Verification, XPEvent
from civicquest.progress import award, invalidate_report, profile, verify_report
from civicquest.schemas import Push
from fastapi import HTTPException
from PIL import Image
from sqlalchemy import func, select


def report_fixture(db):
    category = Category(code="test_road", name="Test road", report_type="place", family="roads")
    users = [User(identity_type="registered") for _ in range(3)]
    db.add_all([category, *users])
    db.flush()
    report = Report(
        reporter_id=users[0].id,
        report_type="place",
        category=category.code,
        title="Test",
        location=point(19.05, 72.84),
        status="open",
        visibility="public",
    )
    db.add(report)
    db.flush()
    return report, users


def test_publication_does_not_award_and_verification_is_replay_safe(db):
    report, users = report_fixture(db)
    assert profile(db, users[0])["xp"] == 0
    for user in users[1:]:
        db.add(Verification(report_id=report.id, user_id=user.id, result="confirmed"))
    db.flush()
    verify_report(db, report, "community")
    verify_report(db, report, "community")
    assert profile(db, users[0])["xp"] == 25
    assert [profile(db, u)["xp"] for u in users[1:]] == [2, 2]
    assert db.scalar(select(func.count()).select_from(XPEvent).where(XPEvent.source_id == report.id)) == 3
    invalidate_report(db, report)
    invalidate_report(db, report)
    assert [profile(db, u)["xp"] for u in users] == [0, 0, 0]


def test_daily_cap_excludes_verified_event_components(db):
    user = User()
    db.add(user)
    db.flush()
    assert award(db, user.id, "test", "report", "one", 95) == 95
    assert award(db, user.id, "test", "report", "two", 15) == 5
    assert award(db, user.id, "test", "report", "three", 10) == 0
    assert award(db, user.id, "action_completed", "action", "event", 120, capped=False) == 120
    assert award(db, user.id, "action_completed", "action", "event", 120, capped=False) == 0
    assert profile(db, user)["xp"] == 220


@pytest.mark.parametrize(("severity", "expected"), [(1, 15), (2, 25), (3, 50)])
def test_verified_place_reward_uses_accepted_severity(db, severity, expected):
    report, users = report_fixture(db)
    report.severity = severity
    verify_report(db, report, "moderator")
    assert profile(db, users[0])["xp"] == expected


def test_photo_derivative_removes_exif_and_rejects_mismatch():
    source = Image.new("RGB", (40, 60), "green")
    exif = Image.Exif()
    exif[270] = "private location"
    output = io.BytesIO()
    source.save(output, format="JPEG", exif=exif)
    clean, _ = decode(output.getvalue(), "image/jpeg")
    with Image.open(io.BytesIO(clean)) as derivative:
        assert not derivative.getexif()
    with pytest.raises(HTTPException) as exc:
        decode(output.getvalue(), "image/png")
    assert exc.value.detail["code"] == "IMAGE_TYPE_MISMATCH"
    with pytest.raises(HTTPException):
        decode(b"not an image", "image/jpeg")


def test_storage_rejects_traversal():
    with pytest.raises(ValueError):
        Storage().path("../../private.txt")


def test_browser_push_serialization():
    subscription = Push.model_validate(
        {
            "endpoint": "https://example.invalid/push",
            "expirationTime": None,
            "keys": {"auth": "a", "p256dh": "b"},
        }
    )
    assert subscription.expirationTime is None


def test_public_profile_does_not_reveal_private_case_counts(db):
    report, users = report_fixture(db)
    report.visibility = "restricted"
    verify_report(db, report, "moderator")
    assert profile(db, users[0])["verified_reports"] == 1
    public = profile(db, users[0], public=True)
    assert public["verified_reports"] == 0
    assert public["civicdex"] == []
    assert "role" not in public


def test_private_profile_lists_linked_providers_only(db):
    user = User(identity_type="registered")
    db.add(user)
    db.flush()
    db.add_all([Identity(user_id=user.id, provider="google", subject="one"),
                Identity(user_id=user.id, provider="demo", subject="two")])
    db.flush()
    assert profile(db, user)["linked_providers"] == ["demo", "google"]
    assert "linked_providers" not in profile(db, user, public=True)


def test_linking_removes_new_self_votes_and_verifications(db):
    from civicquest.identity import link_identity
    from civicquest.models import Identity, Vote

    report, users = report_fixture(db)
    guest, target, independent = users
    guest.identity_type = "guest"
    db.add(Identity(user_id=target.id, provider="test", subject="existing"))
    db.add(Vote(report_id=report.id, user_id=target.id))
    for user in [target, independent]:
        db.add(Verification(report_id=report.id, user_id=user.id, result="confirmed"))
    db.flush()
    verify_report(db, report, "community")
    link_identity(db, guest, "test", "existing")
    assert db.get(Vote, (report.id, target.id)) is None
    assert report.verification == "unverified"
    assert profile(db, target)["xp"] == 0
