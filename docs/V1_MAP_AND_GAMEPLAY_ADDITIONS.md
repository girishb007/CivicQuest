# V1 additions: civic map and character progression

Research and requirements update: 12 September 2026. Status: implementation underway; portraits and initial geography/map journeys are verified. This extends the approved V1 plan and does not close any existing acceptance gate. The later reference master and UI/journey inspiration are reconciled in [remaining work](REMAINING_WORK.md#reference-ux-reconciliation--12-september).

## Confirmed by the user

- Follow Nammakasa's civic-map feel. **No game elements on the map**: no character, quest collectibles, game-world terrain, or game overlay. This supersedes the earlier proposed hybrid map.
- Include ward and constituency pages, representative context, and factual civic statistics. Operational responsibility remains separate from elected representation.
- Use individual progress plus shared ward cleanup goals.
- Use simple character portrait avatars (confirmed when implementation resumed). Character selection is optional; exploring and reporting remain available without choosing one. Selecting a character should make the wider application feel like a game for adults and Gen Z.
- Bring the additions into V1's remaining work. Research and clarify the new requirements before resuming implementation.

## Research method and evidence

Read the supplied [Nammakasa notes](../Nammakasa.txt), then opened the public site in Chrome at desktop and phone sizes, including Pixel 7 browser emulation. Inspected onboarding, map, filters, ward-grouped list, report detail, ward page, constituency page, community directory, and the phone capture form. No report, vote, cleanup verification, complaint, subscription, or external communication was submitted. Screenshots and text captures are in the ignored `.local/research/` directory; these are research evidence, not CivicQuest assets or seed data.

Nammakasa's observed journey is map → numbered clusters or ward-grouped list → individual report sheet → ward/accountability context → cleanup verification or incorrect-report controls. The map uses pale streets, translucent ward shading, outlined count circles, compact severity/status filters, Map/List switching, counters, and a persistent reporting action. Ward sheets show active/resolved statistics, severity distribution, representative context, and report rows. Report sheets contain age, attention count, category, operational hierarchy and separate elected representatives. Sources: [map/list](https://www.nammakasa.in/), [ward](https://www.nammakasa.in/ward/sunkenahalli), [report](https://www.nammakasa.in/report/4b96283e-9e5a-46b3-be7d-c02233cab261).

The phone form requests a photo, GPS, landmark, severity, complaint type and waste type; denied camera/location access exposed recovery guidance. Desktop offered a QR handoff. Only the form was inspected, so submission success and downstream moderation remain unverified. After loading, the constituency route showed active/report totals, average unresolved age, ward count, ranked wards and recent reports. Initial zero counters appeared alongside loading text and must not be treated as factual totals. CivicQuest will use neutral factual area summaries rather than the reference's evaluative ranking language. [Constituency](https://www.nammakasa.in/mla/Chickpet).

Corrections to the supplied teardown: live onboarding displayed 369 wards and a Kannada switch; report deep links exist. Those observations replace the older route/language inferences, not Mumbai dataset requirements. Counts changed during loading and report images were blank in some captures. The clustering algorithm, hotspot thresholds, backend, data accuracy, and unseen workflows have not been established. Community registration and external complaint/digest features are reference observations, not additions to CivicQuest scope. [Communities](https://www.nammakasa.in/communities).

For Pokémon GO, reviewed the [App Store listing](https://apps.apple.com/us/app/pok%C3%A9mon-go/id1094591345) and official documented journeys; no native game walkthrough was performed. Its character flow is profile → style/appearance → preview → apply, including achievement unlocks. Its research flow provides objectives, progress, rewards and longer task sequences. CivicQuest can adapt those patterns into optional characters, CivicDex, civic missions and verified achievement feedback using original assets. Sources: [character customization](https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/2376-how-do-i-customize-my-avatar/), [research progression](https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/45-types-of-research/). The game's [map/avatar interaction](https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/84-what-is-the-map-view/) is excluded by the user's clarification.

Accountability graph : For ward member and who is responsible for that area, surf internet get the india bmc responsible data so we can show the heirecay who is responsible for garbage in that area if and show who MLA or MP is of that area, who is the BMC, elected represenataive MP and MLA of that ward area. (You can surf the https://www.nammakasa.in/report/6cfdc672-573f-417a-b60a-0315d4712291 and see there screenshot of accountbality how they built it.)

## Proposed CivicQuest journey and visual specification

1. Open Explore immediately. Optional character setup is offered outside the map and can be skipped or revisited in Profile.
2. Explore a calm, flat Mumbai civic map: light basemap, accurate administrative outlines, restrained issue-density shading, numbered report clusters, compact filters, map/list switch, recenter/zoom and persistent Capture entry. Show a legend and clearly label the scope of counts. Use ordinary location markers only.
3. Select a cluster to zoom to reports; select a hotspot to inspect its contributing reports and history. Selecting a ward opens its summary. Mobile uses accessible bottom sheets; desktop uses a side panel. Closing or navigating back restores viewport, filters and list position. URLs support direct opening and sharing.
4. Move from ward summary to a report, hotspot, relevant constituency, or approved cleanup Action. Constituency pages show sourced representative context and statistics for the actual electoral geometry. Never assign an entire ward to a constituency simply because one point overlaps.
5. Report or verify an issue through the existing evidence workflow. Capture retains photo upload and manual location fallback, including desktop use. Nammakasa's camera/GPS requirements do not override those agreed V1 capabilities.
6. Outside the map, view character identity, mission cards, CivicDex, personal progress and shared ward goals. Pending evidence has explicit pending feedback. Accepted verification releases the existing rewards and achievement feedback.

The wider UI retains the light, airy base with a mature urban-adventure identity: original characters, deliberate typography, collection cards, achievement emblems, progress tracks and brief completion animation. Reporting, appeals and moderation retain plain factual language. Reduced motion, keyboard access and readable contrast apply throughout. The map and its detail panels stay civic and factual.

## Domain distinctions and proposed rules

| Concept | Meaning and behavior |
|---|---|
| Map cluster | Zoom-dependent aggregation of visible report markers; a count circle is not automatically a hotspot |
| Hotspot | Existing server grouping: public unresolved reports, same ward/category family, 150 m, 30 days, at least three unique reporters; keep the deterministic versioned score |
| Ward | Administrative polygon with source/version/effective dates; boundary ambiguity is explicit |
| Constituency | Separate assembly/parliamentary geometry and representation records; overlap relationships can be many-to-many |
| Density shading | Visual aid with a legend and stated metric; not a cleanliness rating or representative performance score |
| Severity | Proposed new category-aware report attribute, separate from lifecycle, verification, attention and hotspot score; optional until valid guidance exists for that category |
| Shared ward goal | Proposed admin-configured target and period counting approved cleanup outcomes in that ward; independent of personal XP and public representative statistics |

Proposed severity treatment: reporter selects a guided value; moderator can correct it with an audit entry; unknown is valid. Do not extrapolate garbage-area thresholds to every civic category. Severity never increases XP. All map, area and share aggregates use the same public eligibility predicates and exclude restricted reports, duplicate children and publicly gated Civic Catches. Label counts as reports, distinct issues, or verified outcomes consistently; no placeholder zeros during loading.

Proposed ward goals count each approved resolution or completed cleanup Action once, not once per participant. Personal Action XP remains unique per participant/event under existing rules. Reward reversal, duplicate merging, account merging and report restriction must reconcile goal projections. Goal targets and periods are explicit, administered and rebuildable; no new shared-goal XP bonus is assumed.

Confirmed character scope: simple original portrait avatars, optional and changeable from Profile. No outfit editor, earned accessories or 3D creator in V1. Persist guest selection through account linking. Store portrait selection on the server; never grant verification privileges, XP multipliers or map advantages. Profile visibility remains opt-in.

## Implementation work packages

This table is the addition work ledger. G1 and the first M3/M4 slices are now implemented with the remaining evidence recorded below; the other packages remain pending. Owners describe the implementation area, not additional staffing.

| ID / owner | Existing chunks | Tasks and dependency | Acceptance evidence |
|---|---|---|---|
| M1 Specification and UI | CQ-00, CQ-04 | Record simple portrait scope; record map/detail/portrait/mission designs and route contracts; define severity and ward-goal rules | Approved decisions distinguished from proposals; desktop and mobile screen specifications cover all states |
| M2 Geography and data | CQ-02, CQ-05 | Versioned constituency/representative relationships, area statistics, provenance, partial coverage and shared-boundary handling; follows M1 contracts | PostGIS tests cover crossings, overlaps, no data, expired versions and aggregate eligibility |
| M3 Civic map and list | CQ-04, CQ-05, CQ-08 | Nammakasa-inspired basemap styling, ward shading, legend, count clusters, filters, grouped list, selection and viewport restoration; follows M2 | Map/list counts agree; no game elements; keyboard/list fallback; 100k-report read baseline rerun |
| M4 Detail journeys | CQ-05, CQ-07, CQ-08, CQ-09, CQ-12 | Ward/constituency/hotspot/report deep links; mobile sheets and desktop panels; contextual ownership; severity input/review/filter; safe sharing | Direct link/back navigation, unknown owner, denied location, public restriction and consistent counters tested |
| G1 Character identity | CQ-03, CQ-04, CQ-10 | Optional selection, original assets, persistence, profile presentation; follows M1 | Skip → report works; guest linking preserves choice; invalid portrait identifiers rejected; no map character |
| G2 Missions and collections | CQ-04, CQ-10, CQ-12 | Apply mature game theme across non-map screens; quest and CivicDex cards, progress/reward feedback, character presentation and reduced motion | Only verified ledger events advance eligible progress; reversals and replay remain consistent |
| G3 Ward cleanup goals | CQ-02, CQ-05, CQ-10, CQ-11 | Admin target/period configuration, unique outcome contributions, public progress, rebuild/reversal; follows M2 and existing Action approval | Multiple participants do not multiply shared outcomes; cancellations, duplicate merging and approval replay reconcile correctly |
| A1 Integrated acceptance | CQ-14 | Revised citizen/admin browser journeys, accessibility and responsive checks, actual-phone review and docs | Explore → area → report → review → personal/ward progress passes; prior V1 tests remain passing |

Suggested sequence after clarification: verify the outstanding capture retry changes → M1 → M2 → M3/M4 → G1/G2 → G3 → full trust/Action browser journeys and remaining operations/security checks → A1 and release acceptance. These additions are material UI/data work, not only a palette change. They do not remove any task in [remaining work](REMAINING_WORK.md).

## Open decision and implementation defaults

- Character depth answered: use simple character portraits. No product questions currently block local implementation.
- Optional character setup, civic-only map, factual area accountability, and individual/shared-ward progress are already confirmed; do not ask those again.
- Unless revised, retain English, the light theme, verified-only XP, current hotspot thresholds, private Civic Catches by default, admin-managed Actions, and no production deployment.
- Severity definitions and admin-configured shared-goal mechanics above are engineering proposals, not answers already supplied by the user. Review them with the M1 specification; do not silently invent new XP rules.
- Approved Mumbai boundary/ownership/representative datasets remain an external prerequisite. Local fixtures must be clearly synthetic. Current research does not validate or license any source dataset.
