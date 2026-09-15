from sqlalchemy import delete, func, select

from .common import audit, user_ids
from .models import (
    Identity,
    Participation,
    Report,
    ReportFollow,
    ReportMessage,
    SeenConfirmation,
    Session,
    User,
    Verification,
    Vote,
    XPEvent,
)
from .progress import invalidate_report, rebuild_progress, reverse


def link_identity(db, guest, provider, subject, email=None, name=None):
    db.scalar(select(User).where(User.id == guest.id).with_for_update())
    identity = db.scalar(select(Identity).where(Identity.provider == provider, Identity.subject == subject))
    if not identity:
        guest.identity_type = "registered"
        guest.email = email
        if name:
            guest.display_name = name[:60]
        db.add(Identity(user_id=guest.id, provider=provider, subject=subject))
        audit(db, guest.id, "user", guest.id, "account_linked")
        return guest
    target = db.scalar(select(User).where(User.id == identity.user_id).with_for_update())
    if target.id == guest.id:
        return target
    # Never silently merge two registered identities through an ordinary login.
    if guest.identity_type == "registered":
        return target
    aliases = user_ids(db, guest.id)
    # Preserve an established account's choice; otherwise carry over the guest's portrait.
    if target.portrait_id is None:
        target.portrait_id = guest.portrait_id
    for source in db.scalars(select(User).where(User.id.in_(aliases))):
        source.merged_into = target.id
        source.status = "merged"
        source.handle = None
    for session in db.scalars(select(Session).where(Session.user_id.in_(aliases))):
        session.revoked = True
    for source in list(db.scalars(select(Vote).where(Vote.user_id.in_(aliases)))):
        if not db.get(Vote, (source.report_id, target.id)):
            db.add(Vote(report_id=source.report_id, user_id=target.id))
        db.delete(source)
        db.flush()
    for model in (SeenConfirmation, ReportFollow):
        for source in list(db.scalars(select(model).where(model.user_id.in_(aliases)))):
            if db.get(model, (source.report_id, target.id)):
                db.delete(source)
            else:
                source.user_id = target.id
            db.flush()
    for source in db.scalars(select(ReportMessage).where(ReportMessage.user_id.in_(aliases))):
        source.user_id = target.id
    for source in list(db.scalars(select(Verification).where(Verification.user_id.in_(aliases)))):
        if db.scalar(
            select(Verification).where(
                Verification.report_id == source.report_id, Verification.user_id == target.id
            )
        ):
            db.delete(source)
        else:
            source.user_id = target.id
    for source in list(db.scalars(select(Participation).where(Participation.user_id.in_(aliases)))):
        existing = db.get(Participation, (source.action_id, target.id))
        if existing:
            if source.state == "verified" and existing.state != "verified":
                existing.state = source.state
                existing.checked_in_at = source.checked_in_at
            db.delete(source)
        else:
            source.user_id = target.id
    db.flush()
    ids = user_ids(db, target.id)
    # Linking a guest's reports can turn an existing vote/verification into a self-action.
    owned = select(Report.id).where(Report.reporter_id.in_(ids))
    db.execute(delete(Vote).where(Vote.user_id.in_(ids), Vote.report_id.in_(owned)))
    invalid = list(
        db.scalars(
            select(Verification).where(Verification.user_id.in_(ids), Verification.report_id.in_(owned))
        )
    )
    affected = {v.report_id for v in invalid}
    for verification in invalid:
        for event in db.scalars(
            select(XPEvent).where(
                XPEvent.user_id.in_(ids),
                XPEvent.source_id == verification.report_id,
                XPEvent.event_type == "report_verification",
            )
        ):
            reverse(db, event, "account_merge_self_verification")
        db.delete(verification)
    db.flush()
    for report_id in affected:
        report = db.get(Report, report_id)
        confirmations = db.scalar(
            select(func.count())
            .select_from(Verification)
            .where(Verification.report_id == report_id, Verification.result == "confirmed")
        )
        if report.verification == "community" and confirmations < 2:
            invalidate_report(db, report)
    seen = set()
    for event in db.scalars(
        select(XPEvent)
        .where(XPEvent.user_id.in_(ids), XPEvent.points >= 0)
        .order_by(XPEvent.created_at, XPEvent.id)
    ):
        if db.scalar(select(XPEvent.id).where(XPEvent.reversal_of == event.id)):
            continue
        key = (event.event_type, event.source_type, event.source_id)
        if key in seen:
            reverse(db, event, "account_merge")
        else:
            seen.add(key)
    audit(db, target.id, "user", guest.id, "guest_merged", after={"canonical_user_id": target.id})
    rebuild_progress(db, target.id)
    return target
