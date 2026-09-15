import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select

from .common import notify, user_ids
from .config import settings
from .db import now
from .models import Badge, Dex, Identity, Participation, QuestProgress, Report, User, Verification, XPEvent

TZ = ZoneInfo("Asia/Kolkata")


def award(db, user_id, event_type, source_type, source_id, points, capped=True):
    user = db.get(User, user_id)
    if user.merged_into:
        user_id = user.merged_into
    db.scalar(select(User).where(User.id == user_id).with_for_update())
    ids = user_ids(db, user_id)
    old = list(
        db.scalars(
            select(XPEvent).where(
                XPEvent.user_id.in_(ids), XPEvent.event_type == event_type, XPEvent.source_id == source_id
            )
        )
    )
    if old:
        active = [e for e in old if not db.scalar(select(XPEvent.id).where(XPEvent.reversal_of == e.id))]
        if active:
            return 0
    day = now().astimezone(TZ).date().isoformat()
    if capped:
        used = db.scalar(
            select(func.coalesce(func.sum(XPEvent.points), 0)).where(
                XPEvent.user_id.in_(ids),
                XPEvent.capped.is_(True),
                XPEvent.local_date == day,
                XPEvent.points > 0,
            )
        )
        points = max(0, min(points, settings().report_daily_xp_cap - used))
    e = XPEvent(
        user_id=user_id,
        points=points,
        event_type=event_type,
        source_type=source_type,
        source_id=source_id,
        idempotency_key=f"{event_type}:{source_id}:{user_id}:{len(old)}",
        local_date=day,
        capped=capped,
    )
    db.add(e)
    db.flush()
    if points:
        notify(
            db,
            user_id,
            f"+{points} Civic XP",
            "Your verified contribution is now part of your progress.",
            "/profile",
            f"xp:{e.id}",
        )
    return points


def reverse(db, event, reason="invalidated"):
    if event.points >= 0 and not db.scalar(select(XPEvent).where(XPEvent.reversal_of == event.id)):
        db.add(
            XPEvent(
                user_id=event.user_id,
                points=-event.points,
                event_type="reversal",
                source_type=event.source_type,
                source_id=event.source_id,
                idempotency_key=f"reverse:{event.id}",
                reversal_of=event.id,
                local_date=now().astimezone(TZ).date().isoformat(),
                capped=event.capped,
            )
        )


def invalidate_report(db, report):
    affected = {report.reporter_id}
    for event in db.scalars(select(XPEvent).where(XPEvent.source_id == report.id)):
        reverse(db, event)
    report.verification = "unverified"
    for verifier in db.scalars(select(Verification).where(Verification.report_id == report.id)):
        verifier.accepted = False
        affected.add(verifier.user_id)
    db.flush()
    for user_id in sorted(affected):
        rebuild_progress(db, user_id)


def verify_report(db, report, method):
    if report.verification in {"community", "moderator"}:
        return
    report.verification = method
    if report.report_type == "place":
        reward = {1: 15, 2: 25, 3: 50}.get(report.severity, 25)
        award(db, report.reporter_id, "report_verified", "report", report.id, reward)
    for verification in db.scalars(
        select(Verification).where(Verification.report_id == report.id, Verification.result == "confirmed")
    ):
        verification.accepted = True
        award(db, verification.user_id, "report_verification", "report", report.id, 2)
        rebuild_progress(db, verification.user_id)
    rebuild_progress(db, report.reporter_id)


def rebuild_progress(db, user_id):
    user = db.get(User, user_id)
    user_id = user.merged_into or user_id
    ids = user_ids(db, user_id)
    categories = list(
        db.execute(
            select(Report.category, func.count())
            .where(
                Report.reporter_id.in_(ids),
                Report.report_type == "place",
                Report.verification.in_(["community", "moderator"]),
                Report.status != "rejected",
                Report.duplicate_of.is_(None),
                Report.visibility == "public",
            )
            .group_by(Report.category)
        )
    )
    db.execute(delete(Dex).where(Dex.user_id == user_id))
    for category, count in categories:
        db.add(Dex(user_id=user_id, category=category, verified_count=count))
    count = sum(n for _, n in categories)
    verified_reports = list(
        db.scalars(
            select(Report).where(
                Report.reporter_id.in_(ids),
                Report.report_type == "place",
                Report.verification.in_(["community", "moderator"]),
                Report.visibility == "public",
                Report.duplicate_of.is_(None),
                Report.status != "rejected",
            )
        )
    )
    resolved = [report for report in verified_reports if report.status == "resolved"]
    total = int(
        db.scalar(select(func.coalesce(func.sum(XPEvent.points), 0)).where(XPEvent.user_id.in_(ids)))
    )
    level = 1 + math.isqrt(max(total, 0) // 100)
    days = set(
        db.scalars(select(XPEvent.local_date).where(XPEvent.user_id.in_(ids), XPEvent.points > 0))
    )
    ordered = sorted(days, reverse=True)
    best_streak = current = 0
    previous = None
    for value in ordered:
        day = datetime.fromisoformat(value).date()
        current = current + 1 if previous and previous - day == timedelta(days=1) else 1
        best_streak = max(best_streak, current)
        previous = day
    verified_action = db.scalar(
        select(Participation.action_id).where(
            Participation.user_id.in_(ids), Participation.state == "verified"
        )
    )
    first_assist = db.scalar(
        select(Verification.id).where(
            Verification.user_id.in_(ids), Verification.accepted.is_(True)
        )
    )
    user = db.get(User, user_id)
    ward_count = sum(report.area_id == user.home_area_id for report in verified_reports) if user.home_area_id else 0
    early = any(5 <= report.created_at.astimezone(TZ).hour < 9 for report in verified_reports)
    wanted = {
        "first_verified_report": count >= 1,
        "seven_day_streak": best_streak >= 7,
        "zone_scout": len(categories) >= 3,
        "high_impact_helper": len(resolved) >= 3,
        "first_verified_action": bool(verified_action),
        "neighbourhood_hero": count >= 5,
        "early_bird": early,
        "level_10": level >= 10,
        "first_assist": bool(first_assist),
        "ward_champion": ward_count >= 10,
        "high_severity_fix": any(report.severity == 3 for report in resolved),
        "century_club": total >= 100,
    }
    db.execute(delete(Badge).where(Badge.user_id == user_id))
    for code, earned in wanted.items():
        if earned:
            db.add(Badge(user_id=user_id, code=code, rule_version="v1-mobile"))
    db.flush()
    reconcile_quests(db, user_id)


def reconcile_quests(db, user_id):
    ids = user_ids(db, user_id)
    for claim in db.scalars(
        select(QuestProgress).where(QuestProgress.user_id.in_(ids), QuestProgress.completed.is_(True))
    ):
        if claim.code == "daily_verify_3":
            start = datetime.fromisoformat(claim.period).replace(tzinfo=TZ)
            count = db.scalar(
                select(func.count())
                .select_from(Verification)
                .where(
                    Verification.user_id.in_(ids),
                    Verification.accepted.is_(True),
                    Verification.created_at >= start,
                    Verification.created_at < start + timedelta(days=1),
                )
            )
            eligible = count >= 3
        elif claim.code == "discover_2":
            eligible = db.scalar(select(func.count()).select_from(Dex).where(Dex.user_id == user_id)) >= 2
        elif claim.code == "cleanup":
            eligible = bool(
                db.scalar(
                    select(Participation.action_id).where(
                        Participation.user_id.in_(ids), Participation.state == "verified"
                    )
                )
            )
        else:
            continue
        if not eligible:
            claim.completed = False
            for event in db.scalars(
                select(XPEvent).where(
                    XPEvent.user_id.in_(ids),
                    XPEvent.event_type == "quest",
                    XPEvent.source_id == claim.code + ":" + claim.period,
                )
            ):
                reverse(db, event, "quest_evidence_invalidated")


def profile(db, user, public=False):
    ids = user_ids(db, user.id)
    total = int(db.scalar(select(func.coalesce(func.sum(XPEvent.points), 0)).where(XPEvent.user_id.in_(ids))))
    report_count = db.scalar(
        select(func.count())
        .select_from(Report)
        .where(Report.reporter_id.in_(ids), Report.verification.in_(["community", "moderator"]))
    )
    resolved = db.scalar(
        select(func.count())
        .select_from(Report)
        .where(
            Report.reporter_id.in_(ids),
            Report.status == "resolved",
            Report.verification.in_(["community", "moderator"]),
        )
    )
    level = 1 + math.isqrt(max(total, 0) // 100)
    days = set(db.scalars(select(XPEvent.local_date).where(XPEvent.user_id.in_(ids), XPEvent.points > 0)))
    cursor = now().astimezone(TZ).date()
    if cursor.isoformat() not in days:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor.isoformat() in days:
        streak += 1
        cursor -= timedelta(days=1)
    value = {
        "id": user.id,
        "handle": user.handle,
        "display_name": user.display_name,
        "portrait_id": user.portrait_id,
        "xp": total,
        "level": level,
        "next_level_xp": 100 * level**2,
        "level_start_xp": 100 * (level - 1) ** 2,
        "verified_reports": report_count,
        "resolved_reports": resolved,
        "streak": streak,
        "badges": list(db.scalars(select(Badge.code).where(Badge.user_id == user.id))),
        "civicdex": [
            {"category": d.category, "verified_count": d.verified_count}
            for d in db.scalars(select(Dex).where(Dex.user_id == user.id))
        ],
    }
    if not public:
        value.update(
            identity_type=user.identity_type,
            role=user.role,
            linked_providers=sorted(set(db.scalars(select(Identity.provider).where(Identity.user_id.in_(ids))))),
        )
    else:
        # Private submissions contribute to private progress but never reveal their
        # category or case status through public profile counts or share cards.
        from .reports import public_filter

        visible = list(
            db.scalars(
                select(Report).where(
                    Report.reporter_id.in_(ids),
                    Report.verification.in_(["community", "moderator"]),
                    *public_filter(),
                )
            )
        )
        counts = {}
        for report in visible:
            counts[report.category] = counts.get(report.category, 0) + 1
        value["verified_reports"] = len(visible)
        value["resolved_reports"] = sum(report.status == "resolved" for report in visible)
        value["civicdex"] = [
            {"category": code, "verified_count": count} for code, count in sorted(counts.items())
        ]
    return value


QUESTS = [
    {
        "code": "daily_verify_3",
        "title": "A second pair of eyes",
        "description": "Help verify three nearby Places.",
        "target": 3,
        "xp": 15,
        "period": "daily",
    },
    {
        "code": "discover_2",
        "title": "See your city differently",
        "description": "Verify reports in two different categories.",
        "target": 2,
        "xp": 20,
        "period": "once",
    },
    {
        "code": "cleanup",
        "title": "Leave it better",
        "description": "Complete a verified Civic Action.",
        "target": 1,
        "xp": 25,
        "period": "once",
    },
]


def quests(db, user):
    ids = user_ids(db, user.id)
    day = now().astimezone(TZ).date().isoformat()
    result = []
    for q in QUESTS:
        period = day if q["period"] == "daily" else "once"
        if q["code"] == "daily_verify_3":
            start = now().astimezone(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
            n = db.scalar(
                select(func.count())
                .select_from(Verification)
                .where(
                    Verification.user_id.in_(ids),
                    Verification.accepted.is_(True),
                    Verification.created_at >= start,
                )
            )
        elif q["code"] == "discover_2":
            n = db.scalar(select(func.count()).select_from(Dex).where(Dex.user_id == user.id))
        else:
            n = db.scalar(
                select(func.count())
                .select_from(Participation)
                .where(Participation.user_id.in_(ids), Participation.state == "verified")
            )
        claimed = db.scalar(
            select(QuestProgress).where(
                QuestProgress.user_id.in_(ids),
                QuestProgress.code == q["code"],
                QuestProgress.period == period,
                QuestProgress.completed.is_(True),
            )
        )
        result.append(
            {
                **q,
                "progress": min(n, q["target"]),
                "claimable":