# CivicQuest Geospatial & Accountability Design

## 1. Core differentiator

CivicQuest connects:

**problem → location → administrative area → responsible owner → public attention → resolution**

## 2. Spatial data layers

Store versioned polygons for:
- Mumbai city boundary
- BMC zones
- BMC wards
- assembly constituencies
- parliamentary constituencies where needed
- localities/neighborhoods where useful

Do not hardcode ward names in application code.

## 3. Point-in-polygon flow

On report finalize:
1. validate coordinates,
2. resolve city,
3. resolve ward,
4. resolve constituency where applicable,
5. apply category ownership rules.

```text
lat/lng
  ↓
ward polygon
  ↓
category rule
  ↓
responsible authority/department
  ↓
representative lookup
```

## 4. Responsibility rule engine

Use data/config-driven rules.

| Category | Area type | Authority type | Department |
|---|---|---|---|
| garbage | ward | municipality | solid waste |
| pothole | ward/road-owner | municipality | roads |
| water leak | service area | utility | water |
| railway seat misuse | railway context | railway | railway enforcement |

Interface:

```python
resolve_accountability(category_id, point, context)
```

Result should include:
- administrative area,
- authority,
- department,
- representatives,
- source metadata.

The UI does not need a technical confidence percentage.

## 5. Data provenance

Every mapping should track:
- source name,
- source URL,
- imported date,
- effective date,
- version,
- manual override history.

## 6. Nearby search

Use PostGIS `ST_DWithin` for:
- reports within radius,
- Civic Actions within distance,
- hotspots near the user.

## 7. Hotspot creation

Candidate reports:
- public/open,
- same category family,
- within configured radius,
- recent time window,
- not duplicate children.

Starter score:

```text
score =
  recency_weight
  * severity_weight
  * log(1 + upvotes)
  * log(1 + unique_reporters)
  * unresolved_age_factor
```

Keep weights configurable.

## 8. Duplicate detection

Candidate query:
- 30–75 m radius,
- same category family,
- 24–72 h window.

Then add:
- pHash similarity,
- embedding similarity later,
- user confirmation.

Do not auto-delete a report solely because it looks duplicated.

## 9. Civic Action geofencing

Check-in requires:
- active event window,
- participant joined,
- acceptable GPS accuracy,
- location inside geofence,
- anti-replay token.

## 10. Public map privacy

Do not expose:
- reporter home location,
- location history,
- private check-in coordinates,
- image EXIF.

Sensitive categories may need coordinate rounding/snapping.

## 11. Map API

Request by viewport/bounds.

```text
GET /explore?bbox=minLng,minLat,maxLng,maxLat&zoom=...
```

At low zoom: hotspots/clusters.  
At high zoom: individual public reports.

## 12. Future extensions

- ward cleanliness score,
- area resolution SLA,
- heatmaps,
- recurrence patterns,
- time-of-day patterns,
- road-segment ownership,
- Open311 compatibility,
- multi-city boundary packages.
