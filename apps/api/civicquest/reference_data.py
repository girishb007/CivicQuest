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
        imported.append(row)
    db.flush()
    return imported


def import_postal_places(db, rows, metadata):
    required = {"source_url", "version", "fetched_at"}
    if not required.issubset(metadata):
        fail("POSTAL_PROVENANCE_REQUIRED", "Postal source, version and fetch time are required")
    fetched_at = datetime.fromisoformat(metadata["fetched_at"].replace("Z", "+00:00"))
    db.execute(update(PostalPlace).values(active=False))
    imported = []
    seen = set()
    for item in rows:
        if item.get("District", "").strip().upper() not in {"MUMBAI", "MUMBAI SUBURBAN"}:
            continue
        code, office = item.get("Pincode", "").strip(), item.get("OfficeName", "").strip()
        key = (code, office)
        if len(code) != 6 or not code.isdigit() or not office or key in seen:
            continue
        seen.add(key)
        try:
            lat, lng = float(item["Latitude"]), float(item["Longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        # Keep only points inside the active Greater Mumbai coverage polygon.
        covered = db.scalar(select(Area.id).where(Area.area_type == "city", Area.active.is_(True),
                                                  func.ST_Covers(Area.boundary, point(lat, lng))))
        if not covered:
            continue
        row = db.scalar(select(PostalPlace).where(PostalPlace.pincode == code,
                                                  PostalPlace.office_name == office))
        if not row:
            row = PostalPlace(pincode=code, office_name=office, district=item["District"],
                              location=point(lat, lng), source_url=metadata["source_url"],
                              source_version=metadata["version"], fetched_at=fetched_at)
            db.add(row)
        else:
            row.location = point(lat, lng)
            row.district = item["District"]
            row.source_url = metadata["source_url"]
            row.source_version = metadata["version"]
            row.fetched_at = fetched_at
            row.active = True
        imported.append(row)
    db.flush()
    return imported


def import_bmc_ward_offices(db, document, metadata):
    required = {"source_url", "verified_at"}
    if document.get("type") != "FeatureCollection" or not required.issubset(metadata):
        fail("INVALID_BMC_OFFICE_SNAPSHOT", "BMC office features need source and verification time")
    verified_at = datetime.fromisoformat(metadata["verified_at"].replace("Z", "+00:00"))
    imported = []
    for feature in document.get("features", []):
        properties = feature.get("properties", {})
        ward_code = properties.get("WARD_NAME", "").strip()
        area = db.scalar(select(Area).where(Area.code == "BMC-" + ward_code.replace("/", "-"),
                                            Area.area_type == "ward", Area.active.is_(True)))
        if not area:
            fail("BMC_WARD_MISSING", f"Import BMC ward {ward_code} before its office", 409)
        contacts = [("BMC Ward Office", properties.get("BRD_LINE_N")),
                    ("BMC Ward Control Room", properties.get("CNTRL_ROOM"))]
        for title, phone in contacts:
            phone = (phone or "").strip()
            if len(phone.replace("-", "")) < 8:
                continue
            row = db.scalar(select(Officer).where(Officer.area_id == area.id, Officer.title == title,
                                                  Officer.source_url == metadata["source_url"]))
            if not row:
                row = Officer(name=f"{ward_code} {title}", title=title,
                              department="Brihanmumbai Municipal Corporation", area_id=area.id,
                              reason="Official administrative ward contact published by BMC. Operational "
                                     "ownership still depends on the issue category.",
                              source_url=metadata["source_url"], verified_at=verified_at, phone=phone,
                              official_url=metadata["source_url"], reviewed=True)
                db.add(row)
            else:
                row.name, row.phone, row.verified_at = f"{ward_code} {title}", phone, verified_at
                row.reviewed, row.effective_to = True, None
            imported.append(row)
    db.flush()
    return imported
