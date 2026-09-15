"""Synthetic fixtures only: no real people, allegations, or official ward geometry."""

import io
import json
import uuid
from datetime import timedelta
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy import select

from .common import audit, digest
from .config import settings
from .db import now
from .geo import import_geojson, point
from .media import Storage, decode
from .models import (
    Area,
    Category,
    CivicAction,
    CommunityGroup,
    Identity,
    Media,
    Officer,
    Report,
    Representative,
    User,
    WardGoal,
)
from .progress import verify_report

CATEGORIES = [
    ("garbage_dump", "Garbage / illegal dumping", "place", "waste"),
    ("overflowing_bin", "Overflowing bins", "place", "waste"),
    ("pothole", "Potholes", "place", "roads"),
    ("water_leak", "Water leakage", "place", "water"),
    ("open_drain", "Open drains", "place", "water"),
    ("littering", "Littering", "civic_catch", "behavior"),
    ("spitting", "Spitting", "civic_catch", "behavior"),
    ("public_urination", "Public urination", "civic_catch", "behavior"),
    ("prohibited_smoking", "Prohibited smoking", "civic_catch", "behavior"),
]


def fixed(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://civicquest.demo/" + name))


def illustration(kind, index=0):
    image = Image.new("RGB", (800, 500), "#dce4d3")
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 800, 150), fill="#cbdbe2")
    for i in range(10):
        x = i * 95 - 20
        top = 45 + (i % 3) * 22
        d.rectangle((x, top, x + 85, 230), fill=["#d2c9b7", "#e6dfca", "#c2cab9"][i % 3])
        for y in range(top + 20, 215, 35):
            for xx in [x + 15, x + 47]:
                d.rectangle((xx, y, xx + 15, y + 20), fill="#a0afa4")
    d.polygon([(0, 320), (800, 205), (800, 500), (0, 500)], fill="#adada0")
    d.line((0, 320, 800, 205), fill="#e5dfc7", width=12)
    d.line((0, 380, 800, 260), fill="#d5d1b9", width=5)
    for x, y in [(60, 240), (630, 170), (750, 180)]:
        d.rectangle((x, y - 50, x + 10, y + 45), fill="#867b59")
        d.ellipse((x - 40, y - 115, x + 50, y - 30), fill="#8ba17d")
        d.ellipse((x - 25, y - 140, x + 60, y - 70), fill="#98ae88")
    if kind == "pothole":
        d.ellipse((250, 330, 580, 460), fill="#838574")
        d.ellipse((270, 345, 565, 445), fill="#646b5d")
        d.line((200, 440, 250, 380, 310, 365), fill="#717a69", width=6)
    elif kind in {"water_leak", "open_drain"}:
        d.ellipse((250, 295, 680, 420), fill="#829e9f")
        d.ellipse((350, 315, 630, 360), fill="#a7bec0")
        d.line((340, 250, 370, 330), fill="#789a9a", width=13)
    else:
        for x, y, color in [
            (390, 260, "#758b63"),
            (440, 295, "#b5aa8e"),
            (505, 285, "#9b936e"),
            (370, 320, "#dad0b3"),
            (535, 345, "#c4b78e"),
        ]:
            d.rounded_rectangle((x, y, x + 80, y + 65), radius=20, fill=color)
        d.rounded_rectangle((190, 215, 290, 350), radius=10, fill="#719075")
        d.rectangle((180, 211, 300, 225), fill="#4f6d53")
    d.rounded_rectangle((20, 460, 208, 488), radius=5, fill="#f7f8ed")
    d.text((30, 468), "ILLUSTRATIVE DEMO IMAGE", fill="#52674c")
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=88)
    return out.getvalue()


def seed(db):
    cfg = settings()
    if not cfg.demo_mode or cfg.env not in {"local", "test"}:
        raise RuntimeError("Demo seed is forbidden in live environments")
    if db.get(User, fixed("maya")):
        seed_electoral_context(db)
        return
    for code, name, typ, family in CATEGORIES:
        if not db.get(Category, code):
            db.add(Category(code=code, name=name, report_type=typ, family=family))

    def polygon(code, name, typ, x1, y1, x2, y2):
        return {
            "type": "Feature",
            "properties": {"code": code, "name": name, "area_type": typ},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]],
            },
        }

    document = {
        "type": "FeatureCollection",
        "features": [
            polygon(
                "demo-mumbai", "Greater Mumbai — illustrative extent", "city", 72.75, 18.85, 73.02, 19.35
            ),
            polygon("demo-central", "Demo central neighborhood", "ward", 72.79, 18.97, 72.94, 19.09),
            polygon("demo-north", "Demo northern neighborhood", "ward", 72.79, 19.09, 72.98, 19.30),
            polygon("demo-south", "Demo southern neighborhood", "ward", 72.79, 18.85, 72.94, 18.97),
        ],
    }
    import_geojson(
        db,
        document,
        {
            "name": "CivicQuest illustrative geography",
            "version": "1",
            "source_url": "https://example.invalid/civicquest-synthetic",
            "license": "CC0-1.0 (synthetic geometry authored for this project)",
            "reviewed": False,
            "synthetic": True,
        },
    )
    data_dir = Path("data/samples")
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "mumbai-demo.geojson").write_text(json.dumps(document, indent=2))
    area = db.scalar(select(Area).where(Area.code == "demo-central"))
    for persona, name, role in [
        ("maya", "Maya Rao", "citizen"),
        ("arjun", "Arjun Shah", "citizen"),
        ("moderator", "Demo reviewer", "moderator"),
        ("admin", "Demo administrator", "admin"),
        ("isha", "Isha Mehta", "citizen"),
        ("dev", "Dev Patil", "citizen"),
    ]:
        user = User(
            id=fixed(persona),
            identity_type="registered",
            role=role,
            display_name=name,
            handle=persona + "_demo",
            home_area_id=area.id,
        )
        db.add(user)
        db.flush()
        db.add(Identity(user_id=user.id, provider="demo", subject=persona))
    db.flush()
    seeds = [
        ("garbage_dump", "A cleaner corner starts here", "Dadar West", "maya", 19.018, 72.842),
        ("pothole", "Let’s make this walk a smoother one", "Shivaji Park", "arjun", 19.026, 72.838),
        ("water_leak", "A little leak with a big impact", "Matunga", "isha", 19.028, 72.852),
        ("overflowing_bin", "This bin could use a fresh start", "Prabhadevi", "dev", 19.014, 72.831),
        ("garbage_dump", "Help bring attention to this spot", "Dadar West", "isha", 19.0182, 72.8422),
        ("garbage_dump", "A shared street deserves some care", "Dadar West", "dev", 19.0184, 72.8424),
    ]
    approved = []
    for i, (category, title, address, persona, lat, lng) in enumerate(seeds):
        rid = fixed("report-" + str(i))
        r = Report(
            id=rid,
            reporter_id=fixed(persona),
            report_type="place",
            category=category,
            title=title,
            description="An illustrative report for exploring CivicQuest. This does not describe an actual incident.",
            location=point(lat, lng),
            address=address + ", Mumbai",
            area_id=area.id,
            status="open",
            visibility="public",
            demo=True,
            finalized_at=now(),
            created_at=now() - timedelta(hours=i + 1),
        )
        db.add(r)
        db.flush()
        raw = illustration(category, i)
        clean, phash = decode(raw, "image/jpeg")
        mid = fixed("media-" + str(i))
        original = "original/" + mid
        public = "public/" + mid + ".jpg"
        Storage().put(original, raw, "image/jpeg")
        Storage().put(public, clean, "image/jpeg")
        db.add(
            Media(
                id=mid,
                owner_id=fixed(persona),
                report_id=rid,
                role="evidence",
                original_key=original,
                public_key=public,
                content_type="image/jpeg",
                size=len(raw),
                sha256=digest(raw),
                phash=phash,
                state="processed",
                upload_token_hash=digest(mid),
                upload_expires=now(),
                flags={"safe": True, "synthetic": True, "flags": []},
            )
        )
        approved.append(digest(raw))
        (data_dir / (category + ".jpg")).write_bytes(raw)
        audit(db, None, "report", r.id, "published", after={"status": "open"}, public=True)
        if i < 3:
            verify_report(db, r, "moderator")
    (data_dir / "approved-images.json").write_text(json.dumps(approved))
    for i, (title, loc, lat, lng) in enumerate(
        [
            ("A brighter morning at Juhu", "Juhu Beach", 19.10, 72.826),
            ("Little steps, cleaner streets", "Dadar community meeting point", 19.018, 72.842),
        ]
    ):
        db.add(
            CivicAction(
                id=fixed("action-" + str(i)),
                created_by=fixed("admin"),
                title=title,
                description="An illustrative community cleanup. Try joining, checking in, and submitting before/after proof in the local demo.",
                organizer="CivicQuest demo community",
                location_name=loc,
                location=point(lat, lng),
                starts_at=now() - timedelta(minutes=10),
                ends_at=now() + timedelta(hours=6),
                capacity=50,
                status="published",
                demo=True,
            )
        )
    db.flush()
    from .attention import rebuild_hotspots

    rebuild_hotspots(db)
    seed_electoral_context(db)


def seed_electoral_context(db):
    """Independent, additive fixtures; never change existing citizen reports."""
    features = []
    for code, name, kind, left, right in [
        ("demo-assembly-west", "Demo western assembly constituency", "assembly_constituency", 72.79, 72.845),
        ("demo-assembly-east", "Demo eastern assembly constituency", "assembly_constituency", 72.845, 72.98),
        ("demo-parliament", "Demo parliamentary constituency", "parliamentary_constituency", 72.79, 72.98),
    ]:
        features.append({"type": "Feature", "properties": {"code": code, "name": name, "area_type": kind},
                         "geometry": {"type": "Polygon", "coordinates": [
                             [[left, 18.85], [right, 18.85], [right, 19.30], [left, 19.30], [left, 18.85]]
                         ]}})
    dataset = import_geojson(db, {"type": "FeatureCollection", "features": features}, {
        "name": "CivicQuest illustrative electoral geography", "version": "1",
        "source_url": "https://example.invalid/civicquest-synthetic-electoral", "license": "CC0-1.0",
        "reviewed": False, "synthetic": True,
    })
    for area in db.scalars(select(Area).where(Area.dataset_id == dataset.id)):
        rid = fixed("representative-" + area.code)
        if not db.get(Representative, rid):
            db.add(Representative(id=rid, name="Fictional " + ("MP" if area.area_type == "parliamentary_constituency"
                                                           else "MLA") + " — demo context only",
                                  role="MP" if area.area_type == "parliamentary_constituency" else "MLA",
                                  area_id=area.id, source_url=dataset.source_url, reviewed=True,
                                  effective_from="2020-01-01"))
    db.flush()
    goal_id = fixed("central-ward-goal")
    central = db.scalar(select(Area).where(Area.code == "demo-central", Area.active.is_(True)))
    if central and not db.get(WardGoal, goal_id):
        db.add(WardGoal(id=goal_id, created_by=fixed("admin"), area_id=central.id,
                        title="Five verified outcomes, one shared neighborhood", target=5,
                        starts_at=now()-timedelta(days=7), ends_at=now()+timedelta(days=23),
                        status="published"))
        db.flush()
    group_id = fixed("demo-community-group")
    if central and not db.get(CommunityGroup, group_id):
        db.add(
            CommunityGroup(
                id=group_id,
                name="Demo Neighbourhood Cleanup Circle",
                description="An illustrative directory entry for testing external community contact flows.",
                area_id=central.id,
                coverage_text="Demo central neighborhood",
                contact_url="https://example.invalid/demo-community-group",
                source_url="https://example.invalid/civicquest-synthetic-groups",
                source_name="CivicQuest synthetic fixture",
                verified_at=now(),
                reviewed=True,
                statistics={},
            )
        )
    officer_id = fixed("demo-officer")
    if central and not db.get(Officer, officer_id):
        db.add(
            Officer(
                id=officer_id,
                name="Demo Ward Response Desk",
                title="Illustrative civic contact",
                department="Synthetic ward operations",
                area_id=central.id,
                category_family="waste",
                reason="Displayed only to exercise sourced contact presentation in local demo mode.",
                source_url="https://example.invalid/civicquest-synthetic-officers",
                verified_at=now(),
                official_url="https://example.invalid/demo-officer",
                reviewed=True,
            )
        )
    db.flush()
