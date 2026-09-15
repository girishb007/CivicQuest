# CivicQuest UI / UX Inspiration & User Journey Specification

## Purpose

This document translates the reference UI screenshots into a single **CivicQuest product UX specification** for Copilot.

Use it as **inspiration for flow, hierarchy, interactions, information density, bottom sheets, map behavior, accountability, reporting, verification, hotspots, ward analytics, community action, and mobile-web experience**.

Do **not** copy the reference product's name, branding, exact colors, logos, typography, or text verbatim.

CivicQuest should preserve its own visual direction:

- light / white / cream surfaces,
- soft sky blue, aqua, mint, lavender,
- warm XP gold,
- coral / red for unresolved or severe issues,
- green for verified resolution / cleanup,
- game-like feedback without becoming a full game,
- mobile-first responsive website / PWA.

---

# 1. Core Experience Philosophy

CivicQuest should feel like:

> **A civic utility with the emotional feedback of a lightweight exploration game.**

The user should be able to:

```text
OPEN
→ EXPLORE CITY
→ DISCOVER ISSUE / HOTSPOT
→ OPEN ISSUE
→ UNDERSTAND WHAT IS WRONG
→ SEE WHO IS RESPONSIBLE
→ CONFIRM / BOOST / REPORT / ESCALATE
→ VERIFY CLEANUP OR FLAG INCORRECT
→ SEE WARD / MLA / MP ACCOUNTABILITY
→ JOIN COMMUNITY ACTION
→ EARN CIVIC XP / BUILD CIVIC IDENTITY
→ RETURN
```

The map is the main discovery surface.

The product should never feel like a government complaint form first.

---

# 2. Primary Navigation

Recommended Phase 1 navigation:

```text
Explore
Impact
Capture / Report
Actions
Profile
```

Mobile bottom navigation can be lightweight.

The primary action should remain highly visible:

```text
+ Report Issue
```

On a garbage-specific flow:

```text
+ Report Garbage
```

---

# 3. Main Explore Map

## Purpose

The map is the default CivicQuest home experience.

It should immediately answer:

- What is happening near me?
- Where are the worst hotspots?
- What has already been resolved?
- What can I report?
- Which areas need attention?

## Main layout

Top:

```text
CivicQuest logo
language selector
optional community / social shortcut
```

Optional retention banner:

```text
Get the weekly Mumbai Civic Digest
```

Filter bar:

```text
[ All Severity ▼ ] [ All Status ▼ ]     [ Map | List ]
```

Summary:

```text
1,248 Active    |    3,812 Reports
```

Main map:

```text
cluster markers
hotspots
individual issue markers
resolved markers
ward boundaries if useful
```

Bottom:

```text
[ Explore ] [ Impact ]      [ + Report Issue ]
```

---

# 4. Map Cluster Behavior

At low zoom, do not render thousands of individual issues.

Show numbered clusters.

Example:

```text
114
176
355
1.1k
```

## Cluster colors

Recommended:

```text
Unresolved cluster → deep coral / red
Resolved cluster   → green / mint
Mixed status       → neutral / gold
```

## Cluster interaction

```text
Tap cluster
→ zoom in
→ split into smaller clusters
→ eventually show individual issue markers
```

---

# 5. Zoom-Level UX

Recommended map behavior:

```text
CITY LEVEL
→ large clusters

WARD LEVEL
→ smaller clusters + ward summaries

NEIGHBORHOOD LEVEL
→ individual reports / hotspots

STREET LEVEL
→ exact issue pins
```

When zooming in, preserve filters and map position.

---

# 6. Individual Issue Marker Colors

At detailed zoom, use severity-aware markers:

```text
Minor     → pale yellow
Moderate  → orange
Severe    → red / coral
Critical  → dark red
Resolved  → green
```

Do not rely on color alone.

Use:

- icon shape,
- border,
- tooltip,
- accessible label.

---

# 7. Map Filters

## Severity filter

Options:

```text
All Severity
Minor
Moderate
Severe
Critical
```

The dropdown should:

- show current selection,
- dismiss on outside click,
- be keyboard accessible,
- use large touch targets.

## Status filter

Options:

```text
All Status
Unresolved
Resolved
Under Review
```

Potential later states:

```text
Acknowledged
In Progress
Disputed
```

Changing filters updates:

- map clusters,
- ward list,
- issue list,
- counters,
- leaderboard context where applicable.

---

# 8. Map / List Toggle

The same filtered dataset should be viewable as:

```text
Map
List
```

## Context-sensitive list behavior

At city scale:

```text
List = ward summaries
```

At neighborhood scale:

```text
List = individual issue reports
```

This lets users quickly move between geographic exploration and structured scanning.

---

# 9. Ward Summary Popup

At medium zoom, tapping a ward/locality should open a compact summary.

Example:

```text
Dadar West
G/North Ward
Mahim Assembly Constituency

24 active reports
```

Possible fields:

- ward/locality name,
- ward number,
- zone,
- assembly constituency,
- active report count,
- top issue category.

CTA:

```text
View Ward
```

---

# 10. Issue Detail Bottom Sheet

When a user opens an issue from the map or list, open a bottom sheet on mobile.

On desktop, use:

- right-side drawer, or
- centered responsive modal.

## Header

Show:

```text
● SEVERE     Unresolved

Dadar West
Near Shivaji Park, Mumbai

↗ Get directions
```

Actions:

- Share
- Close
- Get directions

---

# 11. Issue Image

Show the primary public-safe issue image near the top.

The image can contain a confirmation CTA:

```text
👍 I've seen this
```

This is not a social like.

It means:

> I have also observed this issue.

---

# 12. Community Confirmation

Use a feature like:

```text
I've seen this
```

or:

```text
Confirm issue
```

Effects:

- increases confirmation count,
- updates last-confirmed timestamp,
- strengthens hotspot visibility,
- helps reduce duplicate reports.

Do not treat confirmation as absolute proof.

---

# 13. Issue Quick Stats

Show compact cards:

```text
6
Also Seen

45
Days Open

Mixed Waste
Issue Type
```

Possible CivicQuest metrics:

- community confirmations,
- days unresolved,
- issue type,
- severity,
- first reported,
- last confirmed.

---

# 14. Issue Metadata Line

Show readable metadata:

```text
Reported 45 days ago
Confirmed by 6 citizens
Still unresolved
```

Avoid awkward language like:

```text
1 citizen(s)
```

---

# 15. Sticky Issue Actions

Keep the two most important corrective actions visible while the user scrolls.

For unresolved Place issues:

```text
[ ✓ Verify Cleanup ]   [ ⚑ Flag Incorrect ]
```

These remain pinned at the bottom of the sheet.

Use:

- green for positive resolution verification,
- red/coral for incorrect/dispute flow.

---

# 16. Accountability Section

This is one of the core CivicQuest differentiators.

Every issue should answer:

> **Who is responsible here?**

Display a visual responsibility chain.

Example:

```text
Your Ward
G/North
   ↓
BMC
   ↓
Solid Waste Management
   ↓
Ward-level officer
   ↓
Assistant Commissioner
   ↓
Municipal Commissioner / Department Head
```

Then separately:

```text
Elected representatives for this area

MLA
MP
```

The hierarchy must depend on:

- latitude/longitude,
- issue category,
- ward,
- responsible department,
- current official data.

Do not hardcode a single chain for all issues.

---

# 17. Accountability Node Interaction

Every authority / official node is clickable.

Tap opens a contact sheet.

Example:

```text
FRONTLINE

Ward Solid Waste Officer
First point of escalation

[ Call Helpline ]
[ WhatsApp ]
[ Email ]
```

Or:

```text
MID-TIER

Assistant Commissioner
Ward-level oversight

[ Email Office ]
[ Call Helpline ]
```

---

# 18. Contact Action Sheet

Each authority contact sheet should include:

- role level,
- title,
- short responsibility description,
- contact methods,
- close button.

Supported actions:

```text
Call
Email
WhatsApp
Open official portal
```

Only show contact channels that actually exist.

Never invent personal contact information.

---

# 19. File / Escalate Complaint

A CivicQuest report and an official complaint can be separate things.

## CivicQuest report

Creates:

- public civic record,
- map visibility,
- hotspot analytics,
- community attention.

## Official complaint

Attempts to escalate to:

- BMC,
- ward office,
- department,
- helpline,
- WhatsApp,
- official portal.

CTA:

```text
File / Escalate Complaint
```

---

# 20. WhatsApp Escalation Flow

When a user taps WhatsApp:

CivicQuest should prepare a message automatically.

Example:

```text
Hello,

I would like to report a civic issue requiring attention.

Issue: Garbage / Illegal Dumping
Location: Dadar West, Mumbai
Coordinates: <lat>, <lng>

Map:
<map link>

CivicQuest Report:
<public report URL>

Please arrange for resolution at the earliest.

Reported via CivicQuest
```

If technically possible, include or help attach the issue image.

The user should not rewrite the complaint manually.

Important:

```text
Opened WhatsApp
```

does not equal:

```text
Complaint officially submitted
```

unless CivicQuest receives confirmation.

---

# 21. Elected Representative Cards

Show the representatives covering the issue area.

Example:

```text
[Photo]

Representative Name
Party · MLA
```

and:

```text
[Photo]

Representative Name
Party · MP
```

Show:

- photo,
- name,
- party,
- role,
- constituency.

Do not imply they personally caused the issue.

They represent jurisdictional context and accountability.

---

# 22. Representative Profile

Tapping MLA or MP opens a representative analytics sheet.

Show KPI cards:

```text
126 Active
340 Reports
113 Avg Days
11 Wards
```

Potential summary:

```text
126 unresolved civic issues remain across 10 wards in this constituency.
Average unresolved duration: 113 days.
```

This summary is generated from CivicQuest data.

---

# 23. Representative Profile Sections

Include:

```text
Header
→ photo
→ name
→ party
→ role
→ constituency

KPI cards
→ active
→ total reports
→ average open days
→ ward count

Coverage
→ assembly constituencies / wards

Worst-performing areas
→ ranked ward list

Recent reports
→ issue thumbnails + severity
```

---

# 24. Worst Wards in Representative Profile

Example:

```text
1  Ward A   90
2  Ward B   76
3  Ward C   65
```

Possible ranking metrics:

- unresolved count,
- average open days,
- severity-weighted burden,
- hotspot count.

Default V1:

```text
unresolved count
```

---

# 25. Ward Accountability / Performance Page

Separate from the **user Civic XP leaderboard**.

This is geographic accountability analytics.

Top metrics:

```text
7,578 Unresolved
279 Resolved
3.6% Resolution Rate
```

Then:

```text
Areas with highest unresolved burden
```

Do not use celebratory language like:

```text
Winner
Top Ward
#1 Best
```

for areas with poor civic performance.

Use:

```text
Needs Attention
Highest Unresolved Burden
Lowest Resolution Rate
```

---

# 26. Ward Ranking Row

Each row can show:

```text
1

Sunkenahalli
Central · Ward #42

140 unresolved
141 total reports
1% resolved
```

Include a comparison bar.

Tap opens ward detail.

---

# 27. Ward Detail

Ward page should contain:

- ward name,
- number,
- zone,
- map boundary,
- unresolved count,
- resolved count,
- resolution rate,
- average open days,
- top categories,
- hotspots,
- recent reports,
- responsible municipal office,
- MLA,
- MP.

Possible CTA:

```text
View on Map
```

---

# 28. City → Ward → Issue Journey

```text
Explore map
   ↓
See city clusters
   ↓
Tap cluster
   ↓
Zoom to ward
   ↓
Tap ward summary
   ↓
Open ward detail
   ↓
Browse reports
   ↓
Open issue
```

Back navigation should preserve:

- map position,
- zoom,
- filters,
- selected status.

---

# 29. Report Issue CTA

Keep a strong sticky action:

```text
+ Report Issue
```

This must remain reachable from the map.

It should feel easier than navigating a government portal.

---

# 30. Report Creation Sheet

Open reporting as a mobile sheet.

Example:

```text
Report Garbage
```

Fields:

```text
PHOTO *
LOCATION *
LANDMARK / ADDRESS *
HOW BAD IS IT? *
COMPLAINT TYPE *
WASTE TYPE *
```

The exact form depends on category.

---

# 31. Required Photo

Show:

```text
PHOTO *

Take a Photo
```

Helper:

```text
Take a clear photo of the issue.
It helps the community verify the report.
```

Allow:

- camera,
- gallery if policy permits,
- preview,
- replace,
- remove before submit.

---

# 32. Camera Permission

When user taps photo capture:

```text
Checking camera access...
```

Then browser/system permission.

Support states:

```text
unknown
prompt
granted
denied
unsupported
```

If denied:

```text
Camera access is off

[ Try Again ]
[ How to enable camera ]
```

Do not repeatedly spam permission prompts.

---

# 33. Required Location

Location helps:

- verify field presence,
- determine ward,
- route responsibility,
- prevent fake reports.

If location is denied:

```text
Location access is off

CivicQuest needs your location to confirm where the issue is
and identify the responsible ward.

[ Try Again ]

[ How to enable location ]
```

Support help for:

- iPhone Safari,
- Android Chrome,
- desktop browsers.

---

# 34. Location-Gated Submission

Let the user fill the form even while location is unresolved.

But final CTA can show:

```text
Enable location to continue
```

Once resolved:

```text
Submit Report
```

---

# 35. Landmark / Address

Field:

```text
LANDMARK / ADDRESS *
```

Example:

```text
Near 5th Cross, opposite Reliance Fresh
```

CivicQuest should:

- reverse geocode automatically,
- allow manual landmark,
- combine both for public display.

---

# 36. Severity Selection

Use plain-language severity cards.

Example for garbage:

### Minor

```text
A few bags or scattered litter.
Small localized area.
```

### Moderate

```text
Noticeable heap.
Roughly the size of a small vehicle.
```

### Severe

```text
Large accumulation.
Blocks sidewalk or road edge.
```

### Critical

```text
Major illegal dumpsite.
Large plot / road section / health risk.
```

Each category should have category-specific severity guidance.

---

# 37. Complaint Type vs Material Type

Do not collapse all data into one category.

For garbage:

## Complaint type

```text
Missed door-to-door collection
Garbage in public place
Garbage in empty plot
Construction / demolition dumping
Street not swept
Overflowing public bin
```

## Waste type

```text
Household Waste
Construction Debris
Mixed Waste
E-Waste
Biomedical
Green Waste
```

These affect:

- routing,
- severity,
- analytics,
- authority responsibility.

---

# 38. Guest / Public Identity Messaging

The reference uses:

```text
All reports are anonymous
```

CivicQuest should only say "anonymous" if technically true.

Safer:

```text
Your public identity is not shown on this report.
```

or:

```text
You can report without showing your name publicly.
```

Guest users can still accumulate provisional Civic XP.

---

# 39. Duplicate Prevention

Before creating a new report, check nearby similar issues.

Example:

```text
We found a similar issue 18m away.

[ I've seen this too ]
[ This is a different issue ]
```

If user confirms existing:

- add confirmation,
- optionally upload new supporting photo,
- update last-confirmed time,
- increase hotspot confidence,
- avoid duplicate record.

---

# 40. Report Submission Result

After successful report:

```text
REPORT ADDED

+10 CIVIC XP

Hotspot contribution +1
```

Then:

```text
Keep Exploring
```

Use a short reward moment, not a long game animation.

---

# 41. Resolution Verification

Issue bottom action:

```text
Verify Cleanup
```

Flow:

```text
Open unresolved issue
→ Tap Verify Cleanup
→ Take current photo
→ Submit for review
→ Pending verification
→ Approved
→ Issue becomes Resolved
```

Require evidence.

Do not allow one-tap resolution.

---

# 42. Resolution Sheet

Example:

```text
Mark as Cleaned

Take a photo to verify this spot has been cleaned.

[ Take Verification Photo ]

[ Submit for Review ]
```

After approval:

- issue status = resolved,
- resolved date recorded,
- map marker turns green,
- hotspot metrics update,
- Civic XP can be awarded.

---

# 43. Flag Incorrect / Dispute

Issue action:

```text
Flag as Incorrect
```

Flow:

```text
Tap Flag Incorrect
→ Explain reason
→ Take current photo
→ Submit evidence
→ Moderation review
→ Approved or rejected
```

Example copy:

```text
This issue is no longer present or was reported incorrectly.

Take a current photo of the location.
```

---

# 44. Dispute Consequence Explanation

Clearly explain:

```text
If approved, the report may be removed from public map/analytics.
If rejected, it remains visible.
```

Do not silently remove public reports.

---

# 45. Issue Lifecycle

Recommended UX state model:

```text
Reported
→ Processing
→ Public / Verified
→ Unresolved
→ Authority Contacted
→ Cleanup Claimed
→ Resolution Review
→ Resolved
```

Alternative:

```text
Unresolved
→ Dispute Submitted
→ Review
→ Valid / Invalid
```

---

# 46. Resolved Map Mode

Users can filter:

```text
Resolved
```

Resolved clusters/issues appear in green.

This is important because users should see:

> CivicQuest does not only expose problems. It shows progress.

Resolved issue page can show:

```text
Before
After
Time to resolution
Verified by community/moderator
```

---

# 47. All Status Map

Users can also choose:

```text
All Status
```

This can show a mix of:

- unresolved,
- resolved,
- under review.

The visual semantics must remain clear.

---

# 48. Impact / Ward Analytics Screen

A dedicated impact area can show:

```text
Unresolved
Resolved
Resolution Rate
```

Then:

```text
Areas needing the most attention
```

This should feel like public accountability analytics, not a game leaderboard.

---

# 49. Volunteer Communities

Add a community directory.

Header:

```text
Volunteer Communities
Groups helping improve Mumbai
```

Each card:

- logo,
- community name,
- geographic coverage,
- description,
- social/contact links.

Example:

```text
Mumbai Ploggers
Works across Mumbai

Community cleanup and plogging group.

[ WhatsApp ] [ Instagram ]
```

---

# 50. Community Contact Links

Supported:

```text
WhatsApp
Instagram
X
Facebook
Website
Email
```

Only show valid configured channels.

External clicks should be tracked.

---

# 51. Register Your Community

CTA:

```text
+ Register your community
```

Form:

- name,
- logo,
- description,
- coverage area,
- website,
- social links,
- contact person,
- proof / verification links.

State:

```text
Submitted
Under Review
Verified
Rejected
```

Do not auto-publish organizations.

---

# 52. Communities vs Civic Actions

Keep them separate.

```text
Community
→ persistent organization
```

Example:

```text
Mumbai Ploggers
```

```text
Civic Action
→ specific event
```

Example:

```text
Juhu Beach Cleanup
Saturday 7:00 AM
```

Relationship:

```text
Community
  ↓ hosts
Civic Action
  ↓ joined by
Users
```

---

# 53. Civic Action Journey

```text
Discover community/action
→ Open cleanup event
→ Join
→ Check in
→ Participate
→ Upload before/after
→ Verify
→ Earn higher Civic XP
```

Real-world action should earn more XP than passive reporting.

---

# 54. User Civic Identity

CivicQuest can add a lightweight personal layer.

Optional early setup:

```text
Choose avatar
Choose civic name
Skip for now
```

Example:

```text
MumbaiScout
```

Guest stays usable.

Later:

```text
You've earned 120 XP.
Save your Civic Identity?
```

---

# 55. Civic Profile

Show:

- avatar,
- civic name,
- level,
- XP,
- Mumbai/local rank,
- reports,
- resolved issues,
- Civic Actions,
- CivicDex progress,
- badges.

Avoid follower-count focus.

---

# 56. CivicDex

Collect issue categories, never people.

Example:

```text
Waste & Dumping
Littering
Spitting
Water Leaks
Potholes
Streetlights
```

First valid discovery can show:

```text
NEW CIVICDEX ENTRY
```

---

# 57. User XP Leaderboard vs Ward Accountability

Keep these completely separate.

## User leaderboard

Ranks positive contribution:

```text
Civic XP
verified actions
verified resolutions
```

## Ward accountability

Ranks area performance/burden:

```text
unresolved reports
resolution rate
open days
```

Do not mix them visually.

---

# 58. Share Experience

Allow sharing:

## Issue

```text
Issue
Location
Status
Open days
Public URL
```

## Representative analytics

```text
Representative
Constituency
Active reports
Average open days
Public URL
```

## Personal Civic Impact

```text
Level
XP
Reports
Resolved
Actions
City percentile
```

Use Web Share API where possible.

Fallback:

- copy link,
- WhatsApp,
- X,
- Facebook.

---

# 59. Loading States

Do not show fake zero values.

Bad:

```text
0 Active
0 Reports
LOADING...
```

Better:

```text
[ skeleton ] Active
[ skeleton ] Reports
```

Use skeletons for:

- representative metrics,
- ward analytics,
- report cards,
- map summaries.

---

# 60. Bottom Sheet Design Pattern

Use bottom sheets consistently on mobile for:

- issue detail,
- contact actions,
- representative profile,
- reporting,
- resolution verification,
- disputes,
- volunteer communities,
- share actions.

Behavior:

- rounded top corners,
- drag handle,
- close button,
- dim background,
- scrollable content,
- safe-area support,
- preserve underlying map state.

Desktop:

- right-side drawer,
- modal,
- split pane where useful.

---

# 61. User Journey A — Explore → Issue → Accountability

```text
Open CivicQuest
→ Map loads
→ See clusters/hotspots
→ Filter severity/status
→ Tap cluster
→ Zoom to ward
→ Tap issue
→ Issue detail opens
→ See photo, severity, age, confirmations
→ Scroll accountability chain
→ Contact authority
→ View MLA / MP analytics
→ Share
→ Verify cleanup OR flag incorrect
```

---

# 62. User Journey B — Report New Issue

```text
Tap + Report Issue
→ Report sheet
→ Take photo
→ Camera permission
→ Capture
→ Location check
→ Reverse geocode
→ Add landmark
→ Select severity
→ Select complaint type
→ Select material/issue type
→ Check duplicate candidates
→ Confirm existing OR create new
→ Submit
→ Processing
→ Report added
→ Civic XP
→ Return to map
```

---

# 63. User Journey C — Resolve an Issue

```text
Open unresolved issue
→ Tap Verify Cleanup
→ Capture current photo
→ Submit proof
→ Pending review
→ Approved
→ Status = Resolved
→ Marker becomes green
→ Ward/hotspot analytics update
→ Eligible XP awarded
```

---

# 64. User Journey D — Dispute an Issue

```text
Open issue
→ Flag Incorrect
→ Explain / capture current condition
→ Submit evidence
→ Moderation review
→ Approved:
     report invalidated / removed from public analytics
   OR
  Rejected:
     report remains
```

---

# 65. User Journey E — Ward Accountability

```text
Open Impact
→ See city unresolved/resolved/rate
→ View wards needing attention
→ Tap ward
→ See ward metrics
→ Map to ward
→ View recent reports/hotspots
→ See responsible office
→ See MLA / MP
→ Open issue
```

---

# 66. User Journey F — Representative Accountability

```text
Open issue
→ Tap MLA / MP
→ Representative profile
→ KPI cards
→ Coverage areas
→ Worst-performing wards
→ Recent civic reports
→ Share profile
```

---

# 67. User Journey G — Community Action

```text
Open Actions / Community
→ Browse volunteer groups
→ Open group
→ View upcoming action
→ Join cleanup
→ GPS check-in
→ Participate
→ Upload before/after
→ Verification
→ Civic XP
→ Share impact
```

---

# 68. UX Rules for Copilot

1. Keep the **map as the primary discovery surface**.
2. Preserve map/filter/zoom state when opening and closing sheets.
3. Use **bottom sheets on mobile**.
4. Use **drawers/modals on desktop**.
5. Keep `+ Report Issue` always easy to reach.
6. Keep `Verify Cleanup` and `Flag Incorrect` visible on unresolved issue detail.
7. Use confirmation (`I've seen this`) to reduce duplicates.
8. Do not treat upvotes/confirmations as proof.
9. Require evidence for resolution and dispute flows.
10. Show accountability as **location + category → authority chain**.
11. Do not hardcode city-specific authorities.
12. Do not invent official contact details.
13. Elected representatives are jurisdictional context, not automatic blame.
14. Keep representative/ward analytics neutral and factual.
15. Do not gamify poor ward performance.
16. Keep Civic XP focused on positive contribution.
17. Real-world Civic Actions earn more XP than passive activity.
18. Keep resolved issues visible in a dedicated success/impact view.
19. Use category-specific severity descriptions.
20. Separate complaint type from material/issue subtype where useful.
21. Use skeleton loading states.
22. Make all map markers accessible beyond color alone.
23. Preserve guest-first participation.
24. Do not force account creation before value is experienced.
25. Use lightweight avatar/name only as optional Civic Identity.
26. Keep the visual theme light, friendly, modern, and civic-first.
27. Do not copy branding or exact UI from reference screenshots.
28. Optimize for Safari/Chrome mobile browser first.
29. Respect mobile safe areas and browser chrome.
30. Keep flows short enough to complete while standing outdoors.

---

# 69. Primary UI Components

```text
ExploreMapPage
├── Header
├── LanguageSwitcher
├── CivicDigestBanner
├── SeverityFilter
├── StatusFilter
├── MapListToggle
├── SummaryCounter
├── CivicMap
│   ├── ClusterMarker
│   ├── IssueMarker
│   ├── WardSummaryPopup
│   └── MapControls
└── StickyReportCTA

IssueDetailSheet
├── IssueHeader
├── IssuePhoto
├── ConfirmIssueButton
├── QuickStats
├── AccountabilityGraph
├── RepresentativeCards
├── FileComplaintCTA
├── IssueMetadata
└── StickyIssueActions

AuthorityContactSheet
├── RoleHeader
├── ResponsibilityText
└── ContactButtons

RepresentativeProfileSheet
├── RepresentativeHeader
├── KPIGrid
├── CoverageList
├── WorstWardRanking
└── RecentReports

ReportIssueSheet
├── PhotoCapture
├── LocationGate
├── LandmarkField
├── SeveritySelector
├── ComplaintTypeSelector
├── MaterialTypeSelector
├── DuplicateCandidatePanel
├── PrivacyNotice
└── SubmitButton

ResolutionVerificationSheet
├── CurrentPhotoCapture
├── ReviewNotice
└── SubmitButton

DisputeSheet
├── CurrentPhotoCapture
├── ConsequenceNotice
└── SubmitButton

WardAccountabilityPage
├── CityKPIs
├── WardRanking
└── WardRows

VolunteerCommunitiesSheet
├── CommunityCards
└── RegisterCommunityCTA

CivicProfile
├── Avatar
├── CivicName
├── Level
├── XP
├── Stats
├── CivicDex
└── ShareImpact
```

---

# 70. Final UI Product Principle

CivicQuest should not feel like:

```text
Open government form
→ Fill fields
→ Submit
→ Hope something happens
```

It should feel like:

```text
Explore your city
→ Discover a real issue
→ Understand its context
→ See who is responsible
→ Contribute evidence / attention
→ Escalate easily
→ Verify change
→ See impact
→ Build civic reputation
→ Return
```

The experience should make civic participation:

- understandable,
- visual,
- actionable,
- accountable,
- rewarding,
- easy to repeat.
