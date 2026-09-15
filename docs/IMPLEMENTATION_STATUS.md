# CivicQuest V1 task ledger — 13 September 2026

## Three-phase mobile plan continuation

The application is running at **http://localhost:3000** through the native PostGIS/API/worker/web runtime. The mobile mockup plan is now the active delivery ledger. The previous CQ-00–CQ-14 inventory below remains useful for infrastructure traceability.

### Completed in the current mobile implementation pass

- Phase 1 data contracts: human report codes and `/i/{publicCode}` lookup, low/medium/high severity, append-only milestones, and the versioned 15/25/50 verified Place reward.
- Phase 1 mobile shell: session splash, first-run onboarding, centered phone frame, five-item bottom navigation, restrained game styling, SVG controls, and Sprout limited to brand entry screens.
- Phase 1 citizen loop: Nammakasa-inspired civic map/list, factual counters, ward/report sheets, Place capture, guided severity, GPS/manual coordinates, durable same-page upload retry, pending XP, redesigned feed, and adaptive report detail.
- Phase 2 trust contracts: Seen confirmations, account deduplication, comments, community updates, follows, ten-person escalation creation, complaint handoff/status records, and notification events.
- Phase 2 directory and Catch foundations: reviewed officers and Community Groups; live Catch sessions, precise location/server time, photo/video processing, profile-only Catch projection, caption checks, removal, and zero rewards.
- Phase 2 reviewer UI: mobile escalation queue, explicit approve/decline, manual external handoff, official-ID recording, sourced status updates, and report/resolution/appeal queues.
- Phase 3 progress presentation: combined Quest Log/Actions/My Reports/Groups hub, twelve versioned badge rules, mobile Civic Card/profile, optional simple portraits, and public Catch wall.
- Civic Action administration includes mobile create/edit/cancel controls. Citizen before/after inputs request live camera capture on supported phones.
- Native startup skips unchanged synchronized files by safe size/time checks while keeping atomic full-file replacement for changed inputs.

### Current verification

- **36 backend tests pass** on the isolated migrated PostgreSQL/PostGIS database.
- **20 Chromium browser checks pass**: all 10 current journeys on Pixel 7 emulation and all 10 in desktop Chrome. They cover map geography/state, Place capture and pending XP, shell navigation, accessibility, portraits, reviewer access, notification preferences, and ward-goal administration.
- Python Ruff and compilation pass. Current web routes compile and return HTTP 200 from the running Next.js development server.
- The full earlier browser suite has not yet been rerun after every mobile screen change; only the focused current checks are claimed here.

### Remaining release work

- Complete and exercise the report → ten Seen → reviewer handoff → official update → verified resolution → appeal/restoration browser journey.
- Populate category-specific operational ownership only from reviewed asset-appropriate BMC sources; the audited admin/effective-date mechanism is complete. Comment abuse/removal UI and scheduled reminders remain. Community Group edit/deactivation and provenance review-due states are complete.
- Complete Catch video safety integration and native FFmpeg setup, retry acceptance, author removal UI, moderator Catch review UI, and physical Android/iPhone checks.
- Finish end-to-end browser share/download and revocation acceptance. Help Fix My Ward, Personal Civic Card, resolved-fix and safe-derivative before/after entries are implemented; resolved report restriction is checked again at delivery.
- Finish ward leaderboard selectors/snapshots, remaining badge/quest rebuild acceptance, participant-history UI, and full Action proof browser coverage.
- Run WebKit, full accessibility/security/write-load/recovery suites, frozen clean-checkout and Docker Compose acceptance, image scans, retention schedules, and handoff guides.
- Credential-dependent Google, MapTiler, Bedrock, push, AWS IAM/CDN/RDS and approved live civic dataset checks remain launch prerequisites.
- Google sign-in is now always visible with linked-provider status and exact callback guidance. Live OAuth remains disabled until operator credentials are supplied.
- The running local map now uses 67 active non-synthetic reference polygons: Greater Mumbai, 24 official BMC administrative wards, 36 Assembly constituencies and six Parliamentary constituencies. Forty-two dated MLA/MP records are bound to constituency geometry. BMC redistribution approval remains launch work.
- Search now includes 230 in-coverage Department of Posts points across 89 Mumbai City/Suburban pincodes. Multiple offices are shown separately and resolve through PostGIS. The transactional monthly refresh configuration is complete and awaits enablement in a reviewed deployment.
- The machine currently has about **3 GB free**. At least 8 GB free remains required for the Docker/PostGIS/browser release gate.

V1 is **partially implemented, not release-complete**. “Implemented” below means code exists; verification is listed separately. No entire CQ chunk should be closed until its complete acceptance gate passes. The approved plan remains the delivery scope.

Latest continuation: the two new UX references are reconciled into UX-01–UX-12 in [remaining work](REMAINING_WORK.md). Spatial constituency counts, current/reviewed representative context, map/filter restoration, resolved/mixed map styling, filter-aware totals, area age/rate metrics and admin-managed shared ward goals are now implemented. **28 backend tests pass**; the broader browser run passed 16 cases and the corrected focused ward-goal rerun passed both desktop/mobile cases. See [current evidence](validation/2026-09-12-geography-goals.md). Full V1 acceptance remains open.

## Verified baseline from 11 September

- 18 backend tests passed on real PostgreSQL/PostGIS.
- 8 browser tests passed: desktop Chrome and Pixel 7 emulation for navigation, capture accessibility, photo submission/pending XP, and moderator workspace access.
- Production web build, TypeScript, backend lint, OpenAPI export/client declarations, and Terraform static validation passed.
- Native database/media backup, isolated restore, and progress/hotspot rebuild passed.
- 100,008 synthetic reports / 50 concurrent read clients: feed p95 662 ms, map p95 924 ms, zero HTTP failures. This is a short read baseline, not production or write-load certification.

## Complete chunk-by-chunk inventory

| Chunk | Implemented / done so far | Pending before the chunk is complete |
|---|---|---|
| CQ-00 Specifications | Approved decisions recorded; 15 OpenSpec changes and task files; old/new scope precedence documented; original license preserved | Expand precise acceptance scenarios and synchronize task completion with evidence; final feature-to-contract audit |
| CQ-01 Foundation | Web/API/worker workspaces, dependency locks, environment example, Compose files, Dockerfiles, migrations/seed commands, CI jobs | Clean-checkout frozen dependency installation; full Docker/Compose startup and image builds; durable developer setup |
| CQ-02 Database/reliability | Frozen initial DDL, public-query index migration, transactional outbox, receipts, retry/dead state, audit/XP immutability; rollback/replay tests | Real ElasticMQ/SQS persistence/restart tests; broader concurrent delivery and operational telemetry |
| CQ-03 Identity/access | Guest sessions, cookies/CSRF, role gates, local identities, Google OIDC adapter, account merge, session revocation, account deletion; core security/merge tests | Live Google linking; concurrent linking/merge cases and entitlement audit; full deletion/retention coverage |
| CQ-04 Web shell | Light responsive design, five navigation areas, reusable controls, loading/error/empty states; desktop/mobile navigation and capture accessibility passed | Accessibility across all screens, keyboard dialogs, responsive edge cases and remaining visual polish |
| CQ-05 Geography/ownership | Greater Mumbai plus 24 BMC wards, 36 Assembly and six Parliamentary boundaries; 89-pincode point search; dated MLA/MP and ward contacts; provenance, ambiguity handling, MapLibre/MapTiler/OSM adapters, ownership admin/effective dates | BMC redistribution approval; reviewed asset-specific ownership rules; richer manual map picker and remaining map restoration coverage |
| CQ-06 Media | Local/S3 adapters, scoped upload authorization, photo decoding/conversion, EXIF stripping, private originals, safe derivatives, safety adapter, duplicate candidates, redaction API/UI | Moto storage tests; original-access/upload-reuse security coverage; multi-photo/expiry/resume cases; graphical redaction and mobile format testing |
| CQ-07 Reporting | Guest draft/upload/finalize, pending XP, processing, history, report detail; browser submission and fail-closed processing tests | Capture suggestion/ownership preview, durable retry across reload/expiry, full review/verification browser flow; same-page retry improvements added today |
| CQ-08 Feeds/attention | Separate feeds, cursor API, vote/unvote/self-vote rules, detail/timeline, deterministic hotspots, bulk response loading; read baseline passed | Pagination controls, meaningful trending, map clusters/action-hotspot filtering, complete hotspot/duplicate/account-merge concurrency coverage |
| CQ-09 Trust/resolution | Community verification, moderation, abuse, appeals/restoration, resolution proof/review/dispute, redaction, duplicate merge, reward reversals | Complete browser verification→resolution and restriction→appeal journeys; nuanced transition/security tests and redaction usability |
| CQ-10 Progress | XP ledger/caps/reversals, levels, CivicDex, badges, quests and quest invalidation, streaks, profile/leaderboard endpoints, rebuild | Ward selector and leaderboard snapshots; public profile routing; full quest/account-merge replay audit; align all public stats with visibility |
| CQ-11 Civic Actions | Admin creation/edit API, listing/join/capacity, geofence/single-use challenge, manual check-in, before/after proof, approval and 120-XP reversal; domain tests | Full citizen/admin browser proof journey; event edit/cancel UI, participant history, concurrency/late-proof cases |
| CQ-12 Sharing/notifications/PWA | Generic share-card jobs/images, inbox, push adapter/subscriptions, manifest, service worker/offline shell | Distinct monthly/cleanup cards; full share/download support, notification preferences/reminders, push delivery, install/icon/WebKit checks |
| CQ-13 Deployment/operations | Terraform for ECS/RDS/Redis/S3/SQS/ALB/CloudFront/IAM/logs/queue alarm; static validation; backup/restore/rebuild, job retry/status, report-original retention, runbook | Deployment workflows/scans, broader dashboards/alarms, secret bootstrap, scheduled maintenance, Action/resolution retention; live AWS plan/IAM/CDN/restore validation |
| CQ-14 Acceptance/handoff | Backend/browser suites, native recovery drill, short load baseline, validation records and remaining-work list | All remaining V1 journeys; full container suite, authenticated write-load/security tests, WebKit and actual phones; final contributor/admin guides and release checklist |

## Current environment

Latest startup update, 12 September: the application is running at **http://localhost:3000** with API on 8001, a dedicated native PostgreSQL 16/PostGIS database on 55434, and the database-outbox worker. The earlier temporary runtime/database was unavailable after session interruption; a fresh synthetic database and dependencies now live outside cloud-synced Desktop in `~/Library/Caches/CivicQuest`. Restart with `python3 scripts/dev/start-native.py`; see [native runtime instructions](LOCAL_NATIVE.md). This does not close the Docker/Compose acceptance gate.

Current checks: **43 backend tests passed** on a separate migrated real PostGIS test database. All **26 current Playwright cases** have passing evidence across desktop Chrome and Pixel 7 emulation, including portrait and Google-account presentation, sourced Mumbai geography and pincode lookup, ward goals, capture, and moderator/admin ownership and Community Group workspace access. Web TypeScript, Ruff and Python compilation pass. The live reference refresh validated 230 postal points, 24 BMC wards, 47 contacts and six sitting MPs. The native restart command was exercised without duplicating running services. Fresh web dependencies were installed with npm rather than the frozen pnpm lockfile; full release-build and container acceptance remain open.

Visual review identified and corrected initial map over-zoom and missing spacing on grouped report rows. Ward-page browser navigation works with synthetic counts and provenance. Map/area completion, live map tiles and the broader additions below remain open.

Follow-up checks confirmed visible numbered clusters on desktop and mobile, mobile list navigation into the ward page and no horizontal page overflow. A repeated browser run exposed a test navigation race: moderator login reloads Profile while the test tried to navigate to Admin. The test now waits for the login reload before opening Admin; this was a test synchronization correction. All other nine cases passed in that repeat. Services remain running at handoff.

Earlier on 12 September, Git was readable again and disk free space was approximately **6.7 GB** (previously below 1 GB). Full container validation has not yet been rerun; the earlier container attempt failed for lack of disk. The native Python environment now installs from the frozen uv lock. No production resources were created.

## Work resumed today

- Added stable draft/finalize idempotency keys during same-page capture retries.
- Added upload-attempt state so a failed completion response retries the same media instead of uploading another copy.
- Added a focused upload-recovery unit test. Equivalent recovery assertions passed directly under Node (one authorization, one photo PUT, retried completion, no extra requests after completion). Vitest and TypeScript invocations stalled without output, including outside the sandbox; stop was requested and full frontend verification remains pending for this change. This does not change the previous 18-backend/8-browser baseline.

## New requirements implementation — 12 September

Reviewed Nammakasa in a rendered desktop/mobile browser and Pokémon GO's App Store/official journey documentation. Confirmed with the user: civic-only map with no game elements; ward/constituency pages and factual representative context; individual plus shared ward cleanup goals; optional simple character portraits outside the map.

Implemented the first additions: six original portrait assets, an optional Profile picker with initials fallback, guest/account persistence, merge precedence, deletion cleanup, an allowlisted CSRF-protected API and migration 0003. The Explore map now uses ward shading, numbered zoom clusters, category/status filters and a ward-grouped list; it contains no character or quest overlay. The upload-completion retry regression now passes under Vitest.

Validation on an isolated migrated PostGIS database: migration 0003 applied, seed completed, backend suite **21 passed** after the area projection addition, API save/reload returned the portrait with zero XP, Ruff passed, web TypeScript passed before the area-page slice, and Vitest passed. Browser validation was attempted but the first Next.js page compilation stalled on cloud-backed filesystem reads and timed out before navigation; it remains pending and is not counted as a product failure.

The next geography slice adds `/api/v1/areas/{id}` and a corresponding web route with factual public counts, category breakdown, recent reports, provenance and separate constituency/representative panels. Restricted reports are excluded from both totals and recent rows. Its focused and full-suite real-PostGIS checks pass; final web type/browser checks remain open after this slice.

Added pending packages M1–M4, G1–G3 and A1 with dependencies and acceptance criteria in [map and gameplay additions](V1_MAP_AND_GAMEPLAY_ADDITIONS.md). These expand CQ-00/02/03/04/05/07/08/09/10/11/12/14; the inventory above describes the implementation before these additions.

Revised sequence after clarification: verify capture retry changes → finalize new contracts/design → area data and civic map/detail journeys → character/mission presentation → shared ward goals → complete trust/Action browser journeys → remaining container/security/recovery checks → release acceptance. Credential-dependent checks remain separate.

Detailed evidence: [local validation](validation/2026-09-11-local.md). Additional edge cases: [remaining work](REMAINING_WORK.md).
