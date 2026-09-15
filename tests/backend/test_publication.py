from datetime import timedelta

import pytest
from civicquest import reports
from civicquest.db import now
from civicquest.geo import point
from civicquest.models import Category, Media, ModerationCase, Report, User, XPEvent
from sqlalchemy import func, select


@pytest.mark.parametrize(
    "provider_result,report_type,expected",
    [
        ({"safe": True, "synthetic": True, "flags": []}, "place", "public"),
        ({"safe": False, "flags": ["safety_provider_unavailable"]}, "place", "pending"),
        ({"safe": True, "synthetic": True, "flags": []}, "civic_catch", "pending"),
        (RuntimeError("Provider timeout"), "place", "pending"),
    ],
)
def test_processing_fails_closed_and_never_awards_xp(db, monkeypatch, provider_result, report_type, expected):
    user = User()
    category = Category(code="test_pipeline", name="Test pipeline", report_type=report_type, family="test")
    db.add_all([user, category])
    db.flush()
    report = Report(
        reporter_id=user.id,
        report_type=report_type,
        category=category.code,
        location=point(19.18, 72.91),
        status="draft",
    )
    db.add(report)
    db.flush()
    db.add(
        Media(
            owner_id=user.id,
            report_id=report.id,
            original_key="private-test",
            public_key="public-test",
            content_type="image/jpeg",
            size=100,
            upload_token_hash="test",
            upload_expires=now() + timedelta(minutes=5),
            state="processed",
            flags={},
            sha256="test",
        )
    )
    db.flush()

    def classify(media):
        if isinstance(provider_result, Exception):
            raise provider_result
        return provider_result

    monkeypatch.setattr(reports, "classify", classify)
    reports.finalize(db, user, report)
    reports.process_report(db, report.id)
    reports.process_report(db, report.id)
    assert report.visibility == expected
    assert report.verification == "unverified"
    assert not db.scalar(select(XPEvent).where(XPEvent.user_id == user.id))
    assert db.scalar(
        select(func.count()).select_from(ModerationCase).where(ModerationCase.report_id == report.id)
    ) == (0 if expected == "public" else 1)
