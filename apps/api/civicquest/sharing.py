import io

from fastapi import APIRouter, Depends, Header, Response
from PIL import Image, ImageDraw, ImageFont, ImageOps
from sqlalchemy import select

from . import reports
from .auth import current_user, registered
from .common import enqueue, fail, mutation
from .db import get_db
from .media import Storage
from .models import Area, Media, Participation, Report, Resolution, ShareCard, User
from .progress import profile
from .schemas import Share

router = APIRouter(prefix="/api/v1")


@router.post("/share-cards")
def share(
    body: Share,
    user=Depends(registered),
    db=Depends(get_db, scope="function"),
    idempotency_key: str | None = Header(default=None),
):
    if not user.handle:
        fail("PUBLIC_HANDLE_REQUIRED", "Create your public civic handle first")

    def create():
        if body.kind == "cleanup":
            p = db.get(Participation, (body.action_id, user.id)) if body.action_id else None
            if not p or p.state != "verified":
                fail("VERIFIED_ACTION_REQUIRED", "Complete a verified Civic Action first")
        if body.kind in {"resolved_fix", "before_after"}:
            report = db.get(Report, body.report_id) if body.report_id else None
            resolution = (
                db.scalar(
                    select(Resolution).where(
                        Resolution.report_id == report.id, Resolution.state == "accepted"
                    )
                )
                if report
                else None
            )
            if not report or report.status != "resolved" or not reports.is_public(report) or not resolution:
                fail("VERIFIED_RESOLUTION_REQUIRED", "Choose a public report with accepted resolution proof")
        if body.kind == "ward":
            area = db.get(Area, body.area_id) if body.area_id else None
            if not area or area.area_type != "ward" or not area.active:
                fail("ACTIVE_WARD_REQUIRED", "Choose an active administrative ward")
        item = ShareCard(
            user_id=user.id,
            kind="civic_card" if body.kind == "achievement" else body.kind,
            action_id=body.action_id,
            report_id=body.report_id,
            area_id=body.area_id,
        )
        db.add(item)
        db.flush()
        enqueue(db, "share_card", {"id": item.id}, "card:" + item.id)
        return {"id": item.id, "state": "pending"}

    return mutation(db, user, "share_card", idempotency_key, body.model_dump(), create)


def render_card(db, card):
    user = db.get(User, card.user_id)
    if not user.handle or user.status != "active":
        card.state = "revoked"
        return
    stats = profile(db, user, True)
    report = db.get(Report, card.report_id) if card.report_id else None
    area = db.get(Area, card.area_id) if card.area_id else None
    if report and (report.status != "resolved" or not reports.is_public(report)):
        card.state = "revoked"
        return
    image = Image.new("RGB", (1080, 1350), "#f6f4eb")
    draw = ImageDraw.Draw(image)

    def font(size):
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)

    draw.rounded_rectangle((60, 60, 1020, 1290), radius=40, fill="#153e3b")
    draw.text((110, 115), "CIVICQUEST", font=font(42), fill="#c6f09c")
    headings = {
        "civic_card": ("My city.", "My impact."),
        "monthly": ("A month of", "civic progress."),
        "cleanup": ("We showed up.", "Mumbai changed."),
        "ward": ("Help fix", area.name if area else "our ward."),
        "resolved_fix": ("A civic issue", "was resolved."),
        "before_after": ("Before.", "After. Verified."),
    }
    first, second = headings.get(card.kind, ("Small acts.", "Real impact."))
    draw.text((110, 235), first, font=font(88), fill="white")
    draw.text((110, 350), second, font=font(88), fill="white")
    if card.kind in {"resolved_fix", "before_after"} and report:
        resolution = db.scalar(
            select(Resolution).where(
                Resolution.report_id == report.id, Resolution.state == "accepted"
            )
        )
        before = db.scalar(
            select(Media).where(
                Media.report_id == report.id, Media.state == "processed", Media.public_key.is_not(None)
            )
        )
        after = (
            db.scalar(
                select(Media).where(
                    Media.resolution_id == resolution.id,
                    Media.state == "processed",
                    Media.public_key.is_not(None),
                )
            )
            if resolution
            else None
        )
        if not before or not after:
            card.state = "revoked"
            return

        def safe_photo(media, size):
            with Image.open(io.BytesIO(Storage().get(media.public_key))) as source:
                return ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)

        if card.kind == "before_after":
            image.paste(safe_photo(before, (400, 430)), (110, 520))
            image.paste(safe_photo(after, (400, 430)), (570, 520))
            draw.text((125, 535), "BEFORE", font=font(24), fill="white", stroke_width=2, stroke_fill="#153e3b")
            draw.text((585, 535), "AFTER", font=font(24), fill="white", stroke_width=2, stroke_fill="#153e3b")
        else:
            image.paste(safe_photo(after, (860, 430)), (110, 520))
            draw.text((125, 535), "VERIFIED FIX", font=font(24), fill="white", stroke_width=2, stroke_fill="#153e3b")
        draw.text((110, 1000), report.public_code, font=font(30), fill="#c6f09c")
        draw.text((110, 1055), report.title[:44], font=font(36), fill="white")
        draw.text((110, 1170), "@" + user.handle, font=font(30), fill="white")
        draw.text((110, 1215), "Verified civic outcomes. Mumbai.", font=font(22), fill="#c6f09c")
        out = io.BytesIO()
        image.save(out, format="PNG")
        card.object_key = f"cards/{card.id}.png"
        Storage().put(card.object_key, out.getvalue(), "image/png")
        card.state = "ready"
        return
    label = {
        "cleanup": "VERIFIED CIVIC ACTION",
        "ward": "VERIFIED OUTCOMES THIS PERIOD",
        "resolved_fix": report.public_code if report else "VERIFIED FIX",
        "before_after": report.public_code if report else "VERIFIED BEFORE / AFTER",
    }.get(card.kind, "MY VERIFIED CIVIC IMPACT")
    draw.text((110, 550), label, font=font(30), fill="#c6f09c")
    metric = stats["resolved_reports"] if card.kind == "ward" else stats["xp"]
    draw.text((110, 650), f"{metric:,}", font=font(145), fill="white")
    metric_label = "VERIFIED OUTCOMES" if card.kind == "ward" else "VERIFIED CIVIC XP"
    draw.text((110, 820), metric_label, font=font(32), fill="#c6f09c")
    draw.text(
        (110, 940),
        f"{stats['verified_reports']} reports  |  {stats['resolved_reports']} resolved",
        font=font(34),
        fill="white",
    )
    draw.text((110, 1130), "@" + user.handle, font=font(36), fill="white")
    draw.text((110, 1200), "Level up your city.", font=font(25), fill="#c6f09c")
    out = io.BytesIO()
    image.save(out, format="PNG")
    card.object_key = f"cards/{card.id}.png"
    Storage().put(card.object_key, out.getvalue(), "image/png")
    card.state = "ready"


@router.get("/share-cards/{cid}")
def card_status(cid: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    c = db.get(ShareCard, cid)
    if not c or c.user_id != user.id:
        fail("NOT_FOUND", "Share card not found", 404)
    return {
        "id": c.id,
        "state": c.state,
        "url": f"/api/v1/share-cards/{c.id}/image" if c.state == "ready" else None,
    }


@router.get("/share-cards/{cid}/image")
def card_image(cid: str, db=Depends(get_db, scope="function")):
    c = db.get(ShareCard, cid)
    user = db.get(User, c.user_id) if c else None
    report = db.get(Report, c.report_id) if c and c.report_id else None
    if (
        not c
        or c.state != "ready"
        or not user
        or not user.handle
        or user.status != "active"
        or (report and (report.status != "resolved" or not reports.is_public(report)))
    ):
        fail("NOT_FOUND", "Share card not available", 404)
    return Response(
        Storage().get(c.object_key), media_type="image/png", headers={"Cache-Control": "no-store"}
    )
