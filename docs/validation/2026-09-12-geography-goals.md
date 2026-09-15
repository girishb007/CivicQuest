# Geography, shared goals and UX references — 12 September 2026

The two root UX reference documents were read and reconciled into UX-01–UX-12 in `docs/REMAINING_WORK.md`. Reference ideas do not override the confirmed V1 identity, XP, public-visibility or geographic rules.

## Implemented

- Migrations 0004 (representative review) and 0005 (ward goals), applied to the dedicated local PostGIS database and isolated test database.
- Spatial ward/constituency report counts; effective/active boundary filtering; reviewed current representative terms; immutable import provenance and full-document validation before inserts.
- Synthetic electoral polygons and clearly fictional representative fixtures, plus an additive demo ward goal.
- Explore category-family/status server filtering, accurate totals before the 200-report display limit, explicit truncation messaging, preserved map/list/filter/viewport state.
- Resolved green and mixed ochre clusters with textual status labels; resolution-rate and average-unresolved-age metrics with explicit definitions and no-data dashes.
- Admin goal create/edit/publish/cancel; guest-readable goals on Quests and ward pages; unique outcome projection, no new XP, immediate exclusion of restricted/duplicate reports and cancelled events.
- Resolution approval replay preserves its original acceptance timestamp.
- Atomic native source synchronization fixes stale-size/truncated copies from cloud-backed Desktop files.

## Evidence

- **28 backend tests passed** on the isolated PostgreSQL 16/PostGIS test database. This includes five new geography tests and two ward-goal tests.
- TypeScript validation passed after the map/metrics/goals changes.
- Ruff passed on backend code, tests and the native launcher.
- Full browser run: **16 passed**, with two ward-goal failures subsequently investigated. The form's accessible select labels were made explicit; an in-progress development refresh also reset the admin tab during the initial run. The focused ward-goal suite then passed **2/2**, covering desktop Chrome and Pixel 7 emulation.
- Six geography browser cases cover ward→constituency counts, area accessibility, no mobile overflow, filter restoration, cluster zoom restoration and resolved/mixed marker semantics. Marker semantics use an explicitly isolated browser response fixture; this is not evidence of the complete resolution/moderation journey.
- Existing navigation, portrait persistence/accessibility, capture submission/pending XP and moderator workspace tests passed in the broader browser run.
- API OpenAPI export and TypeScript client declarations regenerated successfully with openapi-typescript 7.9.1; ward-goal contracts are present.

## Still open

Full approval→resolution/Action→personal/shared progress browser journeys, contextual sheets, scalable zoom queries, severity/subtypes, authority contact data/UI, representative analytics, mature mission styling and the other UX checklist items remain open. These checks do not validate Docker/SQS, live Google/MapTiler/AI/push, AWS deployment, WebKit or physical phones. Geography and people remain synthetic.

The local runtime remains at `http://localhost:3000`; see `docs/LOCAL_NATIVE.md` for restart and storage details.
