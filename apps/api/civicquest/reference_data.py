"""Reviewed civic reference-data imports. UI code must never hardcode office holders."""

from datetime import datetime

from sqlalchemy import func, select, update

from .common import fail
from .geo import point
from .models import Area, Officer, PostalPlace, Representative


def import_representatives(db, document):
    if document.get("type") != "CivicQuestRepresentativeSnapshot" or not document.get("items"):
        fail("INVALID_REPRESENTATIVE_SNAPSHOT", "Use a nonempty representative snapshot")
    snapshot_at = datetime.fromisoformat(document["fetched_at"].replace("Z", "+00:00"))
    seen = set()
    imported = []
    for item in document["items"]:
        required = {"area_code", "area_type", "role", "name", "party", "source_name", "source_id",
                    "source_url", "effective_from", "reviewed"}
        if not required.issubset(item) or item["role"] not in {"MLA", "MP"}:
            fail("INVALID_REPRESENTATIVE_SNAPSHOT", "Every representative needs role, area and provenance")
        key = (item["source_name"], str(item["source_id"]))
        if key in seen:
            fail("INVALID_REPRESENTATIVE_SNAPSHOT", "Representative source IDs must be unique")
        seen.add(key)
        area = db.scalar(select(Area).where(Area.code == item["area_code"],
                                            Area.area_type == item["area_type"], Area.active.is_(True)))
        if not area:
            fail("REPRESENTATIVE_AREA_MISSING", f"Import boundary {item['area_code']} first", 409)
        row = db.scalar(select(Representative).where(Representative.source_name == item["source_name"],
                                                     Representative.source_id == str(item["source_id"])))
        if not row:
            row = Representative(source_name=item["source_name"], source_id=str(item["source_id"]),
                                 name=item["name"], role=item["role"], area_id=area.id,
                                 source_url=item["source_url"], effective_from=item["effective_from"])
            db.add(row)
        row.name = item["name"].strip()
        row.role = item["role"]
        row.area_id = area.id
        row.party = item["party"].strip()
        row.photo_url = item.get("photo_url") or None
        row.source_url = item["source_url"]
        row.effective_from = item["effective_from"]
        row.effective_to = item.get("effective_to")
        row.reviewed = bool(item["reviewed"])
        row.fetched_at = snapshot_at
     