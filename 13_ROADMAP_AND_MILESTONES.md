# CivicQuest Engineering Roadmap & Milestones

## Milestone 0 — Decision freeze

Deliverables:
- Phase 1 scope approved,
- launch categories approved,
- Mumbai pilot geography selected,
- moderation policy draft,
- face/public-media policy decision path,
- XP rules v0,
- accountability sources identified.

## Milestone 1 — Repository & foundation

Build:
- monorepo,
- Next.js web,
- FastAPI API,
- Postgres/PostGIS,
- Redis,
- storage path,
- CI,
- Terraform skeleton,
- Docker Compose.

Exit: web + API + DB deploy to dev.

## Milestone 2 — Guest identity + Explore

Build:
- guest session,
- location permission,
- map,
- viewport API,
- ward polygon import,
- nearby fixtures.

Exit: guest can explore Mumbai.

## Milestone 3 — Reporting

Build:
- report draft,
- camera/upload,
- presigned media,
- category selection,
- geolocation,
- finalize,
- async processing,
- public derivative pipeline.

Exit: Place report works end-to-end.

## Milestone 4 — Geospatial accountability

Build:
- point-in-polygon,
- responsibility rules,
- ward/department display,
- source provenance.

Exit: supported category resolves correct owner in pilot area.

## Milestone 5 — Feed + upvotes + hotspots

Build:
- Places feed,
- Civic Catch feed behind flag,
- upvotes,
- trending,
- hotspot grouping.

Exit: attention affects visibility.

## Milestone 6 — Gamification

Build:
- XP ledger,
- levels,
- CivicDex,
- basic quests,
- leaderboard.

Exit: verified contribution becomes visible progress.

## Milestone 7 — Civic Actions

Build:
- event listing,
- join,
- geofence check-in,
- before/after proof,
- verification,
- high-value XP.

## Milestone 8 — Moderation / admin

Build:
- moderation queue,
- report abuse,
- visibility controls,
- audit log,
- duplicate merge,
- Civic Catch review.

## Milestone 9 — Account conversion + sharing

Build:
- Google account link,
- public profile,
- share card,
- Web Share API.

## Milestone 10 — Pilot hardening

- load test,
- security review,
- accessibility,
- analytics,
- monitoring,
- backup/restore,
- moderator runbook.

## Pilot stop conditions

Pause or narrow the rollout if:
- false reports spike,
- moderation SLA becomes unsustainable,
- dangerous behavior emerges,
- accountability mapping is materially wrong,
- privacy incidents occur.
