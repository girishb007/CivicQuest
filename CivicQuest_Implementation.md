# CivicQuest Implementation Plan

Implementation should follow the Mumbai pilot and keep the first release narrow, observable, and reversible. The recommended architecture is a mobile client, API backend, PostgreSQL with PostGIS, object storage, Redis for derived rankings, and background workers for moderation, hotspot scoring, and notifications.

## Repository Structure

```text
civicquest/
  apps/
    mobile/                  # React Native / Expo client
    api/                     # FastAPI or Node/TypeScript service
    web-admin/               # moderation and authority operations later
  packages/
    shared/                  # types, validation, API contracts
    civic-taxonomy/          # categories, XP rules, status enums
    geo/                     # boundaries, distance, hotspot helpers
  infrastructure/
    database/
    storage/
    deployment/
  docs/
  tests/
  openspec/
```

## Service Boundaries

1. **Identity service:** guest sessions, account claiming, profiles, and access control.
2. **Report service:** report creation, media references, statuses, categories, and report detail.
3. **Attention service:** upvotes, feed ordering, verification signals, and hotspot inputs.
4. **Geospatial service:** coordinate validation, ward lookup, nearby search, and authority mapping.
5. **Trust service:** moderation queues, duplicate detection, rate limits, credibility, disputes, and appeals.
6. **Impact service:** resolutions, Civic Actions, check-ins, before/after proof, and organizer verification.
7. **Progress service:** XP events, levels, badges, CivicDex, quests, and leaderboard snapshots.

These boundaries may begin as modules in one API deployment. They should be separated by domain contracts before being separated into network services.

## Delivery Sequence

### Phase 0 - Product and Safety Foundation

- Confirm supported Mumbai wards and the first Places categories.
- Define Civic Catch privacy, moderation, appeals, and evidence-retention rules.
- Define report, verification, resolution, and XP state transitions.
- Create seed data for categories, XP rules, supported authorities, and boundaries.
- Add API contract tests and a decision log for unresolved product choices.

### Phase 1 - Guest Map and Capture

- Build the mobile shell with Explore, Feed, Capture, Quests, and Profile tabs.
- Add guest session creation and location permission handling.
- Display seeded Mumbai Places pins and supported Civic Catch pins.
- Implement camera capture, category suggestion placeholder, location attachment, report type selection, and submission.
- Return a report identifier and provisional XP result after successful submission.

### Phase 2 - Feeds, Votes, and Profiles

- Add separate Places and Civic Catches feeds.
- Add report detail, upvote-only interaction, and nearby filtering.
- Add profile XP, level progress, report counts, CivicDex, and basic badges.
- Add guest progress claim through Google, Apple, or phone authentication.
- Enforce vote uniqueness, rate limits, duplicate detection, and XP idempotency.

### Phase 3 - Hotspots and Accountability

- Load supported administrative boundaries and ownership mappings.
- Implement nearby report clustering and a versioned hotspot score.
- Show active report count, attention count, issue mix, status, ward, and authority.
- Add report status timeline and authority/representative references.
- Make hotspot scores and ownership mappings rebuildable and source-audited.

### Phase 4 - Civic Actions and Verified Impact

- Add NGO organizer and Civic Action publishing workflow.
- Implement event listing, join, geofenced check-in, and participation history.
- Add before/after media upload and organizer verification.
- Award higher XP only after participation and impact verification.
- Add cleanup impact card data for later social sharing.

### Phase 5 - Trust, Operations, and Growth

- Build moderation queues, abuse reporting, disputes, and appeals.
- Add authority update and resolution-proof workflows.
- Add notifications, daily quests, leaderboard snapshots, and shareable cards.
- Measure activation, report quality, resolution rate, retention, and real-world impact before expanding categories or cities.

## API Surface for the Pilot

```text
POST /v1/guest-sessions
POST /v1/auth/claim-guest-progress

GET  /v1/map/issues
POST /v1/reports
GET  /v1/reports/{report_id}
POST /v1/reports/{report_id}/upvote
POST /v1/reports/{report_id}/verify
GET  /v1/feeds/places
GET  /v1/feeds/civic-catches

GET  /v1/hotspots
GET  /v1/hotspots/{hotspot_id}
GET  /v1/wards/{ward_id}
GET  /v1/authorities/{authority_id}

GET  /v1/actions
POST /v1/actions/{action_id}/join
POST /v1/actions/{action_id}/check-in
POST /v1/actions/{action_id}/impact

GET  /v1/users/{user_id}/profile
GET  /v1/users/{user_id}/xp-events
GET  /v1/leaderboards
GET  /v1/civicdex
GET  /v1/quests
```

## Operational Requirements

- Use PostgreSQL transactions for report creation, vote uniqueness, and XP event creation.
- Use PostGIS indexes for nearby reports, boundary lookup, and hotspot queries.
- Store media outside the database with signed URLs and malware/content checks.
- Process classification, duplicate checks, notifications, and score recomputation asynchronously through a durable job queue.
- Keep an append-only audit trail for moderation, authority updates, XP reversals, and resolution verification.
- Add structured logs, metrics, tracing, error reporting, and a data-retention job before public pilot access.
- Protect sensitive evidence with least-privilege access, encryption, and explicit deletion workflows.

## Definition of Pilot Readiness

The Mumbai pilot is ready for limited testing when a guest can explore the map, submit a supported report, see it in the correct feed, receive idempotent XP, and understand its status and ownership. A claimed user must be able to see the same progress later, upvote without duplicate votes, and join a Civic Action.

Before public launch, the team must also demonstrate that abusive or disputed individual reports can be hidden, appealed, and removed; that authority mappings have a named data source; and that XP, hotspot, and leaderboard values can be recomputed from auditable source events.
