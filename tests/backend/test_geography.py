"""Real PostGIS checks for electoral crossings and time-bounded public context."""
import copy

import pytest
from civicquest import geo
from civicquest.models import Area, Category, Dataset, Officer, Report, Representative, User
from fastapi import HTTPException
from sqlalchemy import func, select, update
from test_journeys import clients  # noqa: F401


def feature(code, kind, left, right, **properties):
    return {"type": "Feature", "properties": {"code": code, "name": code,
            "area_type": kind, **properties}, "geometry": {"type": "Polygon",
            "coordinates": [[[left, 19.0], [right, 19.0], [right, 19.2],
                             [left, 19.2], [left, 19.0]]]}}


def import_areas(db, features, name="geography-test", version="1"):
    return geo.import_geojson(db, {"type": "FeatureCollection", "features": features},
                             {"name": name, "version": version, "source_url": "https://example.invalid",
                              "license": "CC0", "reviewed": False, "synthetic": True})


@pytest.fixture
def geography(db):
    db.execute(update(Area).values(active=False))
    db.execute(update(Report).values(visibility="private"))
    dataset = import_areas(db, [feature("city", "city", 72.8, 73.0),
                               feature("west-ward", "ward", 72.8, 72.9),
                               feature("east-ward", "ward", 72.9, 73.0),
                               feature("crossing-seat", "assembly_constituency", 72.85, 72.95),
                               feature("touch-only", "parliamentary_constituency", 72.95, 73.0)])
    return {a.code: a for a in db.scalars(select(Area).where(Area.dataset_id == dataset.id))}


def test_shared_edges_versions_and_effective_dates(db, geography):
    ward, matches = geo.coverage(db, 19.1, 72.9)
    assert ward is None
    assert len([a for a in matches if a.area_type == "ward"]) == 2
    assert geo.coverage(db, 19.1, 72.84)[0].id == geography["west-ward"].id
    import_areas(db, [feature("west-ward", "ward", 72.8, 72.9)], version="2")
    assert geo.coverage(db, 19.1, 72.84)[0] is None  # overlapping versions never silently win
    newer = db.scalar(select(Area).where(Area.code == "west-ward", Area.id != geography["west-ward"].id))
    newer.effective_from = "2999-01-01"
    db.flush()
    assert geo.coverage(db, 19.1, 72.84)[0].id == geography["west-ward"].id
    geography["west-ward"].effective_to = "2000-01-01"
    db.flush()
    assert geo.coverage(db, 19.1, 72.84)[0] is None
    with pytest.raises(HTTPException) as expired:
        geo.area_details(db, geography["west-ward"].id)
    assert expired.value.status_code == 404
    with pytest.raises(HTTPException) as outside:
        geo.coverage(db, 20, 74)
    assert outside.value.detail["code"] == "OUTSIDE_COVERAGE"


def test_constituency_counts_actual_points_and_excludes_private_content(db, geography):
    user = User()
    category = Category(code="geo_test", name="Geographic test", report_type="place", family="waste")
    db.add_all([user, category])
    db.flush()
    items = []
    for lng in [72.84, 72.86, 72.94, 72.96, 72.9]:
        report = Report(reporter_id=user.id, report_type="place", category=category.code,
                        location=geo.point(19.1, lng), status="open", visibility="public",
                        area_id=geography["west-ward"].id)  # deliberately stale ward assignment
        db.add(report)
        items.append(report)
    db.flush()
    seat = geography["crossing-seat"]
    body = geo.area_details(db, seat.id)
    assert body["statistics"]["total_reports"] == 3
    assert body["statistics"]["resolution_rate"] == 0
    assert body["statistics"]["average_open_days"] == 0
    assert {r["id"] for r in body["reports"]} == {r.id for r in items[1:3]} | {items[4].id}
    assert len(body["wards"]) == 2
    assert body["constituencies"] == []  # the parliamentary polygon only touches its edge
    assert geo.area_details(db, geography["east-ward"].id)["statistics"]["total_reports"] == 3
    items[1].visibility = "restricted"
    items[2].duplicate_of = items[0].id
    items[4].report_type = "civic_catch"
    db.flush()
    body = geo.area_details(db, seat.id)
    assert body["statistics"]["total_reports"] == 0
    assert body["statistics"]["resolution_rate"] is None
    assert body["statistics"]["average_open_days"] is None
    assert body["reports"] == []


def test_representatives_require_review_and_current_terms(db, geography):
    seat = geography["crossing-seat"]
    for name, reviewed, start, end in [("current", True, "2020-01-01", None),
                                       ("unreviewed", False, "2020-01-01", None),
                                       ("expired", True, "2000-01-01", "2001-01-01"),
                                       ("future", True, "2999-01-01", None)]:
        db.add(Representative(name=name, role="MLA", area_id=seat.id, source_url="https://example.invalid",
                              reviewed=reviewed, effective_from=start, effective_to=end))
    db.flush()
    assert [r["name"] for r in geo.area_details(db, seat.id)["representatives"]] == ["current"]
    category = Category(code="geo_owner", name="Owner test", report_type="place", family="waste")
    assert [r["name"] for r in geo.accountability(db, 19.1, 72.86, category)["representatives"]] == ["current"]
    seat.active = False
    db.flush()
    assert geo.accountability(db, 19.1, 72.86, category)["representatives"] == []


def test_representative_snapshot_requires_existing_area_and_is_idempotent(db, geography):
    from civicquest.reference_data import import_representatives

    snapshot = {"type": "CivicQuestRepresentativeSnapshot", "fetched_at": "2026-09-13T12:00:00Z",
                "items": [{"area_code": "crossing-seat", "area_type": "assembly_constituency",
                           "role": "MLA", "name": "Reviewed Person", "party": "Example Party",
                           "source_name": "Official result", "source_id": "seat-1",
                           "source_url": "https://example.invalid/official", "effective_from": "2024-11-24",
                           "reviewed": True}]}
    first = import_representatives(db, snapshot)[0]
    second = import_representatives(db, snapshot)[0]
    assert second.id == first.id
    assert second.party == "Example Party"
    assert second.fetched_at.isoformat() == "2026-09-13T12:00:00+00:00"
    snapshot["items"][0]["area_code"] = "missing"
    with pytest.raises(HTTPException) as missing:
        import_representatives(db, snapshot)
    assert missing.value.detail["code"] == "REPRESENTATIVE_AREA_MISSING"


def test_postal_import_keeps_mumbai_points_inside_coverage_and_is_idempotent(db, geography):
    from civicquest.models import PostalPlace
    from civicquest.reference_data import import_postal_places

    rows = [{"District": "MUMBAI", "Pincode": "400001", "OfficeName": "Test GPO",
             "Latitude": "19.1", "Longitude": "72.84"},
            {"District": "MUMBAI", "Pincode": "400999", "OfficeName": "Outside",
             "Latitude": "20", "Longitude": "74"},
            {"District": "THANE", "Pincode": "400708", "OfficeName": "Airoli",
             "Latitude": "19.15", "Longitude": "72.99"}]
    metadata = {"source_url": "https://data.gov.in/example", "version": "test",
                "fetched_at": "2026-09-13T12:00:00Z"}
    assert len(import_postal_places(db, rows, metadata)) == 1
    assert len(import_postal_places(db, rows, metadata)) == 1
    assert db.scalar(select(func.count()).select_from(PostalPlace)) == 1
    assert db.scalar(select(PostalPlace.pincode)) == "400001"


def test_bmc_office_import_binds_reviewed_contacts_to_official_ward(db, geography):
    from civicquest.reference_data import import_bmc_ward_offices

    geography["west-ward"].code = "BMC-W"
    document = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": None,
                "properties": {"WARD_NAME": "W", "BRD_LINE_N": "022-12345678",
                               "CNTRL_ROOM": "022-"}}]}
    metadata = {"source_url": "https://mcgm.example/official", "verified_at": "2026-09-13T12:00:00Z"}
    assert len(import_bmc_ward_offices(db, document, metadata)) == 1
    assert len(import_bmc_ward_offices(db, document, metadata)) == 1
    office = db.scalar(select(Officer))
    assert office.title == "BMC Ward Office"
    assert office.phone == "022-12345678"
    assert office.reviewed is True


def test_admin_manages_dated_operational_owner_and_officer_records(db, geography, clients):  # noqa: F811
    administrator, user_id = clients(True)
    db.get(User, user_id).role = "admin"
    geography["west-ward"].code = "BMC-W"
    db.flush()
    owner = {
        "name": "Solid Waste Management Department",
        "department": "BMC Solid Waste Management",
        "area_id": geography["west-ward"].id,
        "category_family": "waste",
        "source_url": "https://example.invalid/bmc/solid-waste",
        "effective_from": "2026-01-01",
        "effective_to": None,
        "reviewed": True,
    }
    created = administrator.post("/api/v1/admin/authorities", json=owner)
    assert created.status_code == 200, created.text
    category = Category(code="owner_admin_test", name="Owner admin test", report_type="place", family="waste")
    db.add(category)
    db.flush()
    assert geo.accountability(db, 19.1, 72.84, category)["label"] == owner["name"]
    rule_id = created.json()["id"]
    owner["effective_to"] = "2026-01-02"
    assert administrator.put(f"/api/v1/admin/authorities/{rule_id}", json=owner).status_code == 200
    assert geo.accountability(db, 19.1, 72.84, category)["label"] == "Owner not confirmed"
    assert administrator.get("/api/v1/admin/authorities").json()["items"][0]["reviewed"] is True

    officer = {
        "name": "W Ward Office",
        "title": "BMC Ward Office",
        "department": "Municipal Corporation of Greater Mumbai",
        "area_id": geography["west-ward"].id,
        "category_family": None,
        "reason": "Official BMC ward contact; operational ownership varies by category.",
        "source_url": "https://example.invalid/bmc/wards",
        "verified_at": "2026-09-13T12:00:00Z",
        "effective_to": None,
        "phone": "022-12345678",
        "whatsapp": None,
        "email": None,
        "official_url": "https://example.invalid/bmc",
        "reviewed": True,
    }
    made = administrator.post("/api/v1/admin/officers", json=officer)
    assert made.status_code == 200, made.text
    officer["effective_to"] = "2026-09-14T00:00:00Z"
    changed = administrator.put(f"/api/v1/admin/officers/{made.json()['id']}", json=officer)
    assert changed.status_code == 200
    assert changed.json()["effective_to"] == "2026-09-14T00:00:00+00:00"
    assert administrator.get("/api/v1/admin/officers").json()["items"][0]["reviewed"] is True


def test_admin_updates_and_deactivates_review_due_community_group(db, clients):  # noqa: F811
    administrator, user_id = clients(True)
    db.get(User, user_id).role = "admin"
    db.flush()
    payload = {
        "name": "Reviewed test group",
        "description": "Synthetic directory record used only in the isolated test transaction.",
        "area_id": None,
        "coverage_text": "Mumbai test coverage",
        "contact_url": "https://example.invalid/contact",
        "source_url": "https://example.invalid/source",
        "source_name": "Synthetic test source",
        "verified_at": "2026-01-01T00:00:00Z",
        "reviewed": True,
        "status": "active",
        "statistics": {},
    }
    created = administrator.post("/api/v1/admin/community-groups", json=payload)
    assert created.status_code == 200, created.text
    group_id = created.json()["id"]
    public = administrator.get("/api/v1/community-groups").json()["items"]
    group = next(item for item in public if item["id"] == group_id)
    assert group["provenance"]["review_due"] is True
    payload.update(status="inactive", description="Updated reviewed test directory record.")
    changed = administrator.put(f"/api/v1/admin/community-groups/{group_id}", json=payload)
    assert changed.status_code == 200
    assert changed.json()["status"] == "inactive"
    assert all(item["id"] != group_id for item in administrator.get("/api/v1/community-groups").json()["items"])
    assert any(item["id"] == group_id for item in administrator.get(
        "/api/v1/admin/community-groups").json()["items"])


def test_reference_refresh_rejects_incomplete_postal_snapshot_before_changes(db):
    from civicquest.models import PostalPlace
    from civicquest.reference_refresh import refresh_reference_data

    class Response:
        content = b"District,Pincode,OfficeName,Latitude,Longitude\nMUMBAI,400001,Only Row,19.1,72.84\n"
        headers = {}

        def raise_for_status(self):
            return None

    class Client:
        def get(self, *args, **kwargs):
            return Response()

    before = db.scalar(select(func.count()).select_from(PostalPlace))
    with pytest.raises(HTTPException) as incomplete:
        refresh_reference_data(db, Client())
    assert incomplete.value.detail["code"] == "POSTAL_REFRESH_INCOMPLETE"
    assert db.scalar(select(func.count()).select_from(PostalPlace)) == before


def test_import_validation_is_atomic_and_provenance_is_immutable(db):
    before = db.scalar(select(func.count()).select_from(Dataset))
    valid = feature("valid", "ward", 72.8, 72.9)
    invalid = feature("bad", "ward", 72.8, 72.9, effective_from="2025-02-30")
    with pytest.raises(HTTPException):
        import_areas(db, [valid, invalid])
    assert db.scalar(select(func.count()).select_from(Dataset)) == before
    for bad in [feature("x", "unsupported", 72.8, 72.9),
                feature("x", "ward", 72.8, 72.9, effective_from="2030-01-01", effective_to="2020-01-01")]:
        with pytest.raises(HTTPException):
            import_areas(db, [bad])
    dataset = import_areas(db, [valid])
    assert import_areas(db, [valid]).id == dataset.id
    altered = copy.deepcopy(valid)
    altered["properties"]["name"] = "changed"
    with pytest.raises(HTTPException) as conflict:
        import_areas(db, [altered])
    assert conflict.value.status_code == 409


def test_explore_summary_counts_all_matches_before_page_limit(db, geography, clients):  # noqa: F811
    citizen, uid = clients()
    category = Category(code="map_summary", name="Map summary", report_type="place", family="waste")
    db.add(category)
    db.flush()
    for index in range(205):
        db.add(Report(reporter_id=uid, report_type="place", category=category.code,
                      location=geo.point(19.1,72.84), status="resolved" if index < 2 else "open",
                      visibility="public", area_id=geography["west-ward"].id))
    db.flush()
    path='/api/v1/explore?lat=19.1&lng=72.84&radius_m=1000&family=waste'
    all_reports=citizen.get(path).json()
    assert all_reports["summary"] == {"total":205,"active":203,"resolved":2,"limit":200,"truncated":True}
    assert len(all_reports["reports"]) == 200
    resolved=citizen.get(path+'&status=resolved').json()
    assert resolved["summary"]["total"] == 2
    assert len(resolved["reports"]) == 2
    assert citizen.get(path+'&status=private').status_code == 400
