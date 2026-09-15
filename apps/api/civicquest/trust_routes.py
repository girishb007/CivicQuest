import re

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, func, select

from . import progress, reports, schemas
from .auth import current_user, moderator, optional_user, registered
from .common import audit, fail, notify, user_ids
from .db import get_db, now
from .media import Storage, authorize_upload, redact
from .models import (
    Appeal,
    CivicAction,
    Complaint,
    ComplaintStatusEvent,
    EscalationCase,
    Media,
    ModerationCase,
    Report,
    ReportFollow,
    ReportMessage,
    Resolution,
    ResolutionVerification,
    SeenConfirmation,
    User,
    XPEvent,
)

router = APIRouter(prefix="/api/v1")


def message_data(db, item, user=None):
    author = db.get(User, item.user_id)
    return {
        "id": item.id,
        "kind": item.kind,
        "body": item.body,
        "author": author.handle or author.display_name,
        "created_at": item.created_at.isoformat(),
        "can_report": bool(user and item.user_id not in user_ids(db, user.id)),
    }


@router.post("/reports/{rid}/seen")
def seen(rid: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    report = db.scalar(select(Report).where(Report.id == rid).with_for_update())
    if not report or report.report_type != "place" or not reports.is_public(report):
        fail("SEEN_UNAVAILABLE", "Seen confirmations are available for public Place reports", 403)
    ids = user_ids(db, user.id)
    existing = db.scalar(
        select(SeenConfirmation).where(
            SeenConfirmation.report_id == rid, SeenConfirmation.user_id.in_(ids)
        )
    )
    if not existing:
        db.add(SeenConfirmation(report_id=rid, user_id=user.id))
        db.flush()
    count = db.scalar(
        select(func.count()).select_from(SeenConfirmation).where(SeenConfirmation.report_id == rid)
    )
    if count >= 10 and not db.scalar(select(EscalationCase).where(EscalationCase.report_id == rid)):
        case = EscalationCase(report_id=rid, threshold=10)
        db.add(case)
        db.flush()
        audit(db, None, "escalation_case", case.id, "threshold_reached", after={"seen": count})
        notify(
            db,
            report.reporter_id,
            "Your report reached the community threshold",
            "A moderator will review it before any official handoff.",
            f"/i/{report.public_code}",
            f"escalation-threshold:{rid}",
        )
    audit(db, user.id, "report", rid, "seen_confirmed", public=False)
    return {"seen": True, "seen_count": count, "escalation_review": count >= 10}


@router.delete("/reports/{rid}/seen")
def unseen(rid: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    report = reports.get_report(db, rid, user)
    db.execute(
        delete(SeenConfirmation).where(
            SeenConfirmation.report_id == report.id,
            SeenConfirmation.user_id.in_(user_ids(db, user.id)),
        )
    )
    count = db.scalar(
        select(func.count()).select_from(SeenConfirmation).where(SeenConfirmation.report_id == report.id)
    )
    audit(db, user.id, "report", rid, "seen_removed")
    return {"seen": False, "seen_count": count}


@router.get("/reports/{rid}/comments")
def comments(rid: str, user=Depends(optional_user), db=Depends(get_db, scope="function")):
    report = reports.get_report(db, rid, user)
    if report.report_type != "place" or not reports.is_public(report):
        fail("COMMENTS_UNAVAILABLE", "Discussion is unavailable for this report", 403)
    items = db.scalars(
        select(ReportMessage)
        .where(ReportMessage.report_id == rid, ReportMessage.state == "published")
        .order_by(ReportMessage.created_at)
        .limit(200)
    )
    return {"items": [message_data(db, item, user) for item in items]}


@router.post("/reports/{rid}/comments")
@router.post("/reports/{rid}/updates")
def add_message(
    rid: str,
    body: schemas.ReportMessageInput,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
):
    report = reports.get_report(db, rid, user)
    if report.report_type != "place" or not reports.is_public(report):
        fail("COMMENTS_UNAVAILABLE", "Discussion is unavailable for this report", 403)
    if body.kind == "community_update" and report.reporter_id not in user_ids(db, user.id) and user.role == "citizen":
        fail("FORBIDDEN", "Only the reporter or a moderator can post an update", 403)
    if re.search(r"(?:\+?\d[\d\s-]{7,}\d)|(?:[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,})", body.body):
        fail("PERSONAL_INFORMATION", "Remove phone numbers and email addresses", 422)
    item = ReportMessage(report_id=rid, user_id=user.id, kind=body.kind, body=body.body)
    db.add(item)
    db.flush()
    for follower_id in db.scalars(
        select(ReportFollow.user_id).where(ReportFollow.report_id == rid, ReportFollow.user_id != user.id)
    ):
        notify(
            db,
            follower_id,
            "New report update" if body.kind == "community_update" else "New report comment",
            body.body[:140],
            f"/i/{report.public_code}",
            f"report-message:{item.id}:{follower_id}",
        )
    audit(db, user.id, "report_message", item.id, "published")
    return message_data(db, item, user)


@router.post("/reports/{rid}/comments/{message_id}/abuse")
def report_message_abuse(rid: str, message_id: str, body: schemas.Reason,
                         user=Depends(current_user), db=Depends(get_db, scope="function")):
    reports.get_report(db, rid, user)
    item = db.scalar(select(ReportMessage).where(ReportMessage.id == message_id,
                                                  ReportMessage.report_id == rid))
    if not item or item.state != "published":
        fail("COMMENT_NOT_FOUND", "This comment is unavailable", 404)
    if item.user_id in user_ids(db, user.id):
        fail("OWN_COMMENT", "You cannot report your own comment", 403)
    existing = db.scalar(select(ModerationCase).where(
        ModerationCase.report_id == rid, ModerationCase.user_id == user.id,
        ModerationCase.kind == "comment_abuse", ModerationCase.state != "closed",
        ModerationCase.details["message_id"].as_string() == message_id,
    ))
    if existing:
        return {"id": existing.id, "state": existing.state}
    case = ModerationCase(report_id=rid, user_id=user.id, kind="comment_abuse", priority=1,
                          details={"message_id": message_id, "reason": body.reason,
                                   "comment": item.body[:300]})
    db.add(case)
    db.flush()
    audit(db, user.id, "report_message", message_id, "abuse_submitted")
    return {"id": case.id, "state": case.state}


@router.post("/admin/moderation/cases/{case_id}/comment-decision")
def moderate_comment(case_id: str, body: schemas.MessageModeration,
                     user=Depends(moderator), db=Depends(get_db, scope="function")):
    case = db.scalar(select(ModerationCase).where(ModerationCase.id == case_id).with_for_update())
    if not case or case.kind != "comment_abuse":
        fail("NOT_FOUND", "Comment moderation case not found", 404)
    if case.state == "closed":
        return {"id": case.id, "state": case.state, "decision": case.decision}
    item = db.scalar(select(ReportMessage).where(
        ReportMessage.id == case.details.get("message_id")).with_for_update())
    if not item:
        fail("COMMENT_NOT_FOUND", "The reviewed comment no longer exists", 404)
    before = {"state": item.state}
    item.state = {"keep": "published", "restrict": "restricted", "remove": "removed"}[body.decision]
    item.moderated_by = user.id
    item.moderated_at = now()
    case.state = "closed"
    case.decision = f"{body.decision}: {body.reason}"
    case.closed_at = now()
    audit(db, user.id, "report_message", item.id, body.decision, body.reason,
          before=before, after={"state": item.state})
    notify(db, item.user_id, "Comment reviewed",
           "Your comment remains visible." if item.state == "published" else "Your comment was removed from public discussion.",
           f"/reports/{item.report_id}", f"comment-moderation:{item.id}:{item.state}")
    return {"id": case.id, "state": case.state, "decision": body.decision,
            "message_state": item.state}


@router.get("/reports/{rid}/updates")
def updates(rid: str, user=Depends(optional_user), db=Depends(get_db, scope="function")):
    report = reports.get_report(db, rid, user)
    if report.report_type != "place" or not reports.is_public(report):
        fail("UPDATES_UNAVAILABLE", "Updates are unavailable for this report", 403)
    items = db.scalars(
        select(ReportMessage)
        .where(
            ReportMessage.report_id == rid,
            ReportMessage.kind == "community_update",
            ReportMessage.state == "published",
        )
        .order_by(ReportMessage.created_at)
    )
    return {"items": [message_data(db, item, user) for item in items]}


@router.post("/reports/{rid}/follow")
def follow(rid: str, user=Depends(registered), db=Depends(get_db, scope="function")):
    report = reports.get_report(db, rid, user)
    if report.report_type != "place" or not reports.is_public(report):
        fail("FOLLOW_UNAVAILABLE", "Following is unavailable for this report", 403)
    if not db.get(ReportFollow, (rid, user.id)):
        db.add(ReportFollow(report_id=rid, user_id=user.id))
    return {"following": True}


@router.delete("/reports/{rid}/follow")
def unfollow(rid: str, user=Depends(registered), db=Depends(get_db, scope="function")):
    db.execute(
        delete(ReportFollow).where(
            ReportFollow.report_id == rid, ReportFollow.user_id.in_(user_ids(db, user.id))
        )
    )
    return {"following": False}


@router.post("/reports/{rid}/abuse")
def abuse(rid: str, body: schemas.Reason, user=Depends(current_user), db=Depends(get_db, scope="function")):
    # An affected party may know a report ID even after restriction.
    r = db.get(Report, rid)
    if not r:
        fail("NOT_FOUND", "Report not found", 404)
    case = ModerationCase(
        report_id=rid, user_id=user.id, kind="abuse", priority=1, details={"reason": body.reason}
    )
    db.add(case)
    db.flush()
    audit(db, user.id, "report", rid, "abuse_submitted")
    return {"id": case.id, "state": "open"}


@router.post("/appeals")
def appeal(body: schemas.AppealInput, user=Depends(current_user), db=Depends(get_db, scope="function")):
    target = db.get(Report if body.target_type == "report" else CivicAction, body.target_id)
    if not target:
        fail("NOT_FOUND", "Appeal target not found", 404)
    a = Appeal(user_id=user.id, **body.model_dump())
    db.add(a)
    db.flush()
    audit(db, user.id, "appeal", a.id, "submitted")
    return {"id": a.id, "state": "open"}


@router.get("/appeals/me")
def my_appeals(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": a.id,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "reason": a.reason,
                "state": a.state,
                "decision": a.decision,
            }
            for a in db.scalars(
                select(Appeal)
                .where(Appeal.user_id.in_(user_ids(db, user.id)))
                .order_by(Appeal.created_at.desc())
            )
        ]
    }


@router.get("/admin/appeals")
def appeals(user=Depends(moderator), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": a.id,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "reason": a.reason,
                "state": a.state,
            }
            for a in db.scalars(select(Appeal).where(Appeal.state == "open"))
        ]
    }


@router.post("/admin/appeals/{aid}/decision")
def appeal_decision(
    aid: str, body: schemas.Decision, user=Depends(moderator), db=Depends(get_db, scope="function")
):
    a = db.scalar(select(Appeal).where(Appeal.id == aid).with_for_update())
    if not a:
        fail("NOT_FOUND", "Appeal not found", 404)
    if a.user_id in user_ids(db, user.id):
        fail("SELF_APPROVAL", "Another moderator must decide this appeal", 403)
    if a.state != "open":
        return {"state": a.state}
    if body.approved and a.target_type == "report":
        report = db.scalar(select(Report).where(Report.id == a.target_id).with_for_update())
        reports.moderate(db, report, user, "restore", body.reason)
    a.state = "accepted" if body.approved else "rejected"
    a.decision = body.reason
    a.reviewed_by = user.id
    audit(db, user.id, "appeal", aid, a.state, body.reason)
    notify(
        db,
        a.user_id,
        "Appeal reviewed",
        "View the decision on your appeal.",
        "/profile",
        f"appeal:{aid}:{a.state}",
    )
    return {"state": a.state}


@router.get("/admin/moderation/cases")
def cases(user=Depends(moderator), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": c.id,
                "report_id": c.report_id,
                "kind": c.kind,
                "priority": c.priority,
                "state": c.state,
                "details": c.details,
            }
            for c in db.scalars(
                select(ModerationCase)
                .where(ModerationCase.state != "closed")
                .order_by(ModerationCase.priority, ModerationCase.created_at)
                .limit(100)
            )
        ]
    }


@router.get("/admin/moderation/cases/{cid}")
def case_detail(cid: str, user=Depends(moderator), db=Depends(get_db, scope="function")):
    c = db.get(ModerationCase, cid)
    if not c:
        fail("NOT_FOUND", "Case not found", 404)
    return {
        "id": c.id,
        "details": c.details,
        "report": reports.serialize(db, db.get(Report, c.report_id), user, True) if c.report_id else None,
    }


@router.get("/admin/escalation-cases")
def escalation_cases(user=Depends(moderator), db=Depends(get_db, scope="function")):
    def item_data(case):
        report = db.get(Report, case.report_id)
        complaint = db.scalar(select(Complaint).where(Complaint.escalation_id == case.id))
        latest = None
        if complaint:
            latest = db.scalar(
                select(ComplaintStatusEvent)
                .where(ComplaintStatusEvent.complaint_id == complaint.id)
                .order_by(ComplaintStatusEvent.occurred_at.desc())
                .limit(1)
            )
        return {
            "id": case.id,
            "report_id": case.report_id,
            "report_code": report.public_code if report else None,
            "report_title": report.title if report else "Unavailable report",
            "state": case.state,
            "threshold": case.threshold,
            "created_at": case.created_at.isoformat(),
            "complaint": {
                "id": complaint.id,
                "official_id": complaint.official_id,
                "source_name": complaint.source_name,
                "source_url": complaint.source_url,
                "handed_off_at": complaint.handed_off_at.isoformat(),
                "last_checked_at": complaint.last_checked_at.isoformat()
                if complaint.last_checked_at
                else None,
                "latest_status": latest.status if latest else None,
            }
            if complaint
            else None,
        }

    return {
        "items": [item_data(case) for case in db.scalars(
                select(EscalationCase)
                .where(EscalationCase.state != "closed")
                .order_by(EscalationCase.created_at)
            )]
    }


@router.post("/admin/escalation-cases/{case_id}/decision")
def escalation_decision(
    case_id: str,
    body: schemas.EscalationDecision,
    user=Depends(moderator),
    db=Depends(get_db, scope="function"),
):
    case = db.scalar(select(EscalationCase).where(EscalationCase.id == case_id).with_for_update())
    if not case:
        fail("NOT_FOUND", "Escalation case not found", 404)
    if case.state not in {"review", "approved", "declined"}:
        fail("CASE_LOCKED", "This escalation has already been handed off", 409)
    case.state = "approved" if body.approved else "declined"
    case.reviewed_by = user.id
    case.reviewed_at = now()
    case.decision_reason = body.reason
    audit(db, user.id, "escalation_case", case.id, case.state, body.reason)
    return {"id": case.id, "state": case.state}


@router.post("/admin/escalation-cases/{case_id}/handoff")
def escalation_handoff(
    case_id: str,
    body: schemas.ComplaintInput,
    user=Depends(moderator),
    db=Depends(get_db, scope="function"),
):
    case = db.scalar(select(EscalationCase).where(EscalationCase.id == case_id).with_for_update())
    if not case:
        fail("NOT_FOUND", "Escalation case not found", 404)
    old = db.scalar(select(Complaint).where(Complaint.escalation_id == case.id))
    if old:
        return {"id": old.id, "state": case.state, "official_id": old.official_id}
    if case.state != "approved":
        fail("REVIEW_REQUIRED", "Approve this case before recording an external handoff", 409)
    complaint = Complaint(
        escalation_id=case.id,
        handed_off_at=now(),
        **body.model_dump(),
    )
    db.add(complaint)
    case.state = "handed_off"
    db.flush()
    report = db.get(Report, case.report_id)
    audit(
        db,
        user.id,
        "complaint",
        complaint.id,
        "handed_off",
        after={"source": complaint.source_name, "official_id_recorded": bool(complaint.official_id)},
        public=True,
    )
    notify(
        db,
        report.reporter_id,
        "Your report was handed to the civic authority",
        "Open the report for the sourced complaint status.",
        f"/i/{report.public_code}",
        f"complaint-handoff:{complaint.id}",
    )
    return {"id": complaint.id, "state": case.state, "official_id": complaint.official_id}


@router.post("/admin/complaints/{complaint_id}/status")
def complaint_status(
    complaint_id: str,
    body: schemas.ComplaintStatusInput,
    user=Depends(moderator),
    db=Depends(get_db, scope="function"),
):
    complaint = db.scalar(select(Complaint).where(Complaint.id == complaint_id).with_for_update())
    if not complaint:
        fail("NOT_FOUND", "Complaint not found", 404)
    event = ComplaintStatusEvent(
        complaint_id=complaint.id,
        status=body.status,
        occurred_at=body.occurred_at,
        source_note=body.source_note,
        recorded_by=user.id,
    )
    complaint.last_checked_at = now()
    db.add(event)
    db.flush()
    case = db.get(EscalationCase, complaint.escalation_id)
    report = db.get(Report, case.report_id)
    notify(
        db,
        report.reporter_id,
        "Official complaint status updated",
        body.status,
        f"/i/{report.public_code}",
        f"complaint-status:{event.id}",
    )
    audit(db, user.id, "complaint", complaint.id, "status_recorded", after={"status": body.status})
    return {"id": event.id, "status": event.status, "occurred_at": event.occurred_at.isoformat()}


@router.post("/admin/reports/{rid}/decision")
@router.post("/admin/reports/{rid}/visibility")
def review(rid: str, body: schemas.Review, user=Depends(moderator), db=Depends(get_db, scope="function")):
    r = db.scalar(select(Report).where(Report.id == rid).with_for_update())
    if not r:
        fail("NOT_FOUND", "Report not found", 404)
    reports.moderate(db, r, user, body.decision, body.reason)
    return reports.serialize(db, r, user, True)


@router.post("/admin/media/{mid}/redact")
def redaction(
    mid: str, body: schemas.Redaction, user=Depends(moderator), db=Depends(get_db, scope="function")
):
    m = db.scalar(select(Media).where(Media.id == mid).with_for_update())
    if not m or not m.public_key:
        fail("NOT_FOUND", "Processed photo not found", 404)
    redact(m, body.boxes)
    reports.invalidate_cards(db)
    audit(db, user.id, "media", mid, "redacted", after={"boxes": body.boxes})
    return {"id": m.id, "url": f"/api/v1/media/{m.id}/view"}


@router.get("/admin/media/{mid}/original")
def original(mid: str, user=Depends(moderator), db=Depends(get_db, scope="function")):
    m = db.get(Media, mid)
    if not m or m.purged_at:
        fail("NOT_FOUND", "Original not available", 404)
    audit(db, user.id, "media", mid, "original_accessed")
    return Response(
        Storage().get(m.original_key),
        media_type=m.content_type,
        headers={"Cache-Control": "no-store", "Content-Disposition": 'attachment; filename="evidence"'},
    )


@router.post("/admin/reports/{rid}/merge-duplicate/{canonical_id}")
def merge_duplicate(
    rid: str,
    canonical_id: str,
    body: schemas.Reason,
    user=Depends(moderator),
    db=Depends(get_db, scope="function"),
):
    r = reports.get_report(db, rid, user, True)
    c = reports.get_report(db, canonical_id, user, True)
    if r.id == c.id or c.duplicate_of or r.report_type != c.report_type:
        fail("INVALID_DUPLICATE", "Choose an original report of the same type")
    r.duplicate_of = c.id
    r.visibility = "restricted"
    progress.invalidate_report(db, r)
    reports.invalidate_cards(db)
    audit(db, user.id, "report", rid, "duplicate_merged", body.reason, after={"canonical_id": c.id})
    return {"id": rid, "duplicate_of": c.id}


@router.post("/reports/{rid}/resolutions")
def resolution(
    rid: str, body: schemas.ResolutionInput, user=Depends(registered), db=Depends(get_db, scope="function")
):
    r = reports.get_report(db, rid, user)
    if r.report_type != "place" or not reports.is_public(r):
        fail("RESOLUTION_UNAVAILABLE", "Only public Places support resolution proof")
    item = Resolution(report_id=rid, user_id=user.id, description=body.description)
    db.add(item)
    db.flush()
    return {"id": item.id, "state": item.state}


@router.post("/resolutions/{rid}/media/presign")
def resolution_upload(
    rid: str, body: schemas.Upload, user=Depends(registered), db=Depends(get_db, scope="function")
):
    r = db.get(Resolution, rid)
    if not r or r.user_id != user.id or r.state != "draft":
        fail("NOT_FOUND", "Editable resolution not found", 404)
    return authorize_upload(db, user, body, resolution_id=rid)


@router.post("/resolutions/{rid}/submit")
def submit_resolution(rid: str, user=Depends(registered), db=Depends(get_db, scope="function")):
    r = db.get(Resolution, rid)
    if not r or r.user_id != user.id:
        fail("NOT_FOUND", "Resolution not found", 404)
    if not db.scalar(select(Media.id).where(Media.resolution_id == rid, Media.state == "processed")):
        fail("PROOF_REQUIRED", "Upload after-proof first")
    if r.state == "draft":
        r.state = "pending"
    return {"state": r.state}


@router.get("/admin/resolutions")
def resolutions(user=Depends(moderator), db=Depends(get_db, scope="function")):
    return {
        "items": [
            {
                "id": r.id,
                "report_id": r.report_id,
                "description": r.description,
                "state": r.state,
                "media": [
                    {"url": f"/api/v1/media/{m.id}/view", "id": m.id}
                    for m in db.scalars(
                        select(Media).where(Media.resolution_id == r.id, Media.state == "processed")
                    )
                ],
            }
            for r in db.scalars(select(Resolution).where(Resolution.state == "pending"))
        ]
    }


@router.post("/resolutions/{rid}/verify")
def verify_resolution(
    rid: str, body: schemas.VerificationInput, user=Depends(registered), db=Depends(get_db, scope="function")
):
    r = db.scalar(select(Resolution).where(Resolution.id == rid).with_for_update())
    if not r or r.state == "draft":
        fail("NOT_FOUND", "Resolution not found", 404)
    report = reports.get_report(db, r.report_id, user)
    if r.user_id in user_ids(db, user.id) or report.reporter_id in user_ids(db, user.id):
        fail("SELF_VERIFICATION", "Independent verification is required", 403)
    old = db.scalar(
        select(ResolutionVerification).where(
            ResolutionVerification.resolution_id == rid, ResolutionVerification.user_id == user.id
        )
    )
    if not old:
        db.add(ResolutionVerification(resolution_id=rid, user_id=user.id, result=body.result))
    elif old.result != body.result:
        fail("ALREADY_VERIFIED", "Use the appeal flow to dispute your earlier verification", 409)
    if body.result != "confirmed":
        revoke_resolution(db, r, report)
        r.state = "disputed"
        db.add(ModerationCase(report_id=r.report_id, kind="resolution_disputed", priority=1))
    return {"state": r.state}


def revoke_resolution(db, resolution, report):
    for event in db.scalars(
        select(XPEvent).where(
            ((XPEvent.source_id == report.id) & (XPEvent.event_type == "resolved"))
            | ((XPEvent.source_id == resolution.id) & (XPEvent.event_type == "resolution_verification"))
        )
    ):
        progress.reverse(db, event, "resolution_invalidated")
    for verification in db.scalars(
        select(ResolutionVerification).where(ResolutionVerification.resolution_id == resolution.id)
    ):
        verification.accepted = False
    if report.status == "resolved":
        report.status = "open"
        report.resolved_at = None
    reports.invalidate_cards(db)


@router.post("/admin/resolutions/{rid}/decision")
def resolve_decision(
    rid: str, body: schemas.Decision, user=Depends(moderator), db=Depends(get_db, scope="function")
):
    r = db.scalar(select(Resolution).where(Resolution.id == rid).with_for_update())
    if not r or r.state not in {"pending", "disputed", "verified"}:
        fail("NOT_FOUND", "Submitted resolution not found", 404)
    if r.user_id in user_ids(db, user.id):
        fail("SELF_APPROVAL", "Another moderator must review your proof", 403)
    if r.state == "verified" and body.approved:
        return {"state": "verified"}
    report = db.scalar(select(Report).where(Report.id == r.report_id).with_for_update())
    r.state = "verified" if body.approved else "rejected"
    r.reviewed_by = user.id
    if body.approved:
        report.status = "resolved"
        report.resolved_at = now()
        reports.milestone(db, report.id, "resolved", actor_id=user.id)
        progress.verify_report(db, report, "moderator")
        progress.award(db, report.reporter_id, "resolved", "report", report.id, 15)
        for v in db.scalars(
            select(ResolutionVerification).where(
                ResolutionVerification.resolution_id == rid, ResolutionVerification.result == "confirmed"
            )
        ):
            v.accepted = True
            progress.award(db, v.user_id, "resolution_verification", "resolution", rid, 10)
    else:
        revoke_resolution(db, r, report)
    audit(
        db,
        user.id,
        "report",
        report.id,
        "resolved" if body.approved else "resolution_rejected",
        body.reason,
        after={"status": report.status},
        public=True,
    )
    return {"state": r.state}
