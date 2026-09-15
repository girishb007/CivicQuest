# Remaining work before V1 acceptance

Do not mark CQ-00–CQ-14 collectively complete from the current intermediate validation.

## Active three-phase checklist — 13 September 2026

### Phase 1 — mobile foundation and reporting loop

- [x] Centered phone shell, splash, first-run onboarding, mobile navigation and visual tokens.
- [x] Explore map/list with factual counters, severity/status controls, clusters, ward/report sheets and Capture action.
- [x] Human report IDs, public-code routes, severity migration, milestones and 15/25/50 reward rules.
- [x] Mobile Place Capture, pending-XP confirmation, Feed and report detail.
- [ ] Complete viewport/filter/scroll restoration coverage across every map drill-down and browser back path.
- [ ] Complete upload recovery across browser reload, expired authorization and large mobile HEIC fixtures.
- [x] Replace the partial demo extent with 24 BMC administrative wards, a derived Greater Mumbai coverage polygon, 36 Assembly constituencies and six Parliamentary constituencies; retain provenance on every layer.
- [x] Add reviewed India Post Mumbai City/Suburban post-office points for 89 pincodes; multiple offices remain selectable and each point resolves spatially instead of assigning a ward/representative by postal-code join.
- [x] Show the selected postal office's spatially resolved ward/Assembly/Parliamentary context and explicit shared-boundary ambiguity copy.
- [x] Add a failure-safe monthly India Post refresh task; production schedule remains disabled until the deployment network and operator review are ready.

### Phase 2 — trust, accountability and community

- [x] Seen/unseen, guest/account merge, ten-person threshold and single internal escalation case.
- [x] Comments, community updates, follow/unfollow and notifications with zero XP.
- [x] Escalation/complaint records, real official ID/source/status and adaptive public timeline.
- [x] Mobile moderator handoff, report, resolution and appeal queues.
- [x] Reviewed officer and Community Group contracts and citizen directory presentation.
- [x] Live Catch session and UI, photo/video pipeline, profile wall and zero-XP isolation.
- [ ] Complete comment abuse/removal controls and the full trust browser journey.
- [x] Add reviewed officer context and sourced Call/WhatsApp/Email/official actions to mobile area pages.
- [x] Import current official BMC ward-office board lines and valid control-room contacts for all 24 administrative wards.
- [x] Import dated current Mumbai MLA records from the Maharashtra CEO/ECI 2024 Gazette and sitting Mumbai MPs from Digital Sansad; show party, role, source and check date.
- [x] Add audited category/effective-date operational ownership rule APIs, overlap protection, public ward presentation, and officer/rule admin create/update/expiry controls.
- [ ] Populate category ownership only where current official BMC material establishes the responsible ward/central unit for that asset; roads, drains and streetlights can cross ward/central or utility responsibility and must not be blanket-assigned.
- [x] Complete Community Group edit/deactivation, inactive-record admin visibility and 90-day provenance review-due presentation.
- [ ] Add video safety decision, native FFmpeg path, Catch retry/removal/moderation UI and physical phone checks.

### Phase 3 — progress, Actions, sharing and acceptance

- [x] Combined Quest Log, shared ward goals, Actions, My Reports and Groups.
- [x] Twelve versioned badges and mobile/public Civic Cards.
- [x] Mobile Action create/edit/cancel controls and camera-oriented before/after inputs.
- [ ] Complete participant history and Action check-in/proof/reversal browser journey.
- [ ] Finish ward leaderboard selectors and stored snapshot presentation.
- [x] Implement personal Civic Card, resolved-fix and public-derivative before/after share variants with delivery-time restriction checks.
- [x] Add the Help Fix My Ward entry point using factual ward outcomes rather than community XP.
- [ ] Finish browser share/download and revocation acceptance for all variants.
- [x] Add persisted report-update, Action-reminder and linked-account push preferences.
- [ ] Add reminder schedules, PWA PNG/apple icons and live push fallback acceptance.
- [ ] Complete Catch/report/resolution/Action media retention and scheduled maintenance.
- [ ] Run full Chromium/WebKit, security, authenticated write/video load, backup/restore and rebuild acceptance.
- [ ] Run Docker Compose/ElasticMQ/Moto/image scan gates and finish contributor/moderator/admin/release guides.
- [ ] Run physical Android Chrome and iPhone Safari acceptance.
- [x] Add a scheduled BMC ward/contact and Digital Sansad member recheck with incomplete-snapshot rollback and expiry of replaced contacts/MP records.
- [ ] Enable the schedules in a reviewed AWS environment and obtain approval for BMC layer redistribution before public launch.

### Identity and live-provider setup

- [x] Keep the Google account action visible for guest and registered/demo identities, expose linked-provider state and show the exact configured callback URL.
- [x] Require both Google client ID and secret before advertising OAuth as enabled; document local and deployed redirect setup.
- [ ] Supply operator-owned Google OAuth credentials and complete live new-account, existing-account and merge acceptance. No credentials are stored in the repository.

Current container blocker: about 3 GB disk space is free; the full container/browser release gate needs at least 8 GB.

Latest focused validation: 43 backend/PostGIS tests, TypeScript and Ruff pass. All 26 current Playwright cases have passing desktop/mobile Chrome evidence after replacing stale demo-geography fixtures and adding Google-option, operational-ownership and Community Group admin coverage. A live reference refresh validated 230 Mumbai postal points, 24 BMC wards, 47 BMC contacts and six sitting Mumbai MPs. See [Google identity and Mumbai reference validation](validation/2026-09-13-google-mumbai.md).

## Historical reference UX reconciliation — 12 September

The status language in this older reconciliation is retained as implementation history. The dated three-phase checklist above is authoritative for current completion.

Read the complete [reference master](../CivicQuest_Reference_UX_Features_MASTER.md) and [UI/journey inspiration](../CivicQuest_UI_UX_User_Journey_Inspiration.md). The master repeats Part 3/sections 62–89; those are one set of work items, not duplicate features. The documents guide interaction and information hierarchy, using original CivicQuest assets and copy.

The approved V1 decisions still govern conflicts: guest-first reporting with manual location fallback; optional simple portraits outside the civic map; pending XP until accepted verification; separate lifecycle/visibility/verification; publicly gated Civic Catches; current reviewed sources for official context; operational owners separate from MLA/MP; administrative/electoral overlaps rather than a strict ward→constituency tree. No automatic complaint delivery, fixed 24-hour review promise, unsupported anonymity claim, or copied Bengaluru contacts. Public “All status” never exposes private review records. English remains the initial language with localization preparation.

### Consolidated experience work

| ID | Tasks / completion evidence | State | Existing chunks |
|---|---|---|---|
| UX-01 | Mobile detail sheets and desktop drawers for report/area/contact/resolution/dispute; keyboard focus, close/back, safe areas, upload-dismiss protection and deep links | Pending; standalone detail routes and map/filter restoration are implemented | CQ-04/05/07/09, M3/M4 |
| UX-02 | Zoom-aware geographic queries, highlighted ward summary, shared map/list counters and filters; distinguish clusters from domain hotspots; resolved green/mixed neutral styling with text cues | Partial: clusters, ward shading, category-family/status filters, grouped list, viewport restoration, truthful server totals, resolved green/mixed ochre styling and textual status cues implemented; scalable zoom queries, severity and summary cards remain | CQ-05/08, M3 |
| UX-03 | Category-specific severity guidance with unknown state, independent complaint/material subtype choices, server validation, moderator correction audit, filter consistency; no severity XP | Pending | CQ-00/02/06/07/09, M1/M4 |
| UX-04 | Capture permission help, photo replace/remove, reverse-geocode/landmark assistance, durable retry/reload/expiry, duplicate candidate choice before finalize | Partial: photo/manual location and same-page retry; remaining recovery and duplicate UX pending | CQ-06/07 |
| UX-05 | Separate “I've seen this” attention from registered verification; unique reversible confirmation, counts/last-seen, guest/account merge handling; no XP or verification from attention alone | Pending; existing upvotes and verification stay distinct | CQ-03/08/09 |
| UX-06 | Report photo, age, status and verification facts; sticky resolution/dispute actions; current-photo dispute evidence; before/after resolution view and clear review consequences | Partial domain workflows; complete browser journeys, dispute media and sticky UI remain | CQ-06/09 |
| UX-07 | Configurable sourced authority chain, role/contact sheet, phone/email/WhatsApp/portal links and prepared complaint text; external-opening event never means sent/received | Pending; effective reviewed owner resolution exists, role/contact data and UI remain | CQ-02/05/09/12 |
| UX-08 | Factual ward/constituency/representative metrics: total, active, resolved, resolution rate, average unresolved age, overlapping wards, recent reports, provenance; neutral burden comparison separate from XP leaderboard | Partial: current spatial counts, crossings, dates/review, age/rate with explicit denominators and no-data states, and linked ward/constituency pages implemented; representative profile and comparative analytics remain | CQ-05/10, M2/M4 |
| UX-09 | Adult/Gen Z mission and collection presentation with cream/sky/aqua/mint/lavender and restrained XP gold; optional portraits, verified reward feedback, reduced motion and readable contrast | Portrait flow verified; wider visual refresh and feedback pending | CQ-04/10/12, G1/G2 |
| UX-10 | Shared ward goal admin create/edit/publish/cancel, citizen progress, unique accepted outcomes and immediate reversals | Implemented with migration/API/UI, two PostGIS tests and desktop/mobile admin publish/cancel→citizen visibility tests; complete event/resolution journey integration pending | CQ-02/05/10/11, G3 |
| UX-11 | Share public report/area/impact with Web Share/copy/download fallbacks; distinct monthly/cleanup cards; notification preferences/reminders and app-shell PWA | Partial; full delivery and visibility-revocation acceptance pending | CQ-12 |
| UX-12 | Skeleton/error/empty states throughout, map/list keyboard alternative, touch targets, mobile-safe controls, strings prepared for localization; Chromium/WebKit and real phone evidence | Partial automated checks; broader screens and physical phones pending | CQ-04/14, A1 |

Community directories/applications, organization self-service, weekly email digest, full Marathi/Hindi translation, expanded BI and government integrations are reference/future-scope items. They are not silently added to the agreed V1 scope. Admin-managed Civic Actions remain the V1 bridge from issues to participation.

Next sequence: UX-01/06 contextual detail and evidence journeys → remaining UX-02 scalable discovery → UX-03/04 capture refinements → UX-07 sourced contact experience → UX-09 missions → remaining sharing/operations/security acceptance. Existing pending tasks below remain required.

### Implementation evidence added during this continuation

- M2: constituency counts now use actual report coordinates, including shared edges. Current-date/active predicates apply to lookup, map, search and detail; touching-only polygons do not create constituency associations. Representatives require explicit review and a current term (migration 0004). Imported dates, duplicate codes, geometry and immutable provenance are validated before database inserts. Four added PostGIS tests pass; full backend suite reached 25 tests before ward goals.
- M3: category filters include related waste/water categories; Explore remembers filters, mode, center and zoom across drill-down. Four new browser cases pass on desktop Chrome/Pixel 7 emulation, including constituency counts, ward links, accessibility, no horizontal overflow and cluster zoom restoration.
- G3: migration 0005 and admin-managed ward goal API/UI added. Progress is a live, rebuild-free projection: each eligible waste report resolution and completed approved Action counts once; multiple proposals/participants never multiply outcomes. Restricted/duplicate reports, cancelled events and shared-boundary events are excluded. Periods use resolution acceptance time or Action end time; no new XP. Two PostGIS goal tests and both desktop/mobile admin→citizen goal browser cases pass. Complete proof-approval integration remains pending.
- Native startup now reads cloud-backed files to EOF and replaces runtime files atomically; this fixes recurring stylesheet truncation during source synchronization.

Latest local startup: web/API/PostGIS/database-worker are running through the [native runtime](LOCAL_NATIVE.md). The current browser suite passes all 10 desktop/mobile-emulation tests, including G1 portrait persistence and accessibility. Backend suite: 21 passing on isolated PostGIS; TypeScript and upload-retry Vitest pass. These results supersede the earlier cloud-filesystem browser blockage below. G1's browser verification is complete; wider map/area acceptance, physical-phone checks and the full frozen/container stack are still pending.

## Added V1 scope — 12 September

Reference research is complete and the user has authorized resuming implementation with simple portrait avatars. [Map and gameplay additions](V1_MAP_AND_GAMEPLAY_ADDITIONS.md) records the walkthrough, confirmed answers, dependencies and acceptance criteria. Packages below remain open until their acceptance checks pass.

- M1: finalize screen/route contracts, simple portrait scope, severity definitions and shared-goal mechanics (CQ-00/04).
- M2: constituency/representative data relationships and consistent ward/constituency statistics, including provenance and boundary ambiguity (CQ-02/05).
- M3: Nammakasa-inspired civic map, ward shading, count clusters, filters and grouped list. **No game elements on the map** (CQ-04/05/08). First implementation is present; complete browser, accessibility, count-consistency and load validation remains.
- M4: ward/constituency/hotspot/report detail sheets and deep links, contextual accountability, severity review and safe sharing (CQ-05/07/08/09/12). Public area projection and the first responsive area page are implemented; constituency imports, hotspot integration, severity and browser checks remain.
- G1: optional original character selection, guest/account persistence and profile presentation; simple portrait scope confirmed (CQ-03/04/10). API, migration, six original portraits and profile/header UI are implemented; browser verification passes.
- G2: mature game theme for non-map screens, mission cards, CivicDex, collections and verified achievement feedback (CQ-04/10/12).
- G3: individual progress plus shared ward cleanup goals; admin targets and citizen visibility now pass backend/browser checks. Live projections reconcile eligible outcomes without stored counters; complete event/resolution browser integration remains (CQ-02/05/10/11).
- A1: integrated map→area→report→verified progress browser journeys, responsive/accessibility checks and updated load baseline (CQ-14).

## Existing implementation and validation gaps

- Run the frozen uv environment and full Compose stack, including ElasticMQ persistence, duplicate delivery, restart, and Docker image builds. As of 12 September, free space is approximately 6.7 GB; the earlier run had fallen below 1 GB.
- Git is readable again as of 12 September. Confirm LICENSE and dependency 