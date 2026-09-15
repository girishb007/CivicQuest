import math
from datetime import timedelta

from sqlalchemy import delete, func, select

from .db import now
from .geo import coords
from .models import Category, Hotspot, HotspotReport, Report, User, Vote
from .reports import public_filter


def rebuild_hotspots(db):
    # One worker owns the projection rebuild across concurrent queue deliveries.
    db.execute(select(func.pg_advisory_xact_lock(731930)))
    reports = list(
        db.scalars(
            select(Report)
            .where(
                *public_filter(), Report.status != "resolved", Report.created_at >= now() - timedelta(days=30)
            )
            .order_by(Report.created_at, Report.id)
        )
    )
    cats = {c.code: c.family for c in db.scalars(select(Category))}
    unassigned = {r.id: r for r in reports}
    rank = {r.id: index for index, r in enumerate(reports)}
    canonical = {user.id: user.merged_into or user.id for user in db.scalars(select(User))}
    db.execute(delete(HotspotReport))
    for h in db.scalars(select(Hotspot)):
        h.active = False
    for anchor in reports:
        if anchor.id not in unassigned:
            continue
        nearby = set(
            db.scalars(
                select(Report.id).where(
                    *public_filter(),
                    Report.status != "resolved",
                    Report.created_at >= now() - timedelta(days=30),
                    Report.area_id == anchor.area_id,
                    Report.category.in_(
                        [code for code, family in cats.items() if family == cats[anchor.category]]
                    ),
                    func.ST_DWithin(Report.location, anchor.location, 150),
                )
            )
        )
        group = [unassigned[rid] for rid in sorted(nearby & unassigned.keys(), key=rank.__getitem__)]
        for r in group:
            unassigned.pop(r.id, None)
        unique = len({canonical.get(r.reporter_id, r.reporter_id) for r in group})
        if unique < 3:
            continue
        votes = db.scalar(
            select(func.count()).select_from(Vote).where(Vote.report_id.in_([r.id for r in group]))
        )
        days = max(0, (now() - max(r.created_at for r in group)).total_seconds() / 86400)
        score = (
            (1 + math.log1p(votes))
            * math.log1p(unique)
            * (sum(r.severity for r in group) / len(group))
            * math.exp(-days / 7)
        )
        h = db.scalar(select(Hotspot).where(Hotspot.anchor_id == anchor.id))
        if not h:
            h = Hotspot(
                anchor_id=anchor.id,
                name=anchor.address,
                family=cats[anchor.category],
                area_id=anchor.area_id,
                location=anchor.location,
            )
            db.add(h)
            db.flush()
        h.active = True
        h.score = score
        for r in group:
            db.add(HotspotReport(report_id=r.id, hotspot_id=h.id))


def hotspot_data(db, h):
    ids = list(
        db.scalars(
            select(HotspotReport.report_id)
            .join(Report, Report.id == HotspotReport.report_id)
            .where(HotspotReport.hotspot_id == h.id, *public_filter())
        )
    )
    return {
        "id": h.id,
        "name": h.name,
        "family": h.family,
        **coords(h.location),
        "report_count": len(ids),
        "upvotes": db.scalar(select(func.count()).select_from(Vote).where(Vote.report_id.in_(ids))),
        "score": round(h.score, 2),
        "report_ids": ids,
        "owner_label": "Owner not confirmed",
    }
