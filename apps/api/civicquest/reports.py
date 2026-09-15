from datetime import timedelta

import imagehash
from sqlalchemy import func, select

from .common import audit, enqueue, fail, notify, user_ids
from .config import settings
from .db import now
from .geo import accountability, coords, point
from .media import classify
from .models import (
    Area,
    Category,
    Complaint,
    ComplaintStatusEvent,
    EscalationCase,
    Media,
    ModerationCase,
    Report,
    ReportFollow,
    ReportMilestone,
    SeenConfirmation,
    ShareCard,
    Vote,
)
from .progress import invalidate_report, verify_report

SEVERITY_TO_VALUE = {"low": 1, "medium": 2, "high": 3}
VALUE_TO_SEVERITY = {value: name for name, value in SEVERITY_TO_VALUE.items()}
PLACE_REWARD = {1: 15, 2: 25, 3: 50}


def pending_reward(report):
    if report.report_type != "place":
        return 0
    return PLACE_REWARD.get(report.severity, 25)


def milestone(db, report_id, kind, actor_id=None, details=None):
    existing = db.scalar(
        select(ReportMilestone).where(
            ReportMilestone.report_id == report_id, ReportMilestone.kind == kind
        )
    )
    if not existing:
        db.add(
            ReportMilestone(
                report_id=report_id, kind=kind, actor_id=actor_id, details=details or {}
            )
        )


def public_filter():
    terms = [
        Report.visibility == "public",
        Report.duplicate_of.is_(None),
        Report.status.notin_(["draft", "processing", "rejected"]),
    ]
    if not settings().catches_public:
        terms.append(Report.report_type == "place")
    return terms


def is_public(report):
    return (
        report.visibility == "public"
        and not report.duplicate_of
        and report.status not in {"draft", "processing", "rejected"}
        and (report.report_type == "place" or settings().catches_public)
    )


def get_report(db, report_id, user=None, edit=False):
    report = db.get(Report, report_id)
    if not report:
        fail("REPORT_NOT_VISIBLE", "This report is not available", 404)
    owner = user and report.reporter_id in user_ids(db, user.id)
    privileged = user and user.role in {"moderator", "admin"}
    if edit and not owner and not privileged:
        fail("FORBIDDEN", "This report belongs to another account", 403)
    if not edit and not is_public(report) and not owner and not privileged:
        fail("REPORT_NOT_VISIBLE", "This report is not available", 404)
    return report


def serialize_many(db, rows, user=None):
    rows = list(rows)
    ids = [r.id for r in rows]
    if not ids:
        return []
    context = {
        "votes": dict(
            db.execute(
                select(Vote.report_id, func.count()).where(Vote.report_id.in_(ids)).group_by(Vote.report_id)
            ).all()
        ),
        "seen": dict(
            db.execute(
                select(SeenConfirmation.report_id, func.count())
                .where(SeenConfirmation.report_id.in_(ids))
                .group_by(SeenConfirmation.report_id)
            ).all()
        ),
        "media": {},
        "categories": {c.code: c for c in db.scalars(select(Category))},
        "areas": {
            a.id: a
            for a in db.scalars(select(Area).where(Area.id.in_({r.area_id for r in rows if r.area_id})))
        },
        "voted": set(
            db.scalars(select(Vote.report_id).where(Vote.report_id.in_(ids), Vote.user_id == user.id))
        )
        if user
        else set(),
        "seen_by_me": set(
            db.scalars(
                select(SeenConfirmation.report_id).where(
                    SeenConfirmation.report_id.in_(ids), SeenConfirmation.user_id.in_(user_ids(db, user.id))
                )
            )
        )
        if user
        else set(),
        "user_ids": user_ids(db, user.id) if user else [],
    }
    for media in db.scalars(
        select(Media)
        .where(Media.report_id.in_(ids), Media.state == "processed")
        .order_by(Media.created_at, Media.id)
    ):
        context["media"].setdefault(media.report_id, media)
    return [serialize(db, row, user, context=context) for row in rows]


def serialize(db, report, user=None, detail=False, context=None):
    vote_count = (
        context["votes"].get(report.id, 0)
        if context
        else db.scalar(select(func.count()).select_from(Vote).where(Vote.report_id == report.id))
    )
    seen_count = (
        context["seen"].get(report.id, 0)
        if context
        else db.scalar(
            select(func.count())
            .select_from(SeenConfirmation)
            .where(SeenConfirmation.report_id == report.id)
        )
    )
    media = (
        context["media"].get(report.id)
        if context
        else db.scalar(
            select(Media)
            .where(Media.report_id == report.id, Media.state == "processed")
            .order_by(Media.created_at)
        )
    )
    category = context["categories"][report.category] if context else db.get(Category, report.category)
    area = (
        context["areas"].get(report.area_id)
        if context
        else (db.get(Area, report.area_id) if report.area_id else None)
    )
    v = {
        "id": report.id,
        "public_code": report.public_code,
        "report_type": report.report_type,
        "category": report.category,
        "category_name": category.name,
        "title": report.title or category.name,
        "description": report.description,
        "address": report.address,
        **coords(report.location),
        "status": report.status,
        "visibility": report.visibility,
        "verification": report.verification,
        "severity": VALUE_TO_SEVERITY.get(report.severity, "medium"),
        "upvotes": vote_count,
        "voted": report.id in context["voted"]
        if context
        else bool(user and db.get(Vote, (report.id, user.id))),
        "seen_count": seen_count,
        "seen": report.id in context["seen_by_me"]
        if context
        else bool(
            user
            and db.scalar(
                select(SeenConfirmation).where(
                    SeenConfirmation.report_id == report.id,
                    SeenConfirmation.user_id.in_(user_ids(db, user.id)),
                )
            )
        ),
        "following": bool(
            user
            and user.identity_type == "registered"
            and db.scalar(
                select(ReportFollow).where(
                    ReportFollow.report_id == report.id,
                    ReportFollow.user_id.in_(user_ids(db, user.id)),
                )
            )
        ),
        "image_url": f"/api/v1/media/{media.id}/view" if media else None,
        "created_at": report.created_at.isoformat(),
        "area_id": area.id if area else None,
        "area": area.name if area else None,
        "demo": report.demo,
        "owner_label": "Owner not confirmed",
        "can_verify": bool(
            user
            and user.identity_type == "registered"
            and report.reporter_id not in (context["user_ids"] if context else user_ids(db, user.id))
            and is_public(report)
            and report.report_type == "place"
        ),
    }
    if detail:
        v["media"] = [
            {"id": m.id, "url": f"/api/v1/media/{m.id}/view"}
            for m in db.scalars(select(Media).where(Media.report_id == report.id, Media.state == "processed"))
        ]
        owner = accountability(db, **coords(report.location), category=category)
        v["accountability"] = owner
        v["owner_label"] = owner["label"]
        v["timeline"] = [
            {
                "action": item.kind,
                "created_at": item.created_at.isoformat(),
                "details": item.details,
            }
            for item in db.scalars(
                select(ReportMilestone)
                .where(ReportMilestone.report_id == report.id)
                .order_by(ReportMilestone.created_at, ReportMilestone.id)
            )
        ]
        case = db.scalar(select(EscalationCase).where(EscalationCase.report_id == report.id))
        complaint = (
            db.scalar(select(Complaint).where(Complaint.escalation_id == case.id)) if case else None
        )
        v["escalation"] = (
            {
                "state": case.state,
                "threshold": case.threshold,
                "official_id": complaint.official_id if complaint else None,
                "official_status": "Official complaint pending" if complaint and not complaint.official_id else None,
                "source_name": complaint.source_name if complaint else None,
                "source_url": complaint.source_url if complaint else None,
                "last_checked_at": complaint.last_checked_at.isoformat()
                if complaint and complaint.last_checked_at
                else None,
                "events": [
                    {
                        "status": event.status,
                        "occurred_at": event.occurred_at.isoformat(),
                        "source_note": event.source_note,
                    }
                    for event in db.scalars(
                        select(ComplaintStatusEvent)
                        .where(ComplaintStatusEvent.complaint_id == complaint.id)
                        .order_by(ComplaintStatusEvent.occurred_at, ComplaintStatusEvent.id)
                    )
                ]
                if complaint
                else [],
            }
            if case
            else None
        )
        if user and report.reporter_id in user_ids(db, user.id):
            v["pending_xp"] = (
                0
                if report.verification in {"community", "moderator"} or report.status == "rejected"
                else pending_reward(report)
            )
    return v


def create_draft(db, user, body):
    category = db.get(Category, body.category)
    if not category or not category.active or category.report_type != body.report_type:
        fail("INVALID_CATEGORY", "Choose a supported category for this report type")
    ownership = accountability(db, body.lat, body.lng, category)
    r = Report(
        reporter_id=user.id,
        report_type=body.report_type,
        category=body.category,
        title=body.title,
        description=body.description,
        location=point(body.lat, body.lng),
        accuracy_m=body.accuracy_m,
        address=body.address,
        severity=SEVERITY_TO_VALUE[body.severity],
        area_id=ownership["area"]["id"] if ownership["area"] else None,
        authority_id=ownership["authority"]["id"] if ownership["authority"] else None,
        demo=ownership["synthetic"],
    )
    db.add(r)
    db.flush()
    milestone(db, r.id, "reported", user.id)
    audit(db, user.id, "report", r.id, "draft_created")
    return {"id": r.id, "status": r.status}


def finalize(db, user, report):
    if report.status != "draft":
        return {
            "id": report.id,
            "status": report.status,
            "visibility": report.visibility,
            "provisional_xp": pending_reward(report),
        }
    if not db.scalar(select(Media.id).where(Media.report_id == report.id, Media.state == "processed")):
        fail("MEDIA_REQUIRED", "Upload and finish processing a photo first")
    report.status = "processing"
    report.visibility = "pending"
    report.finalized_at = now()
    enqueue(db, "process_report", {"report_id": report.id}, f"process:{report.id}")
    audit(db, user.id, "report", report.id, "submitted", after={"status": "processing"}, public=True)
    return {
        "id": report.id,
        "status": "processing",
        "visibility": "pending",
        "provisional_xp": pending_reward(report),
    }


def process_report(db, report_id):
    report = db.scalar(select(Report).where(Report.id == report_id).with_for_update())
    if not report or report.status != "processing":
        return
    photos = list(db.scalars(select(Media).where(Media.report_id == report.id, Media.state == "processed")))
    all_safe = bool(photos)
    flags = []
    for media in photos:
        try:
            result = classify(media)
        except Exception:
            result = {"safe": False, "flags": ["safety_check_failed"]}
        if result.get("category") and result["category"] != report.category:
            result["safe"] = False
            result["flags"] = [*result.get("flags", []), "category_needs_review"]
        media.flags = result
        all_safe = all_safe and result.get("safe") is True
        flags += result.get("flags", [])
    cat = db.get(Category, report.category)
    candidates = list(
        db.scalars(
            select(Report)
            .join(Category, Category.code == Report.category)
            .where(
                Report.id != report.id,
                Category.family == cat.family,
                Report.created_at >= now() - timedelta(hours=48),
                Report.status.notin_(["draft", "rejected"]),
                func.ST_DWithin(Report.location, report.location, 50),
            )
        )
    )
    duplicate_ids = []
    for candidate in candidates:
        others = db.scalars(select(Media).where(Media.report_id == candidate.id, Media.phash.is_not(None)))
        if any(
            imagehash.hex_to_hash(m.phash) - imagehash.hex_to_hash(other.phash) <= 6
            for other in others
            for m in photos
            if m.phash
        ):
            duplicate_ids.append(candidate.id)
    if duplicate_ids:
        flags.append("duplicate_candidate")
        all_safe = False
    report.status = "open"
    report.visibility = "public" if all_safe and report.report_type == "place" else "pending"
    if report.visibility != "public":
        db.add(
            ModerationCase(
                report_id=report.id,
                kind="publication",
                priority=1 if report.report_type == "civic_catch" else 2,
                details={"flags": flags, "duplicate_candidates": duplicate_ids},
            )
        )
    audit(
        db,
        None,
        "report",
        report.id,
        "published" if report.visibility == "public" else "awaiting_review",
        after={"status": "open"},
        public=True,
    )
    milestone(db, report.id, "publication_reviewed", details={"visibility": report.visibility})
    notify(
        db,
        report.reporter_id,
        "Report update",
        "Your report is published."
        if report.visibility == "public"
        else "Your report is waiting for review.",
        f"/reports/{report.id}",
        f"processed:{report.id}",
    )
    enqueue(db, "hotspots", {}, f"hotspots:processed:{report.id}")


def invalidate_cards(db):
    for card in db.scalars(select(ShareCard).where(ShareCard.state == "ready")):
        card.state = "revoked"


def moderate(db, report, actor, decision, reason):
    if report.status in {"draft", "processing"}:
        fail("INVALID_TRANSITION", "Wait until report processing completes", 409)
    before = {"status": report.status, "visibility": report.visibility, "verification": report.verification}
    if decision in {"publish", "restore", "verify"}:
        media = list(db.scalars(select(Media).where(Media.report_id == report.id)))
        if not media or any(m.state != "processed" or not m.public_key for m in media):
            fail("MEDIA_NOT_READY", "A safe derivative is required before publication")
        if any(m.flags.get("flags") and not m.redacted for m in media):
            if any(
                any(
                    f
                    not in {
                        "safety_provider_unavailable",
                        "safety_check_failed",
                        "category_needs_review",
                        "duplicate_candidate",
                    }
                    for f in m.flags.get("flags", [])
                )
                for m in media
                if not m.redacted
            ):
                fail("REDACTION_REQUIRED", "Review and redact flagged evidence first")
        report.visibility = (
            "public" if report.report_type == "place" or settings().catches_public else "pending"
        )
        if report.status == "rejected":
            report.status = "open"
        if decision == "verify":
            if report.reporter_id in user_ids(db, actor.id):
                fail("SELF_VERIFICATION", "Another moderator must verify your report", 403)
            verify_report(db, report, "moderator")
    elif decision in {"restrict", "remove", "reject"}:
        report.visibility = {"restrict": "restricted", "remove": "removed", "reject": "removed"}[decision]
        if decision == "reject":
            report.status = "rejected"
            invalidate_report(db, report)
        invalidate_cards(db)
    elif decision == "acknowledge":
        report.status = "acknowledged"
        milestone(db, report.id, "authority_acknowledged", actor.id)
    elif decision == "in_progress":
        report.status = "in_progress"
        milestone(db, report.id, "action_pending", actor.id)
    for case in db.scalars(
        select(ModerationCase).where(ModerationCase.report_id == report.id, ModerationCase.state != "closed")
    ):
        case.state = "closed"
        case.decision = decision
        case.closed_at = now()
    audit(
        db,
        actor.id,
        "report",
        report.id,
        decision,
        reason,
        before,
        {"status": report.status, "visibility": report.visibility, "verification": report.verification},
        public=True,
    )
    enqueue(db, "hotspots", {}, f"hotspots:moderate:{report.id}:{now().isoformat()}")
    notify(
        db,
        report.reporter_id,
        "Your report has an update",
        "View its current status and verification.",
        f"/reports/{report.id}",
        f"review:{report.id}:{now().isoformat()}",
    )
