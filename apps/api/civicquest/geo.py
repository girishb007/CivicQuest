import hashlib
import json
from datetime import date
from zoneinfo import ZoneInfo

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import MultiPolygon, Point, shape
from sqlalchemy import cast, func, select

from .common import fail
from .db import now
from .models import Area, Authority, Category, Dataset, Report, Representative

AREA_TYPES = {"city", "ward", "assembly_constituency", "parliamentary_constituency"}


def effective(model):
    today = now().astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat()
    return [
        model.effective_from.is_(None) | (model.effective_from <= today),
        model.effective_to.is_(None) | (model.effective_to >= today),
    ]


def current_areas():
    return [Area.active.is_(True), *effective(Area)]


def area_reports(area):
    """Count coordinates within the actual polygon, never whole overlapping wards."""
    from .reports import public_filter

    return [func.ST_Covers(area.boundary, cast(Report.location, Geometry("POINT", srid=4326))),
            *public_filter()]


def point(lat, lng):
    return from_shape(Point(lng, lat), srid=4326)


def coords(location):
    p = to_shape(location)
    return {"lat": p.y, "lng": p.x}


def coverage(db, lat, lng):
    matches = list(
        db.scalars(select(Area).where(*current_areas(), func.ST_Covers(Area.boundary, point(lat, lng)))
                   .order_by(Area.area_type, Area.code, Area.id))
    )
    cities = [a for a in matches if a.area_type == "city"]
    if not cities:
        fail("OUTSIDE_COVERAGE", "Choose a location within supported Greater Mumbai coverage")
    wards = [a for a in matches if a.area_type == "ward"]
    return wards[0] if len(wards) == 1 else None, matches


def accountability(db, lat, lng, category):
    area, matches = coverage(db, lat, lng)
    rules = (
        list(
            db.scalars(
                select(Authority).where(
                    Authority.area_id == area.id,
                    Authority.category_family == category.family,
                    Authority.reviewed.is_(True),
                    *effective(Authority),
                )
            )
        )
        if area
        else []
    )
    owner = rules[0] if len(rules) == 1 else None
    reps = list(
        db.scalars(
            select(Representative).where(
                Representative.area_id.in_([a.id for a in matches]),
                Representative.reviewed.is_(True),
                *effective(Representative),
            )
        )
    )
    return {
        "area": {"id": area.id, "name": area.name} if area else None,
        "authority": {
            "id": owner.id,
            "name": owner.name,
            "department": owner.department,
            "source_url": owner.source_url,
        }
        if owner
        else None,
        "label": owner.name if owner else "Owner not confirmed",
        "ambiguous": len([a for a in matches if a.area_type == "ward"]) > 1,
        "representatives": [{"name": r.name, "role": r.role, "party": r.party,
                             "photo_url": r.photo_url, "source_url": r.source_url,
                             "source_name": r.source_name, "fetched_at": r.fetched_at} for r in reps],
        "synthetic": any(db.get(Dataset, a.dataset_id).synthetic for a in matches),
    }


def area_details(db, area_id, user=None):
    """Safe, factual public projection for a ward or constituency page."""
    from .reports import serialize_many

    area = db.scalar(select(Area).where(Area.id == area_id, *current_areas()))
    if not area:
        fail("AREA_NOT_FOUND", "This area is not available", 404)
    dataset = db.get(Dataset, area.dataset_id)
    base = area_reports(area)
    status = dict(db.execute(select(Report.status, func.count()).where(*base).group_by(Report.status)).all())
    average_open_days = db.scalar(select(func.avg(
        func.extract("epoch", now() - Report.created_at) / 86400.0
    )).where(*base, Report.status != "resolved"))
    total = sum(status.values())
    categories = dict(
        db.execute(
            select(Category.name, func.count())
            .join(Report, Report.category == Category.code)
            .where(*base)
            .group_by(Category.name)
            .order_by(func.count().desc(), Category.name)
        ).all()
    )
    contexts = list(
        db.scalars(
            select(Area).where(
                *current_areas(),
                Area.id != area.id,
                Area.area_type.in_(["ward", "assembly_constituency", "parliamentary_constituency"]),
                func.ST_Relate(Area.boundary, area.boundary, "T********"),
            ).order_by(Area.area_type, Area.name, Area.id)
        )
    )
    context_ids = [area.id, *(a.id for a in contexts)]
    representatives = list(db.scalars(select(Representative).where(
        Representative.area_id.in_(context_ids), Representative.reviewed.is_(True),
        *effective(Representative),
    ).order_by(Representative.role, Representative.name, Representative.id)))
    recent = db.scalars(select(Report).where(*base).order_by(Report.created_at.desc(), Report.id).limit(30))
    return {
        "id": area.id,
        "code": area.code,
        "name": area.name,
        "area_type": area.area_type,
        "synthetic": dataset.synthetic,
        "effective_from": area.effective_from,
        "effective_to": area.effective_to,
        "provenance": {
            "dataset": dataset.name,
            "version": dataset.version,
            "source_url": dataset.source_url,
            "license": dataset.license,
            "reviewed": dataset.reviewed,
        },
        "statistics": {
            "total_reports": total,
            "active": sum(count for state, count in status.items() if state != "resolved"),
            "resolved": status.get("resolved", 0),
            "by_status": status,
            "by_category": categories,
            "average_open_days": round(max(0, float(average_open_days)), 1) if average_open_days is not None else None,
            "resolution_rate": round(status.get("resolved", 0) / total, 4) if total else None,
            "rate_note": "Resolved public reports divided by all eligible public reports in this boundary, all time.",
            "counting_method": "Public report coordinates covered by this area's current boundary",
            "boundary_note": "Reports on shared edges may appear in both areas; area totals are not additive.",
        },
        "constituencies": [
            {"id": item.id, "name": item.name, "area_type": item.area_type} for item in contexts
            if item.area_type != "ward"
        ],
        "wards": [
            {"id": item.id, "name": item.name, "area_type": item.area_type} for item in contexts
            if item.area_type == "ward"
        ],
        "context_note": "Linked areas overlap this boundary; they are not a whole-ward assignment.",
        "representatives": [
            {
                "name": person.name,
                "role": person.role,
                "party": person.party,
                "photo_url": person.photo_url,
                "source_name": person.source_name,
                "source_id": person.source_id,
                "fetched_at": person.fetched_at,
                "source_url": person.source_url,
                "area_id": person.area_id,
                "effective_from": person.effective_from,
                "effective_to": person.effective_to,
                "reviewed": person.reviewed,
            }
            for person in representatives
        ],
        "reports": serialize_many(db, recent, user),
    }


def import_geojson(db, document, metadata):
    required = {"name", "version", "source_url", "license", "reviewed", "synthetic"}
    if not required.issubset(metadata):
        fail(
            "DATA_PROVENANCE_REQUIRED",
            "Name, version, source, license, review and synthetic status are required",
        )
    if document.get("type") != "FeatureCollection" or not document.get("features"):
        fail("INVALID_DATASET", "GeoJSON must contain features")
    if not isinstance(metadata["reviewed"], bool) or not isinstance(metadata["synthetic"], bool):
        fail("INVALID_DATASET", "Review and synthetic flags must be booleans")
    if any(not isinstance(metadata[key], str) or not metadata[key].strip()
           for key in required - {"reviewed", "synthetic"}):
        fail("DATA_PROVENANCE_REQUIRED", "Dataset provenance fields must be nonempty text")
    # Validate the entire document before inserting even the dataset row.
    validated = []
    seen = set()
    for feature in document["features"]:
        try:
            properties = feature["properties"]
            key = (properties["code"], properties["area_type"])
            if key in seen or key[1] not in AREA_TYPES:
                fail("INVALID_DATASET", "Use unique codes and supported administrative/electoral area types")
            if not all(isinstance(properties[k], str) and properties[k].strip() for k in ("code", "name")):
                fail("INVALID_DATASET", "Area code and name are required")
            seen.add(key)
            start, end = properties.get("effective_from"), properties.get("effective_to")
            for value in (start, end):
                if value is not None and date.fromisoformat(value).isoformat() != value:
                    fail("INVALID_DATASET", "Effective dates must use YYYY-MM-DD")
            if start and end and start > end:
                fail("INVALID_DATASET", "Effective start must not follow effective end")
            geom = shape(feature["geometry"])
        except (KeyError, TypeError, ValueError, AttributeError):
            fail("INVALID_DATASET", "Each feature needs valid properties, dates and geometry")
        if geom.geom_type == "Polygon":
            geom = MultiPolygon([geom])
        if geom.geom_type != "MultiPolygon" or not geom.is_valid or geom.is_empty:
            fail("INVALID_GEOMETRY", "Boundaries must be valid, nonempty polygons")
        if not (-180 <= geom.bounds[0] <= geom.bounds[2] <= 180
                and -90 <= geom.bounds[1] <= geom.bounds[3] <= 90):
            fail("INVALID_CRS", "Use EPSG:4326 coordinates")
        validated.append((properties, geom))
    checksum = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
    old = db.scalar(
        select(Dataset).where(Dataset.name == metadata["name"], Dataset.version == metadata["version"])
    )
    if old:
        if old.checksum != checksum or any(getattr(old, key) != metadata[key] for key in required):
            fail("DATASET_VERSION_CONFLICT", "Use a new version for changed geometry or provenance", 409)
        return old
    dataset = Dataset(**{key: metadata[key] for key in required}, checksum=checksum)
    db.add(dataset)
    db.flush()
    for p, geom in validated:
        db.add(
            Area(
                dataset_id=dataset.id,
                code=p["code"],
                name=p["name"],
                area_type=p["area_type"],
                boundary=from_shape(geom, srid=4326),
                effective_from=p.get("effective_from"),
                effective_to=p.get("effective_to"),
            )
        )
    db.flush()
    return dataset
