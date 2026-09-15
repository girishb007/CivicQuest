# Approved V1 decisions

The implementation request and this record supersede conflicting recommendations in the original vision and engineering pack. Application license remains MIT; datasets require their own provenance and license.

- Deliver a responsive Next.js web/PWA, FastAPI modular monolith, PostgreSQL/PostGIS, Redis and Python worker, with local execution and AWS configuration. Do not provision paid services or publish production.
- Cover Greater Mumbai. Unsourced ownership stays unknown; demo boundaries and reports are labeled synthetic. Real geography requires a separately reviewed import.
- Guests can report and vote. Registered identities can verify, join events and opt into public handles. Google linking preserves activity and deduplicates entitlements.
- Separate report status, visibility and verification. Low-risk Places can auto-publish; failed, absent or uncertain safety checks require review. Civic Catches remain publicly gated.
- Bank XP only after verification. Two independent registered confirmations verify Places; disputes require a moderator; Civic Catches and resolutions require moderators.
- Rewards: Place 10, Catch 5, first verification bonus 5, accepted verifier 2, resolution 15, resolution verifier 10, verified action 120. No vote XP. Daily non-action cap 100 in Asia/Kolkata. Level threshold 100*(level-1)^2.
- Admins create events and verify proof. Check-in requires joined status, time window, <=100 m distance, <=50 m GPS accuracy and single-use challenge.
- Public originals are prohibited. Derivatives strip metadata and support redaction. Hidden content is removed from public projections and sharing. Offline cache contains app shell only.
- Include inbox, opt-in browser push, three share-card types, CivicDex, quests, streaks, city/ward leaderboards, moderation, abuse and appeals.
- Initial duplicate window: 50 m / 48 hours. Hotspot window: same ward/category family / 150 m / 30 days / three unique reporters, deterministic and zero-vote-safe.
- English UI, light theme, local demo without credentials. Production adapters are separately tested when credentials arrive.
- Local retention defaults: original evidence 30 days after case closure, security logs 14 days, restricted audit 365 days. Open cases hold evidence. Public deployment requires policy review and named operators.

## External release gates

Live provider credentials and AWS account/domain/budget; reviewed and licensed boundary/ownership data; staffed moderation and appeals; approved privacy/retention/AI-region policy; actual-phone and live staging validation.

## Confirmed V1 additions — 12 September 2026

The later UX reference master and user-journey inspiration guide the remaining interaction design. Their duplicated sections are reconciled into UX-01–UX-12 in [remaining work](REMAINING_WORK.md). Existing V1 decisions override conflicting examples about mandatory GPS, immediate XP, public review records, strict ward/electoral hierarchies and self-service organizers. Contact deep links remain citizen-initiated; no automated external complaint delivery is authorized.

Shared-goal implementation default `ward-outcomes-v1`: an eligible waste resolution counts once per public non-duplicate report; a completed Civic Action with at least one currently verified participant counts once per event. Resolution acceptance time and event end time determine the goal period (start inclusive, end exclusive). Admin dates are interpreted in Mumbai time. Live projections reconcile restrictions/cancellations without an additional ledger or XP. Full event-to-goal browser acceptance remains required.

- Follow Nammakasa's civic-map visual and navigation direction. No game elements on the map; this replaces the proposed hybrid map/avatar approach.
- Add ward and constituency pages with representative context and factual civic statistics. Keep operational ownership separate.
- Use individual progress plus shared ward cleanup goals.
- Character selection is optional and contributes to an adult/Gen Z game feel outside the map. Guests can explore and report without selecting a character. Use simple character portraits; no outfit customization or 3D creator in V1.
- Research the reference journeys and clarify requirements before continuing implementation. The [addition specification](V1_MAP_AND_GAMEPLAY_ADDITIONS.md) distinguishes confirmed decisions, observed reference behavior and proposed implementation defaults.
