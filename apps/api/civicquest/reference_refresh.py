"""Failure-safe refreshes for reviewed public reference sources."""

import csv
import io
from datetime import timedelta, timezone

import httpx
from sqlalchemy import select

from .common import fail
from .db import now
from .models import Area, Officer, Representative
from .reference_data import import_bmc_ward_offices, import_postal_places, import_representatives

POSTAL_CSV = "https://www.data.gov.in/sites/default/files/datafile/pincode.csv"
POSTAL_SOURCE = "https://www.data.gov.in/resource/all-india-pincode-directory-till-last-month"
BMC_APP = "https://mcgm.maps.arcgis.com/apps/webappviewer/index.html?id=42d036c489924352b760f560ac250a2d"
BMC_OFFICES = (
    "https://services8.arcgis.com/r6MmJtuWAzMawmJ8/arcgis/rest/services/"
    "BMConMaps_Nov26gdb/FeatureServer/23/query"
)
BMC_WARDS = BMC_OFFICES.replace("FeatureServer/23/query", "FeatureServer/24/query")
SANSAD_API = "https://sansad.in/api_ls/member"
SANSAD_SOURCE = "Digital Sansad current-member API"


def normalized(value):
    return " ".join(str(value or "").casefold().split())


def refresh_reference_data(db, client=None):
    """Refresh three sources in one transaction; any bad snapshot rolls everything back."""
    fetched = now().astimezone(timezone.utc)
    owns_client = client is None
    client = client or httpx.Client(timeout=45, follow_redirects=True)
    try:
        postal_response = client.get(POSTAL_CSV)
        postal_response.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(postal_response.content.decode("latin1"))))
        mumbai_rows = [row for row in rows if row.get("District", "").strip().upper()
                       in {"MUMBAI", "MUMBAI SUBURBAN"}]
        if len(mumbai_rows) < 200:
            fail("POSTAL_REFRESH_INCOMPLETE", "Department of Posts snapshot has too few Mumbai rows", 502)
        postal = import_postal_places(db, rows, {
            "source_url": POSTAL_SOURCE,
            "version": postal_response.headers.get("last-modified", fetched.date().isoformat()),
            "fetched_at": fetched.isoformat(),
        })
        if len(postal) < 150:
            fail("POSTAL_REFRESH_INCOMPLETE", "Too few postal points fell inside Greater Mumbai", 502)

        ward_response = client.get(BMC_WARDS, params={"where": "1=1", "outFields": "*",
                                                       "outSR": "4326", "f": "geojson"})
        ward_response.raise_for_status()
        ward_features = ward_response.json().get("features", [])
        if len(ward_features) != 24:
            fail("BMC_WARD_REFRESH_INCOMPLETE", "BMC ward snapshot must contain 24 polygons", 502)

        bmc_response = client.get(BMC_OFFICES, params={"where": "1=1", "outFields": "*",
                                                       "outSR": "4326", "f": "geojson"})
        bmc_response.raise_for_status()
        bmc_document = bmc_response.json()
        ward_codes = {feature.get("properties", {}).get("WARD_NAME", "").strip()
                      for feature in bmc_document.get("features", [])}
        if len(ward_codes) != 24:
            fail("BMC_REFRESH_INCOMPLETE", "BMC office snapshot must contain all 24 wards", 502)
        offices = import_bmc_ward_offices(db, bmc_document, {
            "source_url": BMC_APP, "verified_at": fetched.isoformat(),
        })
        if len(offices) < 40:
            fail("BMC_REFRESH_INCOMPLETE", "BMC office snapshot has too few valid contacts", 502)
        office_ids = {item.id for item in offices}
        for old in db.scalars(select(Officer).where(Officer.source_url == BMC_APP,
                                                     Officer.effective_to.is_(None))):
            if old.id not in office_ids:
                old.effective_to = fetched

        sansad_response = client.get(SANSAD_API)
        sansad_response.raise_for_status()
        members = sansad_response.json().get("membersDtoList", [])
        sitting = [item for item in members if item.get("status") == "Sitting"
                   and item.get("stateName") == "Maharashtra"
                   and normalized(item.get("constName")).startswith("mumbai ")]
        if len(sitting) != 6:
            fail("SANSAD_REFRESH_INCOMPLETE", "Digital Sansad must return six sitting Mumbai MPs", 502)
        areas = {normalized(area.name): area for area in db.scalars(select(Area).where(
            Area.area_type == "parliamentary_constituency", Area.active.is_(True)))}
        snapshot = {"type": "CivicQuestRepresentativeSnapshot", "fetched_at": fetched.isoformat(),
                    "items": []}
        for member in sitting:
            area = areas.get(normalized(member.get("constName")))
            if not area:
                fail("REPRESENTATIVE_AREA_MISSING",
                     f"No parliamentary boundary matches {member.get('constName')}", 409)
            source_id = str(member["mpsno"])
            existing = db.scalar(select(Representative).where(
                Representative.source_name == SANSAD_SOURCE, Representative.source_id == source_id))
            snapshot["items"].append({
                "area_code": area.code, "area_type": area.area_type, "role": "MP",
                "name": member["mpFirstLastName"], "party": member["partyFname"],
                "photo_url": member.get("imageUrl") or None, "source_name": SANSAD_SOURCE,
                "source_id": source_id, "source_url": "https://sansad.in/ls/members",
                "effective_from": existing.effective_from if existing else fetched.date().isoformat(),
                "reviewed": True,
            })
        representatives = import_representatives(db, snapshot)
        current_ids = {item.source_id for item in representatives}
        expired_on = (fetched.date() - timedelta(days=1)).isoformat()
        for old in db.scalars(select(Representative).where(
                Representative.source_name == SANSAD_SOURCE, Representative.role == "MP",
                Representative.effective_to.is_(None))):
            if old.source_id not in current_ids:
                old.effective_to = expired_on
        db.flush()
        return {"postal_places": len(postal), "bmc_wards_checked": len(ward_features),
                "bmc_contacts": len(offices),
                "sitting_mumbai_mps": len(representatives), "fetched_at": fetched.isoformat()}
    finally:
        if owns_client:
            client.close()
