# CivicQuest Reference UX Specification — Part 1
## Accountability, Escalation, Verification, Representative Analytics & External Reporting

**Purpose:**  
This document converts the attached reference screenshots into a functional product specification that can be given to an engineering Copilot. It describes behavior, user journey, states, components, data needs, and backend expectations rather than copying the source application's branding or exact UI.

**Important CivicQuest adaptation:**  
The screenshots use Bengaluru-specific entities such as BSWML, ward numbers, local officials, MLA/MP names, and the 1533 helpline. CivicQuest must treat all of these as dynamic location-dependent data. For the Mumbai Phase 1 pilot, equivalent data should come from BMC / ward / department / representative mappings.

---

# 1. Core Feature: Civic Issue Detail Sheet

When a user opens a civic issue from the map or feed, show an **issue detail bottom sheet / drawer** over the current page.

## Header

Display:

- Severity badge
  - Example states: `Critical`, `Severe`, `Moderate`, `Low`
- Resolution state
  - Example: `Unresolved`
- Issue locality / neighborhood
- Human-readable address
- `Get directions` action
- Share icon
- Close icon

### Example

```text
● SEVERE    Unresolved

Sagayapuram
Karnataka Holy Cross Sisters 47 Davies Road

↗ Get directions
```

For CivicQuest, the same component should work with any city:

```text
● SEVERE    Unresolved

Dadar West
Near Shivaji Park, Mumbai

↗ Get directions
```

## Quick issue metrics

Display compact statistic cards near the top of the issue detail.

Observed examples:

- **Also Seen**
  - Number of other users who reported / confirmed the same issue
- **Days**
  - Number of days the issue has remained open
- **Waste Type / Issue Type**
  - Example: `Mixed Waste`

Recommended CivicQuest fields:

```text
community_confirmation_count
open_days
category
severity
status
first_reported_at
last_confirmed_at
```

---

# 2. Core Feature: Accountability Chain

The strongest feature shown in the screenshots is a **visual accountability hierarchy** for the specific issue location.

The product should answer:

> Who is responsible for this issue, from the local frontline official all the way up to the larger municipal / political chain?

## Example hierarchy shown in reference

```text
Ward
  ↓
Municipal Waste Organization
  ↓
Commissioner
  ↓
Additional Commissioner
  ↓
Assistant Executive Engineer
  ↓
Junior Health Inspector
```

The reference also separately displays elected representatives associated with the ward:

```text
MLA
MP
```

## CivicQuest interpretation

The hierarchy should be **generated dynamically based on:**

1. Issue latitude / longitude
2. Administrative ward
3. Issue category
4. Responsible municipal department
5. Current office holders / responsible roles
6. Relevant elected representatives

Example for Mumbai:

```text
Issue location
   ↓
BMC Ward
   ↓
Responsible Department
   ↓
Ward-level Officer
   ↓
Assistant Commissioner / Ward Officer
   ↓
Municipal Commissioner / Department Head
   ↓
MLA
   ↓
MP
```

Do not hardcode one hierarchy globally. Different issue types can have different responsibility chains.

Example:

```text
Garbage issue
→ Solid Waste Management

Pothole
→ Roads Department

Water leak
→ Hydraulic Engineering / Water Department

Railway issue
→ Railway authority
```

---

# 3. Interactive Accountability Nodes

Every authority / official shown in the accountability chain should be **clickable**.

Clicking a role opens a contact-action bottom sheet.

## Contact sheet structure

Display:

- Role level
  - Example: `FRONTLINE`, `MID-TIER`
- Role title
- Short responsibility description
- Available contact methods
- Close button

### Example: Additional Commissioner

```text
MID-TIER

Additional Commissioner
Corporation-level oversight · North Corp

[ Email Joint Commissioner ]

[ Call helpline ]
```

### Example: Frontline officer

```text
FRONTLINE

Junior Health Inspector (JHI)
Ward-level SWM officer · First point of escalation

[ Call helpline ]

[ WhatsApp civic authority ]
```

## Contact actions supported

The screenshots demonstrate:

- Email
- Phone / helpline
- WhatsApp
- Potential sharing/escalation

CivicQuest should model contacts generically:

```json
{
  "authority_id": "...",
  "role": "Junior Health Inspector",
  "level": "frontline",
  "description": "Ward-level solid waste officer",
  "contacts": [
    {
      "type": "phone",
      "label": "Call helpline",
      "value": "..."
    },
    {
      "type": "whatsapp",
      "label": "WhatsApp",
      "value": "..."
    },
    {
      "type": "email",
      "label": "Email",
      "value": "..."
    }
  ]
}
```

If a particular official has no direct public contact information, show the department / official helpline rather than inventing contact details.

---

# 4. External WhatsApp Escalation

A user can escalate or report the civic issue directly through WhatsApp.

The reference flow opens an official/business WhatsApp conversation with content already prepared.

## Expected CivicQuest behavior

When the user taps:

```text
WhatsApp authority
```

CivicQuest should generate a deep link containing a **pre-filled message**.

Suggested template:

```text
Hello,

I would like to report a civic issue requiring attention.

Issue: Garbage / Illegal Dumping
Location: Dadar West, Mumbai
Coordinates: 19.xxxxxx, 72.xxxxxx

Map:
<map link>

CivicQuest Report:
<public report URL>

Please arrange for resolution at the earliest.

Reported via CivicQuest
```

If the platform supports media sharing reliably, attach or guide the user to attach the issue photo.

## Key UX requirement

The user should **not have to manually write the complaint again**.

CivicQuest should prepare:

- Issue category
- Address
- Coordinates
- Map URL
- CivicQuest report URL
- Short complaint text
- Photo where technically supported

Then the user only presses **Send** in WhatsApp.

---

# 5. Elected Representative Cards

The accountability section shows elected representatives associated with the location.

Observed examples:

- MLA
- MP

Each representative card includes:

- Photo
- Name
- Party
- Role
- Constituency
- Clickable profile

Example:

```text
A. C. Srinivasa
INC · MLA
```

```text
Shobha Karandlaje
BJP · MP
```

## CivicQuest requirement

Do not treat these cards as claims that the elected representative personally caused the issue.

They represent:

> The elected representatives covering the area in which the issue exists.

Recommended fields:

```text
representative_id
name
role_type
party
constituency_name
photo_url
official_profile_url
effective_from
effective_to
source_url
```

---

# 6. Representative Accountability Profile

Clicking an MLA / MP opens a **representative analytics profile**.

This profile aggregates civic reports inside the representative's geographic jurisdiction.

## KPI cards shown

Observed fields:

- **Active**
  - Current unresolved issues
- **Reports**
  - Total reports
- **Avg Days**
  - Average unresolved duration / resolution wait
- **Wards**
  - Number of wards represented in the dataset

Example:

```text
126 Active
340 Reports
113 Avg Days
11 Wards
```

MP example:

```text
1730 Active
5075 Reports
112 Avg Days
115 Wards
```

## Generated summary

The interface generates a readable summary such as:

```text
126 garbage dumps across 10 wards remain unresolved in this constituency.
Average wait time: 113 days.
```

CivicQuest should generate this from data, not store it as static copy.

Possible backend calculation:

```text
active_count =
count(report where status != resolved)

total_reports =
count(all reports within representative boundary)

average_open_days =
avg(now - first_reported_at for unresolved reports)

ward_count =
count(distinct ward_id)
```

---

# 7. Worst-Performing Wards Ranking

Representative profiles include a ranked list of wards with the highest unresolved issue burden.

Example:

```text
WORST WARDS

1  Shampura          90
2  Pulakeshi Nagar   76
3  Sagayapuram       65
4  S.K Garden        48
5  Kushal Nagar      23
```

For an MP, the ranking can span many assembly constituencies / wards.

Each row can show:

- Rank
- Ward / locality
- Zone / region
- Ward number
- Parent assembly constituency if relevant
- Active issue count / hotspot score

## CivicQuest equivalent

Possible filters:

```text
Worst wards by:
- unresolved count
- average open days
- severity-weighted score
- number of hotspots
```

V1 can default to unresolved issue count.

---

# 8. Assembly / Constituency Coverage

For MP-level profiles, the UI can show the assembly constituencies contained within the parliamentary constituency.

Example shown:

```text
ASSEMBLY CONSTITUENCIES

Byatarayanapura
Pulakeshinagar
Hebbal
Dasarahalli
K R Pura
Yeshwanthapura
Mahalakshmi Layout
Malleshwaram
```

## CivicQuest data relationship

```text
Country
  ↓
State
  ↓
Parliamentary Constituency
  ↓
Assembly Constituency
  ↓
Municipal Ward
  ↓
Report / Hotspot
```

This hierarchy should live in geospatial/reference data rather than being hardcoded in UI.

---

# 9. Recent Reports Inside Representative Profile

Representative profiles also show **recent issue reports within their jurisdiction**.

Each recent report row contains:

- Thumbnail
- Locality
- Address snippet
- Time / relative timestamp
- Severity badge

Example:

```text
Shampura
7th cross, Ramaih Layout...
SEVERE
```

The user should be able to tap the row and open the full issue detail.

Recommended endpoint concept:

```http
GET /representatives/{id}/reports
    ?status=open
    &sort=recent
```

---

# 10. Issue Dispute Flow: "This Isn't Garbage"

Users can challenge an incorrect report.

The screenshot shows a dedicated bottom sheet:

```text
This isn't garbage

Take a photo of the spot to show it's not garbage.
Our team will review within 24 hours.
```

## Required flow

1. User opens an issue.
2. User chooses `Dispute` / `This issue is incorrect`.
3. CivicQuest requests a **current verification photo**.
4. User takes/uploads photo.
5. User submits for review.
6. Dispute enters moderation queue.
7. Reviewer approves or rejects.
8. Public report state changes accordingly.

## UI elements

- Explanation
- Camera / upload area
- Current-state photo
- Submit for Review button
- Review expectation message

## Important explanation shown

The reference explains the consequence:

```text
If approved, this report is removed from the public map and analytics.
If rejected, it remains.
Clearly fraudulent disputes may be ignored.
```

CivicQuest should provide similarly clear consequence text.

## Recommended data object

```json
{
  "dispute_id": "...",
  "report_id": "...",
  "submitted_by": "...",
  "reason": "issue_not_present",
  "verification_media_id": "...",
  "status": "pending_review",
  "created_at": "..."
}
```

Possible states:

```text
pending_review
approved
rejected
ignored_abuse
```

---

# 11. Resolution Verification: "Mark as Cleaned"

Users can claim that an issue has been resolved.

The reference flow is:

```text
Mark as Cleaned

Take a photo to verify this spot has been cleaned.
We'll review it within 24 hours.
```

## CivicQuest flow

1. Open unresolved issue.
2. Tap `Mark as resolved` / `Mark as cleaned`.
3. Require a current photo.
4. Optionally verify location.
5. Submit proof.
6. Mark submission as `resolution_pending`.
7. Moderator / trusted verifier reviews proof.
8. If approved:
   - report becomes resolved,
   - `resolved_at` is recorded,
   - map styling changes,
   - hotspot counts recalculate,
   - reporter / verifier can receive XP.

## Required fields

```text
resolution_submission_id
report_id
submitted_by
photo
location
submitted_at
review_status
reviewed_by
reviewed_at
```

## Product principle

A user should **not** be able to mark an issue resolved with one tap.

Resolution needs evidence.

---

# 12. Issue Status Lifecycle

Based on these screenshots, CivicQuest should support more than just `open` and `closed`.

Recommended lifecycle:

```text
Reported
   ↓
Processing
   ↓
Public / Verified
   ↓
Unresolved
   ↓
Authority Contacted
   ↓
Cleanup Claimed
   ↓
Resolution Review
   ↓
Resolved
```

Alternative branches:

```text
Unresolved
   ↓
Dispute Submitted
   ↓
Review
   ├── Valid issue → remains public
   └── Invalid issue → removed / invalidated
```

---

# 13. Share Feature

Issue and representative profiles show a share action.

CivicQuest should support sharing:

## Issue

Share:

```text
Issue title/category
Location
Status
Open days
Public CivicQuest URL
```

## Representative accountability profile

Share:

```text
Representative
Constituency
Active unresolved reports
Average age
CivicQuest analytics URL
```

Use the browser's native Web Share API when available.

Fallback:

```text
Copy link
WhatsApp
X
Facebook
```

---

# 14. Loading State

One screenshot shows representative analytics before data is loaded:

```text
0 Active
0 Reports
0 Avg Days
115 Wards

LOADING...
```

For CivicQuest, avoid misleading users with fake `0` values while data is loading.

Preferred UX:

```text
skeleton cards
```

rather than:

```text
0
0
0
```

until actual values arrive.

---

# 15. Bottom Sheet Interaction Pattern

A consistent UX pattern across these screenshots is the **mobile bottom sheet**.

Use this pattern for:

- issue details,
- authority contacts,
- representative profiles,
- resolution verification,
- report disputes,
- sharing options.

## Bottom sheet behavior

- rounded top corners,
- drag handle,
- close button,
- background dimming,
- scrollable content,
- preserve underlying context,
- swipe down to dismiss if safe,
- avoid dismissing while upload/submission is in progress without confirmation.

For the website/PWA, desktop can use:

- right-side drawer, or
- centered modal,

while mobile uses the bottom sheet.

---

# 16. Suggested CivicQuest Component Architecture

```text
IssueDetailSheet
├── IssueHeader
├── IssueQuickStats
├── AccountabilityGraph
│   ├── WardNode
│   ├── AuthorityNode
│   ├── OfficerNode
│   └── RepresentativeNode
├── IssueActions
│   ├── GetDirectionsButton
│   ├── ShareButton
│   ├── MarkResolvedButton
│   └── DisputeButton
└── RecentActivityTimeline

AuthorityContactSheet
├── AuthorityHeader
├── ResponsibilityDescription
└── ContactActionList

RepresentativeProfileSheet
├── RepresentativeHeader
├── AccountabilityKPIs
├── SummaryCard
├── ConstituencyList
├── WorstWardRanking
└── RecentReports

ResolutionVerificationSheet
├── Explanation
├── CameraUploader
├── LocationVerification
└── SubmitReviewButton

DisputeReportSheet
├── Explanation
├── CameraUploader
├── ConsequenceInfo
└── SubmitReviewButton
```

---

# 17. Suggested Backend Domains

These screenshots imply the following CivicQuest backend capabilities.

```text
reports
report_media
report_status_history
report_confirmations

administrative_areas
wards
assembly_constituencies
parliamentary_constituencies

authorities
departments
official_roles
official_contacts

representatives
representative_boundaries

report_disputes
resolution_submissions
moderation_cases

share_links
external_escalations
```

---

# 18. Suggested API Surface

## Issue

```http
GET /reports/{reportId}
GET /reports/{reportId}/accountability
GET /reports/{reportId}/timeline
POST /reports/{reportId}/share
```

## Resolution

```http
POST /reports/{reportId}/resolution-submissions
GET  /reports/{reportId}/resolution-submissions
```

## Dispute

```http
POST /reports/{reportId}/disputes
GET  /reports/{reportId}/disputes/me
```

## Accountability

```http
GET /accountability/resolve
    ?lat=
    &lng=
    &category=
```

Response:

```json
{
  "ward": {},
  "authority_chain": [],
  "representatives": []
}
```

## Authority contact

```http
GET /authorities/{authorityId}
GET /authorities/{authorityId}/contacts
```

## Representative

```http
GET /representatives/{representativeId}
GET /representatives/{representativeId}/metrics
GET /representatives/{representativeId}/wards
GET /representatives/{representativeId}/reports
```

---

# 19. Representative Metrics Data Model

CivicQuest can calculate representative metrics dynamically.

```json
{
  "representative_id": "...",
  "active_report_count": 126,
  "total_report_count": 340,
  "average_open_days": 113,
  "ward_count": 11,
  "hotspot_count": 8,
  "resolved_report_count": 214,
  "resolution_rate": 0.63
}
```

These should derive from reports spatially located inside the representative's jurisdiction.

---

# 20. External Action Tracking

When users tap:

- WhatsApp
- Email
- Call
- Get directions
- Share

CivicQuest should log an analytics event.

Examples:

```text
authority_whatsapp_clicked
authority_email_clicked
authority_phone_clicked
directions_clicked
issue_shared
representative_shared
resolution_submission_started
resolution_submission_completed
report_dispute_started
report_dispute_completed
```

Do **not** claim that the authority received or acted on a complaint merely because a user clicked the button.

Use wording such as:

```text
Opened WhatsApp
```

rather than:

```text
Complaint sent
```

unless CivicQuest actually has confirmation.

---

# 21. Important UX Principles Learned From These Screens

## A. Show responsibility, not only the problem

Bad:

```text
Garbage at Dadar.
```

Better:

```text
Garbage at Dadar.

Responsible:
BMC
G/North Ward
Solid Waste Management
Ward-level official
MLA
MP
```

## B. Make escalation actionable

Do not just list contact information.

Provide buttons:

```text
Call
Email
WhatsApp
Get directions
Share
```

## C. Let the community correct the data

Two critical actions:

```text
This report is wrong
```

and

```text
This issue has been resolved
```

Both require evidence and review.

## D. Convert individual issues into accountability analytics

A single report contributes to:

```text
Ward statistics
↓
Assembly constituency statistics
↓
MP constituency statistics
↓
City statistics
```

## E. Keep proof attached to state changes

Examples:

```text
Report exists
→ original evidence

Issue cleaned
→ new verification photo

Report disputed
→ current-state photo
```

No major public status change should rely only on a button press.

---

# 22. Recommended CivicQuest User Journey

```text
User opens map
       ↓
Finds civic issue
       ↓
Opens Issue Detail
       ↓
Sees severity + age + category
       ↓
Sees accountability chain
       ↓
Can contact responsible authority
       ↓
Can inspect MLA / MP accountability statistics
       ↓
Can share the report
       ↓
Later another user can:
    ├── confirm issue still exists
    ├── dispute incorrect report
    └── submit proof that it is resolved
       ↓
CivicQuest reviews evidence
       ↓
Issue status updates
       ↓
Ward / representative / city analytics update
```

---

# 23. Copilot Implementation Rules

When implementing these features:

1. **Do not hardcode Bengaluru-specific names or helpline numbers.**
2. Resolve authorities dynamically from location + category.
3. Store source/provenance for government contact data.
4. Treat elected representatives as jurisdictional context, not automatic blame.
5. Require evidence for dispute/resolution workflows.
6. Keep original media private and generate public-safe derivatives.
7. Never mark a dispute or resolution approved without backend state confirmation.
8. Use mobile bottom sheets, but responsive drawers/modals on desktop.
9. Use clear loading/error/empty states.
10. Log external contact clicks separately from confirmed government actions.
11. Use current effective dates for representatives and officials.
12. Keep all accountability nodes configurable because different cities use different administrative structures.
13. Do not expose private reporter information in authority or representative analytics.
14. Recalculate aggregate metrics after report state changes.
15. Keep contact actions accessible with semantic buttons and visible labels.

---

# 24. Part 1 Feature Checklist

- [ ] Issue detail bottom sheet
- [ ] Severity badge
- [ ] Resolution status
- [ ] Location + address
- [ ] Get directions
- [ ] Share
- [ ] Community confirmation count
- [ ] Open-day counter
- [ ] Issue / waste type
- [ ] Ward display
- [ ] Accountability hierarchy
- [ ] Municipal organization node
- [ ] Official role nodes
- [ ] Clickable authority contact sheet
- [ ] Email action
- [ ] Phone action
- [ ] WhatsApp escalation
- [ ] Pre-filled complaint message
- [ ] MLA card
- [ ] MP card
- [ ] Representative analytics profile
- [ ] Active issue count
- [ ] Total reports count
- [ ] Average open days
- [ ] Ward count
- [ ] Constituency hierarchy
- [ ] Worst wards ranking
- [ ] Recent reports list
- [ ] Dispute incorrect report
- [ ] Evidence/photo upload for dispute
- [ ] Mark as cleaned/resolved
- [ ] Verification photo
- [ ] Moderation review workflow
- [ ] Analytics update after resolution
- [ ] External-action analytics
- [ ] Loading / skeleton states

---

## Status

**Part 1 captured from the current screenshot batch.**

Additional screenshot batches should be appended to this document as new sections rather than replacing these requirements.

---

# CivicQuest Reference UX Specification — Part 2
## Map Discovery, Report Creation, Confirmation, Permissions, Filters & Anonymous Reporting

**Purpose:**  
This section extends Part 1 using the second screenshot batch. It focuses on the **main map experience**, **report creation form**, **location/camera permission handling**, **community confirmation**, **sticky issue actions**, **status filtering**, and **anonymous-reporting cues**.

The implementation should reproduce the interaction logic and user journey, not copy the reference product's branding or exact visual styling.

---

# 25. Main Map as the Default Discovery Experience

The screenshots show the map as the primary landing surface.

For CivicQuest Phase 1, the map should remain the main entry point after the lightweight guest/onboarding flow.

## Core map elements

Display:

- City map
- Cluster markers
- Issue count per cluster
- Severity/status filtering
- Resolved/unresolved filtering
- Map/List toggle
- Zoom controls
- Optional user-location control
- Primary `Report` CTA
- Lightweight aggregate counters

### Example structure

```text
[ All Severity ▼ ] [ Unresolved ▼ ]      [ Map | List ]

         7,578 Active   |   7,578 Reports

       map with clustered report markers

[ secondary nav ]                 [ + Report Garbage ]
```

For CivicQuest:

```text
[ All Severity ▼ ] [ Unresolved ▼ ]      [ Map | List ]

         1,248 Active   |   3,812 Reports

       Mumbai civic issue map

[ Explore / stats ]               [ + Report Issue ]
```

---

# 26. Map Clustering

The screenshots use large numbered circles to represent groups of nearby reports.

## Cluster behavior

At low zoom:

- show aggregate cluster marker,
- marker contains issue count,
- size can scale with count,
- color can indicate status or dominant severity.

Observed pattern:

- red/dark red clusters for unresolved reports,
- green clusters for resolved reports.

## CivicQuest recommendation

Use:

```text
Unresolved = warm red / coral
Resolved   = green / mint
Mixed      = neutral/gold or segmented
```

At higher zoom:

- split large clusters,
- eventually show individual issue pins.

## Cluster data

Recommended response:

```json
{
  "type": "cluster",
  "cluster_id": "...",
  "lat": 19.0760,
  "lng": 72.8777,
  "count": 176,
  "active_count": 160,
  "resolved_count": 16,
  "dominant_severity": "severe"
}
```

## Backend

Possible API:

```http
GET /explore/clusters
    ?bbox=
    &zoom=
    &status=
    &severity=
    &category=
```

Use server-side or PostGIS aggregation.

---

# 27. Global Map Filters

The screenshots show:

```text
All Severity
Unresolved
```

and the same map can be switched to:

```text
Resolved
```

## CivicQuest filter set

Phase 1:

### Severity

```text
All Severity
Minor
Moderate
Severe
Critical
```

### Status

```text
All
Unresolved
Resolved
Under Review
```

Optional later:

```text
Acknowledged
In Progress
Disputed
```

### Category

Could later add:

```text
Garbage
Pothole
Water leak
Drainage
Streetlight
Civic Catch
```

## Filter behavior

- filters update map clusters,
- counters update,
- list view uses the same filter state,
- filters should persist while toggling Map/List,
- filters should be represented in the URL where reasonable.

Example:

```text
/explore?status=unresolved&severity=severe
```

---

# 28. Map/List Toggle

The screenshots expose a two-state switch:

```text
Map | List
```

## Requirement

Users should be able to view the same filtered dataset as:

### Map
Best for geographic exploration.

### List
Best for quickly scanning:
- recent reports,
- severity,
- locality,
- open age,
- thumbnails.

Both views should share the same query/filter state.

---

# 29. Aggregate Counters

The map shows lightweight summary counters such as:

```text
7,578 Active
7,578 Reports
```

Resolved view shows:

```text
0 Active
279 Reports
```

## CivicQuest counters

Recommended:

```text
Active
Total Reports
Resolved
Hotspots
```

Do not overload the map with four metrics at once.

For Phase 1, show two contextual counters:

### Unresolved filter

```text
Active
Total Reports
```

### Resolved filter

```text
Resolved
Total Reports
```

Counters should come from the same filtered query as the map.

---

# 30. Persistent Primary Report CTA

The screenshots keep a strong CTA at the bottom:

```text
+ Report Garbage
```

This is important.

Users should not need to navigate through menus to submit a civic issue.

## CivicQuest

Use:

```text
+ Report Issue
```

or contextually:

```text
+ Report Garbage
```

if the experience is scoped to a single issue category.

The CTA should remain easy to reach on mobile.

### Mobile behavior

- sticky/fixed near bottom,
- respect Safari bottom safe area,
- avoid overlapping browser controls,
- remain visible during map exploration.

---

# 31. Report Creation Bottom Sheet

The report flow opens as a large mobile sheet rather than navigating away entirely.

Title example:

```text
Report Garbage
```

## Recommended sections

```text
Report Issue

PHOTO *
LOCATION *
LANDMARK / ADDRESS *
HOW BAD IS IT? *
COMPLAINT TYPE *
WASTE / ISSUE TYPE *
[ Submit Report ]
```

The exact fields must be category-specific.

---

# 32. Photo Is Required

The screenshots make the photo field mandatory.

```text
PHOTO *
Take a Photo

A photo makes your report 10x more credible
```

## CivicQuest requirement

For report types where visual evidence is appropriate:

- photo required,
- camera preferred,
- gallery upload optionally allowed,
- preview before submission,
- replace/remove photo before submission.

Suggested helper copy:

```text
Take a clear photo of the issue.
It helps the community verify the report.
```

Avoid making unsupported numerical claims like "10x more credible" unless CivicQuest has evidence for that statistic.

## Media validation

Validate:

- image type,
- max file size,
- minimum dimensions,
- corrupted file,
- upload completion.

---

# 33. Camera Permission Flow

One screenshot shows the website checking camera permission and then the iOS browser permission dialog.

The UI displays:

```text
Checking camera access...
```

before the system permission dialog.

## CivicQuest flow

```text
User taps Take Photo
      ↓
Check browser camera capability
      ↓
Request camera permission
      ↓
Allowed?
 ├── Yes → open camera capture
 └── No  → show recovery instructions
```

## Browser considerations

Use:

```javascript
navigator.mediaDevices.getUserMedia(...)
```

where appropriate, or mobile file input:

```html
<input type="file" accept="image/*" capture="environment">
```

for reliable mobile capture.

## Permission states

Support:

```text
unknown
prompt
granted
denied
unsupported
```

Do not repeatedly trigger permission prompts after denial.

---

# 34. Location Is Required for Authenticity

The report form displays a strong error state:

```text
Location access is off

NammaKasa needs your GPS to verify you're at this spot.
This keeps reports authentic.
```

This is a useful pattern for CivicQuest.

## CivicQuest requirement

For a new field report, capture:

- latitude,
- longitude,
- accuracy,
- timestamp,
- optional browser location source.

Location can be required to qualify for:
- verified report status,
- Civic XP,
- local responsibility mapping.

## Permission recovery UI

If location is off:

```text
Location access is off

CivicQuest needs your location to confirm where the issue is
and identify the responsible ward.

[ Try Again ]

[ How to enable location ]
```

The screenshots also show a platform-specific help expansion:

```text
How to enable on iPhone
```

## CivicQuest should support help content for

- iOS Safari
- Android Chrome
- desktop browsers

---

# 35. Location Gating

One screenshot shows the report CTA disabled until location is enabled:

```text
Enable location to continue
```

## Recommended behavior

Do not allow the final submission when required location is missing.

However, let the user fill other fields while location is unresolved.

Button states:

```text
Enable location to continue
```

then:

```text
Submit Report
```

when valid.

This is better than blocking the entire form.

---

# 36. Landmark / Address Field

The report form contains:

```text
LANDMARK / ADDRESS *
```

Example placeholder:

```text
Near 5th Cross, opposite Reliance Fresh
```

## CivicQuest behavior

Automatically prefill a reverse-geocoded address when possible.

Allow the user to add a landmark because civic locations are often easier to identify using local references.

Recommended fields:

```text
latitude
longitude
location_accuracy_m
reverse_geocoded_address
user_landmark
```

Public display can combine:

```text
Near Shivaji Park Gate 3, Dadar West
```

---

# 37. Human-Friendly Severity Selection

The screenshots do something important: severity is not only a label. Each level explains what it means using a real-world size comparison.

Observed examples:

### Minor

```text
A few bags or scattered litter — fits in a small area (under 1m²)
```

### Moderate

```text
Noticeable heap — roughly the size of an auto-rickshaw (1–5m²)
```

### Severe

```text
Covers a significant area — sidewalk blocked or road edge piled up (5–20m²)
```

### Critical

```text
Major illegal dumpsite — occupies a vacant plot or entire stretch of road (20m²+)
```

## CivicQuest requirement

Use **category-specific severity guidance** so users do not guess what `Severe` means.

Example:

```text
Garbage severity:
Minor → scattered litter
Moderate → visible heap
Severe → blocks pedestrian/road space
Critical → large dumpsite / health or access risk
```

For potholes, severity criteria would be different.

## UI behavior

Each severity option includes:

- colored dot,
- label,
- short description,
- selected border/highlight.

Only one severity can be selected.

---

# 38. Complaint Type

The screenshots separate **complaint type** from **waste type**.

Observed complaint types:

```text
Door-to-door collection missed
Garbage in a public place
Garbage in an empty plot
Construction & demolition waste
Street not swept / cleaned
```

This is a strong data-model lesson.

## CivicQuest

Do not collapse everything into one `category`.

For garbage issues, separate:

```text
Issue / complaint type
```

from:

```text
Material / waste type
```

Example:

### Complaint type

```text
Missed collection
Public dumping
Empty-plot dumping
Construction debris
Street cleanliness
Overflowing municipal bin
```

### Waste type

```text
Household waste
Construction debris
Mixed waste
E-waste
Biomedical
Green waste
```

This allows routing to the right department and better analytics.

---

# 39. Waste Type

Observed choices:

```text
Household Waste
Construction Debris
Mixed Waste
E-Waste
Biomedical
```

## CivicQuest requirement

Waste type should be a separate enum/reference table.

Suggested model:

```text
waste_type_id
code
display_name
hazard_class
routing_rule
active
```

Certain types may trigger special handling:

```text
Biomedical → higher severity / special department
E-waste → specialized disposal pathway
Construction debris → construction-waste authority/rule
```

---

# 40. Anonymous Reporting Message

The screenshots repeatedly reassure:

```text
All reports are anonymous
```

This communicates low-friction participation.

## CivicQuest adaptation

CivicQuest is guest-first, but the exact word **anonymous** should be used carefully if the backend stores session, IP/security metadata, or later account linkage.

Safer UI options:

```text
Your public identity is not shown on this report.
```

or

```text
Reports can be submitted without showing your name publicly.
```

If CivicQuest truly implements anonymous reporting, document precisely what that means in the privacy policy.

---

# 41. Community Confirmation: "I've Seen This"

The issue photo contains a button:

```text
👍 I've seen this
```

This is separate from generic social liking.

It means:

> Another citizen confirms this issue exists / has also observed it.

This is very valuable for CivicQuest.

## Recommended terminology

Options:

```text
I've seen this
Confirm issue
Still here
Also seen
```

## Behavior

A user should be able to confirm an existing issue instead of submitting a duplicate report.

This:

- increases community confirmation count,
- strengthens report credibility,
- reduces duplicates,
- can refresh `last_confirmed_at`,
- contributes to hotspot scoring.

## Data model

```text
report_confirmations
- report_id
- user_id / guest_user_id
- confirmed_at
- location_at_confirmation optional/private
- confirmation_type
```

Unique constraint:

```text
(report_id, user_id)
```

## Important

Confirmation is not necessarily proof.

It is a community signal.

---

# 42. Duplicate Prevention Through Existing-Report Confirmation

The `I've seen this` feature can be used in the new-report flow.

Before final submission:

```text
We found a similar issue 18m away.

[ I've seen this too ]
[ Report a different issue ]
```

If the user confirms:

- do not create a duplicate report,
- create a confirmation,
- optionally allow a fresh photo,
- update hotspot/report recency.

This should be part of CivicQuest's duplicate-reduction strategy.

---

# 43. Issue Detail: Report Metadata

One screenshot shows:

```text
Reported 45d ago · 1 citizen(s) reported · 45d unresolved
```

## CivicQuest should display

- first reported date,
- number of unique reporters / confirmations,
- age unresolved,
- latest confirmation,
- resolution date if resolved.

Example:

```text
Reported 45 days ago · Confirmed by 6 citizens · Still unresolved
```

Use natural language rather than exposing awkward pluralization such as `1 citizen(s)`.

---

# 44. File a Complaint CTA

The issue detail includes:

```text
File a complaint
```

This appears separate from merely viewing the accountability chain.

## CivicQuest interpretation

A report and an official complaint can be distinct concepts.

### CivicQuest report

Creates:
- public civic record,
- community visibility,
- hotspot/accountability analytics.

### Official complaint

Attempts to contact or submit to:
- municipal authority,
- WhatsApp,
- phone,
- email,
- official complaint portal/API.

## UX

Issue detail can provide:

```text
[ File / Escalate Complaint ]
```

Then show available channels.

If there is no official API integration, CivicQuest should be transparent:

```text
Open official WhatsApp
Call helpline
Email department
Open official complaint portal
```

Do not claim an official ticket was created unless confirmation is received.

---

# 45. Persistent Verify Cleanup / Flag Incorrect Actions

The screenshots keep two large buttons fixed at the bottom of the issue detail:

```text
✓ Verify Cleanup
⚑ Flag as Incorrect
```

This is excellent because the two most important community correction actions remain visible even while scrolling through the accountability chain.

## CivicQuest adaptation

For an unresolved Place issue:

```text
[ ✓ Verify Resolution ]   [ ⚑ Report Incorrect ]
```

or category-specific:

```text
[ ✓ Verify Cleanup ]      [ ⚑ Flag Incorrect ]
```

### Sticky behavior

- fixed to bottom of mobile sheet,
- account for safe-area inset,
- content behind it needs bottom padding,
- maintain buttons while user scrolls accountability hierarchy.

---

# 46. Issue Image + Confirmation CTA

The detail screen prominently displays the report image near the top.

The `I've seen this` action overlays or sits beside the image.

## CivicQuest image block

Include:

- main public-safe photo,
- photo timestamp if useful,
- confirmation action,
- optional photo count,
- before/after state if resolved.

Example:

```text
[ issue photo ]

             [ 👍 I've seen this ]
```

A strong image immediately helps users decide whether the report matches what they know.

---

# 47. Resolved Map Mode

The screenshots show the same map in a `Resolved` filter.

Clusters change to green.

This lets users see positive outcomes, not only failures.

## CivicQuest requirement

Resolved issues should remain discoverable for a configurable period or via filter.

Benefits:

- demonstrates platform impact,
- provides before/after proof,
- creates positive feedback,
- supports resolution analytics.

Map legend:

```text
Red / coral  = unresolved
Green        = resolved
Gold         = under review / action underway
```

---

# 48. Civic Impact Through Resolved Issues

Do not immediately delete resolved reports from all public experiences.

Instead, consider:

```text
resolved issue
→ map visible in resolved mode
→ before/after
→ time to resolution
→ authority / community action
```

This supports CivicQuest's core narrative:

> We are not only collecting complaints. We show change.

---

# 49. Newsletter / Civic Digest

The screenshots contain an optional banner:

```text
Join 635 Bengalureans on the Monday digest
```

This is not core to the first reporting flow, but it suggests a useful retention feature.

## CivicQuest future feature

Weekly civic digest:

```text
Your area this week:
- 12 new reports
- 4 resolved
- 2 hotspots
- 1 cleanup event
- your +40 XP
```

Possible CTA:

```text
Get the Mumbai Civic Digest
```

This can be deferred from MVP if needed.

---

# 50. Language Toggle

The screenshot contains a Kannada language toggle.

For CivicQuest Mumbai, localization is important.

Potential Phase 1 languages:

```text
English
Marathi
Hindi
```

The architecture should be internationalization-ready even if launch starts with English.

## Implementation

Use message keys rather than hardcoded text:

```text
report.issue.title
report.severity.moderate
report.location.permission_denied
```

---

# 51. Full Report Form Validation Model

Suggested Phase 1 validation:

```text
photo                 required
location              required for verified field report
location_accuracy     must pass threshold or warn
landmark/address      required or reverse-geocoded fallback
severity              required
complaint_type        required
waste/issue_type      required where applicable
```

Submit button remains disabled until required validation passes.

## Validation UX

Do not wait until submit to reveal all errors.

Show contextual state near each missing field.

---

# 52. Proposed Garbage Report Schema

The screenshot batch implies that a single generic `category` column is insufficient.

Recommended extension:

```json
{
  "report_type": "place",
  "category": "garbage",
  "complaint_type": "garbage_public_place",
  "material_type": "mixed_waste",
  "severity": "moderate",
  "description": null,
  "location": {
    "lat": 19.0,
    "lng": 72.0,
    "accuracy_m": 14
  },
  "address": "...",
  "landmark": "...",
  "media_ids": ["..."]
}
```

---

# 53. Recommended Severity Model

Use enum:

```text
minor
moderate
severe
critical
```

But store the criteria by issue category.

Possible tables:

```text
severity_levels
category_severity_guidance
```

Example:

```text
category=garbage
severity=moderate
min_area_m2=1
max_area_m2=5
description="Noticeable heap..."
```

Do not make the measurement mandatory if users cannot estimate accurately.

The text is guidance, not a scientific measurement.

---

# 54. Anonymous / Guest Reporting + CivicQuest XP

CivicQuest has a slight difference from the reference product because we also want XP and a Civic Identity.

Recommended behavior:

### Guest
Can:
- submit reports,
- confirm issues,
- see provisional XP.

Public report does not display their identity.

### After value is earned

Prompt:

```text
You've earned 18 Civic XP.

Save your progress?
```

Account linking preserves:
- reports,
- confirmations,
- XP,
- CivicDex,
- quests.

This keeps the privacy/friction benefit while retaining our game layer.

---

# 55. End-to-End Map-to-Report Journey

```text
Open CivicQuest
      ↓
Map loads
      ↓
See unresolved clusters
      ↓
Filter / inspect nearby area
      ↓
Tap + Report Issue
      ↓
Report bottom sheet opens
      ↓
Request camera permission when user chooses Take Photo
      ↓
Capture photo
      ↓
Check location
      ↓
If location denied:
    show recovery instructions
      ↓
Reverse geocode + user adds landmark
      ↓
Select severity using human-readable guidance
      ↓
Select complaint type
      ↓
Select waste / issue type
      ↓
Check nearby duplicate candidates
      ↓
If existing match:
    confirm existing report
or
    continue with new report
      ↓
Submit
      ↓
Processing / moderation
      ↓
Report appears on map/feed
      ↓
User receives eligible Civic XP
```

---

# 56. End-to-End Existing-Issue Journey

```text
Tap cluster
   ↓
Zoom / choose issue
   ↓
Issue detail opens
   ↓
View photo + severity + status + address
   ↓
I've seen this
   ↓
See open duration + confirmations + issue type
   ↓
Scroll accountability chain
   ↓
File complaint / contact authority
   ↓
View MLA / MP
   ↓
Share
   ↓
Persistent bottom actions:
   ├── Verify Cleanup
   └── Flag Incorrect
```

---

# 57. Suggested Additional Components

```text
ExploreMapPage
├── DigestBanner
├── ExploreFilters
│   ├── SeverityFilter
│   ├── StatusFilter
│   └── MapListToggle
├── MapSummaryCounter
├── CivicMap
│   ├── IssueClusterMarker
│   ├── IssueMarker
│   └── MapControls
└── StickyReportCTA

ReportIssueSheet
├── PhotoCaptureField
├── LocationGate
├── LandmarkField
├── SeveritySelector
├── ComplaintTypeSelector
├── MaterialTypeSelector
├── DuplicateCandidatePanel
├── AnonymousReportingNotice
└── SubmitReportButton

IssueImageCard
├── PublicImage
└── ConfirmIssueButton

IssueStickyActions
├── VerifyResolutionButton
└── FlagIncorrectButton
```

---

# 58. Suggested Additional API Endpoints

## Explore

```http
GET /explore/clusters
GET /explore/issues
GET /explore/summary
```

Query parameters:

```text
bbox
zoom
status
severity
category
```

## Report metadata

```http
GET /categories/{categoryId}/complaint-types
GET /categories/{categoryId}/material-types
GET /categories/{categoryId}/severity-guidance
```

## Confirmation

```http
POST   /reports/{id}/confirmations
DELETE /reports/{id}/confirmations/me
GET    /reports/{id}/confirmations/summary
```

## Duplicate candidates

```http
POST /reports/duplicate-candidates
```

Input:

```json
{
  "lat": 19.0,
  "lng": 72.0,
  "category_id": "...",
  "captured_at": "..."
}
```

## Location

```http
GET /locations/reverse-geocode?lat=&lng=
GET /accountability/resolve?lat=&lng=&category=
```

---

# 59. Analytics Events Added by This Screenshot Batch

```text
explore_map_viewed
explore_list_viewed
severity_filter_changed
status_filter_changed
map_cluster_clicked
map_issue_clicked
report_cta_clicked

camera_permission_requested
camera_permission_granted
camera_permission_denied
photo_capture_started
photo_capture_completed

location_permission_requested
location_permission_granted
location_permission_denied
location_retry_clicked
location_help_opened

report_severity_selected
report_complaint_type_selected
report_material_type_selected
duplicate_candidate_shown
duplicate_confirmed_existing
new_report_continued_despite_candidate

report_confirmation_added
report_confirmation_removed

resolved_filter_viewed
digest_banner_clicked
language_changed
```

---

# 60. UX Improvements CivicQuest Should Make Over the Reference

The screenshots are useful, but CivicQuest should improve several details.

## A. Avoid zero-as-loading

Use skeletons instead of temporary `0` metrics.

## B. Do not claim "anonymous" unless technically accurate

Use public-identity-safe wording.

## C. Avoid fixed city-specific complaint forms

Report form fields should depend on category.

## D. Make duplicate prevention explicit

Use the `I've seen this` concept before allowing easy duplicate submissions.

## E. Explain severity in plain language

Retain this pattern. It is strong.

## F. Keep positive outcomes visible

Resolved map mode is especially useful for CivicQuest because it supports impact/XP.

## G. Preserve context

Bottom sheets are ideal because users can close them and return to the same map state.

---

# 61. Part 2 Feature Checklist

- [ ] Main civic map
- [ ] Cluster markers with report counts
- [ ] Unresolved cluster styling
- [ ] Resolved cluster styling
- [ ] Map zoom behavior
- [ ] Map viewport data loading
- [ ] Severity filter
- [ ] Status filter
- [ ] Map/List toggle
- [ ] Aggregate active/report counters
- [ ] Sticky primary Report Issue CTA
- [ ] Report creation bottom sheet
- [ ] Required photo field
- [ ] Browser camera permission flow
- [ ] Camera denied recovery
- [ ] Required GPS/location
- [ ] Location permission error state
- [ ] Retry location
- [ ] iPhone/Android/browser help instructions
- [ ] Reverse-geocoded address
- [ ] Landmark field
- [ ] Severity selector
- [ ] Severity guidance descriptions
- [ ] Complaint type selector
- [ ] Waste/material type selector
- [ ] Anonymous/public-identity notice
- [ ] `I've seen this` confirmation
- [ ] Confirmation count
- [ ] Duplicate prevention using confirmation
- [ ] Report metadata line
- [ ] File/escalate complaint CTA
- [ ] Persistent Verify Cleanup action
- [ ] Persistent Flag Incorrect action
- [ ] Resolved map filter
- [ ] Resolved issues remain visible
- [ ] Weekly civic digest concept
- [ ] Localization architecture
- [ ] Filter-aware analytics
- [ ] Responsive mobile bottom sheets
- [ ] Desktop drawer/modal adaptation

---

## Status

**Part 2 captured from the second screenshot batch.**

The next screenshot batch should continue from Section 62.

---

# CivicQuest Reference UX Specification — Part 3
## Ward Drill-Down, Leaderboards, Volunteer Communities, Severity Menus, List Mode & Area Analytics

**Purpose:**  
This section extends Parts 1 and 2 using the third screenshot batch. It focuses on the **ward-level exploration layer**, **severity filtering UI**, **ward leaderboard / analytics**, **volunteer community discovery**, **ward list mode**, and **map drill-down behavior**.

As before, the goal is to capture the interaction pattern and data model for CivicQuest without copying the reference product's branding or exact visual design.

---

# 62. Ward / Area Drill-Down From the Map

One screenshot shows the map zoomed into a smaller area with a contextual card such as:

```text
Jaya Chamarajendra Nag...
North #49 · Yelahanka
Hebbal
24 reports
```

This suggests an intermediate layer between:

```text
city-wide cluster
```

and:

```text
individual report
```

## CivicQuest requirement

When the user taps a ward, zone, cluster, or area boundary, show a compact **Area Summary Card**.

Recommended content:

- Ward / locality name
- Zone / administrative region
- Ward number
- Parent assembly constituency if useful
- Total reports
- Active unresolved count
- Resolution rate
- Optional representative name
- Optional hotspot count

### Example

```text
Dadar West
G/North Ward · Mumbai

38 active
72 total reports
47% resolved
```

## Interaction

```text
tap area / cluster
      ↓
highlight geographic area
      ↓
show Area Summary Card
      ↓
actions:
- View ward details
- Zoom into reports
- Open list
```

---

# 63. Area Boundary Highlighting

The screenshots show a tinted map with visible administrative boundaries.

CivicQuest should support optional ward / constituency boundary overlays.

## Use cases

- show which ward a report belongs to,
- let users understand responsibility geography,
- power ward analytics,
- give context to representative profiles,
- allow ward-level filtering.

## Recommended implementation

Boundary polygons should come from PostGIS and be rendered on the map.

Possible endpoint:

```http
GET /administrative-areas
    ?bbox=
    &type=ward
```

or preload simplified ward boundaries for the city.

## Performance

Use simplified polygons at low zoom.

Do not send full-resolution geometry unnecessarily.

---

# 64. Individual Map Marker Severity Styling

The close-up map screenshot shows individual markers in several warm colors.

This appears to represent severity or issue state.

The screenshots do not fully prove the exact color-to-severity mapping, so CivicQuest should define its own explicit legend.

Recommended:

```text
Minor      = pale yellow
Moderate   = orange
Severe     = coral/red
Critical   = dark red
Resolved   = green
Under review = gold or neutral
```

## Requirement

Every color used on the map should also have:

- a text label,
- accessible contrast,
- non-color differentiation where possible.

Do not rely on color alone for accessibility.

---

# 65. Severity Filter Dropdown

The screenshots show an expanded severity menu:

```text
All Severity
Minor
Moderate
Severe
Critical
```

## Behavior

- single-select,
- active choice reflected in filter button,
- map/list refresh immediately,
- selected value persisted when switching Map/List,
- analytics counters update.

Suggested URL state:

```text
?severity=severe
```

## Mobile UX

Use a compact dropdown/popover if space allows.

If more filters are added later, move to a filter bottom sheet.

---

# 66. All Status Filter

The screenshots show:

```text
All Status
```

as a status filter, in addition to resolved/unresolved states from the previous batch.

## CivicQuest options

Phase 1:

```text
All Status
Unresolved
Resolved
Under Review
```

Later:

```text
Acknowledged
In Progress
Disputed
Removed
```

Keep user-facing labels simpler than internal workflow states.

---

# 67. Ward Leaderboard / Civic Accountability Ranking

A dedicated screen ranks wards by unresolved reports.

Header:

```text
Ward Leaderboard
Wards ranked by unresolved reports
```

## CivicQuest value

This converts individual reports into a **city-level accountability view**.

It lets citizens answer:

> Which wards currently have the largest unresolved civic burden?

## Summary KPI cards

Observed:

```text
7,578 Unresolved
279 Resolved
3.6% Rate
```

CivicQuest should support:

- total unresolved,
- total resolved,
- resolution rate,
- optional median/average resolution time.

### Resolution rate

Recommended formula:

```text
resolved / (resolved + unresolved)
```

Use a clear tooltip explaining the denominator.

---

# 68. Ward Ranking Rows

Observed ranking structure:

```text
1  Sunkenahalli    Central #42      140
   141 reports · 1% resolved

2  Kasavanahalli   South #31        112
   115 reports · 3% resolved
```

Each row includes:

- rank,
- ward/locality,
- zone,
- ward number,
- unresolved count,
- total report count,
- resolution percentage,
- progress bar / relative magnitude.

## CivicQuest recommended fields

```text
ward_id
ward_name
zone_name
ward_number
active_count
total_reports
resolved_count
resolution_rate
average_open_days
hotspot_count
rank
```

## Ranking modes

V1:

```text
Most unresolved
```

Later:

```text
Slowest resolution
Lowest resolution rate
Most severe reports
Most improved
```

Avoid labeling a ward as "worst" without clearly stating the metric.

Better CivicQuest language:

```text
Highest unresolved count
```

---

# 69. Analytics Deep Link

The leaderboard has:

```text
See more data on Analytics
```

## CivicQuest future analytics page

Potential views:

- city totals,
- ward trends,
- category trends,
- resolution times,
- hotspot trends,
- authority performance,
- Civic Action impact.

Phase 1 can link to a simple analytics page rather than building a full BI system.

---

# 70. Ward List Mode

The screenshots show a full `List` view with rows such as:

```text
141  Sunkenahalli  Central #42
     140 unresolved · Uday B. Garudachar

131  Panathur  East #48
     111 unresolved · Manjula S.
```

This is different from a list of individual reports.

It is a **ward summary list**.

## CivicQuest requirement

Depending on zoom/filter context, List Mode can show:

### City level
Ward / locality summaries.

### Ward level
Individual reports within that ward.

The UI should make the list scope explicit.

Example title:

```text
Mumbai Wards
```

or:

```text
Reports in G/North Ward
```

---

# 71. Ward List Row

Recommended row:

```text
[141]

Sunkenahalli
Central · Ward #42
140 unresolved · 1% resolved

                         >
```

CivicQuest row can include:

- total reports badge,
- ward name,
- zone,
- ward number,
- unresolved count,
- resolution rate,
- representative / ward officer optionally,
- chevron.

## Tap behavior

```text
tap ward row
   ↓
Ward Detail Page / Sheet
```

Possible detail:

- ward metrics,
- map,
- active reports,
- hotspots,
- responsible authority,
- representatives,
- recent resolutions.

---

# 72. Ward Representative / Official Label in List

The screenshot includes a person name after the unresolved count.

This appears to be a representative / official associated with the ward.

For CivicQuest:

- only show role/person when the data source is authoritative and current,
- label the role clearly,
- store effective dates.

Instead of:

```text
140 unresolved · Person Name
```

prefer:

```text
140 unresolved · MLA: Person Name
```

or:

```text
Ward officer: Person Name
```

so users know the relationship.

---

# 73. Bottom Navigation / Utility Tabs

The screenshots show small bottom controls near the primary Report CTA:

- a people/community icon,
- an analytics/leaderboard icon.

This implies lightweight secondary navigation.

## CivicQuest Phase 1 recommendation

Possible bottom utility destinations:

```text
Community / Civic Actions
Leaderboard / Impact
```

while the main CTA remains:

```text
+ Report Issue
```

If CivicQuest already uses full navigation elsewhere, do not add duplicate navigation simply to mimic the reference.

The core principle is:

> Keep reporting primary; keep impact/community one tap away.

---

# 74. Volunteer Communities Directory

One screenshot opens:

```text
Volunteer Communities
3 communities cleaning up Bengaluru
```

This is highly relevant to CivicQuest's **Civic Actions** pillar.

## CivicQuest feature

Create a directory of:

- NGOs,
- volunteer cleanup groups,
- resident groups,
- civic communities,
- plogging groups,
- local environmental organizations.

## Community card fields

Observed:

- logo,
- community name,
- coverage area,
- short description,
- external contact/social links.

Example:

```text
Team Social Spotlight
Works across Bengaluru

We plant native trees...

[ WhatsApp ] [ Instagram ]
```

## CivicQuest data model

```text
community_id
name
logo_url
description
coverage_type
coverage_area_ids
city
verification_status
website_url
whatsapp_url
instagram_url
x_url
facebook_url
contact_email
active
created_at
```

---

# 75. Community Social / Contact Chips

The screenshots show compact chips for:

- WhatsApp,
- Instagram,
- X,
- possibly Facebook / more.

## Behavior

Tapping opens the external destination.

Log:

```text
community_whatsapp_clicked
community_instagram_clicked
community_external_link_clicked
```

Do not imply partnership unless the organization is verified / onboarded.

---

# 76. Community Verification

CivicQuest should distinguish:

```text
Community listed
```

from:

```text
Verified CivicQuest community
```

Recommended states:

```text
submitted
under_review
verified
rejected
inactive
```

Verified community cards may show a badge.

---

# 77. Register Your Community

The screenshot includes:

```text
+ Register your community
```

## CivicQuest flow

Allow a community organizer to submit:

- organization/community name,
- logo,
- description,
- coverage area,
- website/social links,
- contact person,
- contact email/phone,
- proof of organization where appropriate.

Submission enters review.

## API

```http
POST /communities/applications
```

Do not automatically publish user-submitted community records.

---

# 78. Civic Actions Connection

The directory should not remain only a contact list.

Longer term, each community can publish Civic Actions:

```text
Community
   ↓
Upcoming cleanup
   ↓
Join
   ↓
Check in
   ↓
Before/after proof
   ↓
Civic XP
```

This connects the reference community directory with CivicQuest's existing gamified Civic Action system.

---

# 79. City-Wide Community Directory

Recommended filters:

```text
Nearby
Cleanup
Plogging
Tree planting
Waste segregation
Beach cleanup
Ward-based
```

Phase 1 can simply show verified Mumbai communities without complex filtering.

---

# 80. Header Localization Control

The screenshots show a language button and a contextual tooltip indicating switching languages.

## CivicQuest

Language switch should:

- be obvious,
- not require logout,
- persist preference,
- update all navigation/forms,
- update server-rendered public content where translations exist.

Suggested Phase 1:

```text
EN
मराठी
हिंदी
```

## Tooltip

Example:

```text
View in Marathi
```

Do not use a tooltip as the only way to understand the button.

---

# 81. External Social Channel Icons

The screenshots show varying social icons in the header across captures.

This suggests direct links to project/community channels.

For CivicQuest, header-level social icons are optional and should not distract from the core flow.

Possible use:

- Instagram
- X
- Telegram/WhatsApp community

Recommendation:

Keep them in a menu/footer unless a community channel is central to the pilot.

---

# 82. Map Area Card vs Issue Detail

The screenshots show two separate levels of map interaction:

### Area card
Example:

```text
Ward / locality
24 reports
```

### Issue detail
Example:

```text
specific garbage report
photo
severity
accountability
```

CivicQuest must preserve this distinction.

Recommended drill-down:

```text
City
  ↓
Cluster
  ↓
Ward/Area summary
  ↓
Individual report
```

This prevents users from being overwhelmed by thousands of individual pins.

---

# 83. Map Drill-Down State Machine

Suggested map state:

```text
CITY_OVERVIEW
    ↓ tap cluster
AREA_OVERVIEW
    ↓ tap ward/card
WARD_DETAIL
    ↓ tap report
REPORT_DETAIL
```

Back/close should restore the prior:

- map center,
- zoom,
- filters,
- selected area.

Do not reset the user to the city-wide map every time a sheet is closed.

---

# 84. Area Summary API

Suggested endpoint:

```http
GET /administrative-areas/{areaId}/summary
```

Response:

```json
{
  "area": {
    "id": "...",
    "name": "G/North Ward",
    "type": "ward",
    "zone": "...",
    "ward_number": "..."
  },
  "metrics": {
    "active": 38,
    "resolved": 21,
    "total": 59,
    "resolution_rate": 0.356,
    "average_open_days": 17
  },
  "representatives": [],
  "hotspot_count": 4
}
```

---

# 85. Ward Leaderboard API

Suggested:

```http
GET /analytics/wards
    ?city=mumbai
    &sort=active_desc
    &limit=50
```

Response row:

```json
{
  "ward_id": "...",
  "rank": 1,
  "ward_name": "G/North",
  "zone_name": "...",
  "ward_number": "...",
  "active_count": 140,
  "total_reports": 141,
  "resolved_count": 1,
  "resolution_rate": 0.01
}
```

---

# 86. Communities API

```http
GET /communities
GET /communities/{id}
POST /communities/applications
GET /communities/{id}/civic-actions
```

Filters:

```text
city
area_id
verified
activity_type
```

---

# 87. Added Analytics Events

```text
area_marker_clicked
area_summary_opened
area_detail_opened

severity_dropdown_opened
severity_filter_selected
status_dropdown_opened
status_filter_selected

ward_leaderboard_viewed
ward_rank_clicked
analytics_link_clicked

community_directory_viewed
community_card_clicked
community_whatsapp_clicked
community_instagram_clicked
community_registration_started
community_registration_submitted

language_menu_opened
language_selected
```

---

# 88. CivicQuest Design Recommendations From This Batch

## A. Keep the map hierarchy scalable

Do not render every report as a pin at city scale.

Use:

```text
clusters → wards → reports
```

## B. Make accountability comparative, not only individual

The ward leaderboard is useful because users can compare areas.

CivicQuest should eventually answer:

```text
Which ward has the most unresolved problems?
Which ward resolves fastest?
Which areas are improving?
```

## C. Include positive rankings later

A leaderboard based only on unresolved problems can feel punitive.

Add future views such as:

```text
Most improved wards
Highest resolution rate
Fastest median resolution
Most Civic Actions completed
```

## D. Connect communities to action

A volunteer-community directory becomes much more valuable when every group can have:

```text
profile → upcoming actions → join → proof → XP
```

## E. Keep administrative labels explicit

Whenever a person or political representative is shown, explain the role.

Avoid implying responsibility merely through proximity in the UI.

---

# 89. Part 3 Feature Checklist

- [ ] Ward / area summary card
- [ ] Ward polygons / boundaries
- [ ] Area highlight on map
- [ ] City → cluster → ward → report drill-down
- [ ] Preserve map state when closing sheets
- [ ] Severity-coded individual markers
- [ ] Accessible marker legend
- [ ] Severity dropdown
- [ ] All Status dropdown
- [ ] Ward leaderboard
- [ ] Unresolved KPI
- [ ] Resolved KPI
- [ ] Resolution-rate KPI
- [ ] Ward ranking rows
- [ ] Relative progress bars
- [ ] Ward rank metric label
- [ ] Analytics deep link
- [ ] Ward list mode
- [ ] Ward detail navigation
- [ ] Explicit official/representative role labels
- [ ] Community directory
- [ ] Community cards
- [ ] Coverage-area metadata
- [ ] WhatsApp/social contact chips
- [ ] Community verification state
- [ ] Register community flow
- [ ] Community application moderation
- [ ] Community → Civic Action linkage
- [ ] Language switcher
- [ ] Localized copy architecture
- [ ] Area summary API
- [ ] Ward analytics API
- [ ] Community API

---

## Status

**Part 3 captured from the third screenshot batch.**

The next screenshot batch should continue from Section 90.

---

# CivicQuest Reference UX Specification — Part 3
## Severity Menus, Map Drill-Down, Ward Leaderboards, List View, Volunteer Communities & Civic Analytics

**Purpose:**  
This section extends the CivicQuest reference specification using the third screenshot batch. It focuses on **map drill-down behavior**, **severity filter menus**, **ward-level summary cards**, **ward leaderboard / analytics**, **volunteer community discovery**, and **list-mode ward browsing**.

The goal is to preserve the product behavior and information architecture while adapting it to CivicQuest's Mumbai-first, web/PWA-first architecture.

---

# 62. Explicit Severity Filter Menu

The screenshots show the severity filter expanding into a simple dropdown menu.

Observed options:

```text
All Severity
Minor
Moderate
Severe
Critical
```

## CivicQuest requirement

The severity filter should be a reusable dropdown / popover with:

- current selection,
- accessible keyboard navigation,
- single-selection behavior,
- outside-click dismissal,
- active state,
- mobile-friendly touch targets.

### State model

```text
all
minor
moderate
severe
critical
```

### Example

```text
[ All Severity ▼ ]

All Severity
Minor
Moderate
Severe
Critical
```

The selected severity immediately refreshes:

- map markers/clusters,
- list view,
- summary counters,
- ward ranking where applicable.

---

# 63. Status Filter

The same filter row supports:

```text
All Status
Unresolved
Resolved
```

CivicQuest should support at minimum:

```text
All Status
Unresolved
Resolved
```

Possible later states:

```text
Under Review
Acknowledged
In Progress
Disputed
```

The map/list state must stay synchronized.

---

# 64. Language Switch Interaction

The screenshot shows a language button with a tooltip / helper state.

For CivicQuest Mumbai:

Potential launch languages:

```text
English
Marathi
Hindi
```

## UX behavior

When the user taps the language control:

- show currently active language,
- expose available languages,
- optionally show a tooltip such as:
  - `View in Marathi`
  - `View in Hindi`

Do not make language switching reload the entire app unnecessarily.

Persist preference:

```text
local preference
or
account profile preference
```

---

# 65. Map Drill-Down from Cluster to Local Area

One screenshot shows the map zoomed in from large clusters to individual colored markers.

At this level, tapping an area produces a small **ward/locality summary popup**.

Observed content:

```text
Jaya Chamarajendra Nag...
North #49 · Yelahanka
Hebbal
24 reports
```

## CivicQuest behavior

At medium zoom:

- display individual issue markers or smaller clusters,
- tapping a marker/area can open a compact summary card,
- summary should give enough context before opening a full report/ward page.

## Suggested popup fields

```text
ward_name
zone_name
ward_number
assembly_constituency
active_report_count
```

Example CivicQuest Mumbai:

```text
Dadar West
G/North Ward
Mahim Assembly Constituency
24 active reports
```

## Interaction

```text
Tap cluster
  ↓
Zoom in
  ↓
Tap local marker / ward area
  ↓
Compact ward summary
  ↓
Tap summary
  ↓
Ward analytics / report list
```

---

# 66. Marker Color Semantics at Detailed Zoom

The screenshot shows multiple colored point markers, including dark red, orange, and bright red.

This implies severity-sensitive marker colors.

## CivicQuest recommendation

Map individual reports using severity color:

```text
Minor     = pale yellow
Moderate  = orange
Severe    = coral / red
Critical  = dark red
Resolved  = green
```

Keep the map legend accessible somewhere in the experience.

Do not use color alone; marker shape/border or accessible labels should also convey state.

---

# 67. Ward Leaderboard / Civic Analytics Screen

The screenshots include a dedicated **Ward Leaderboard** page.

Observed top metrics:

```text
7,578 Unresolved
279 Resolved
3.6% Rate
```

Then:

```text
Worst Wards by Unresolved Reports
```

This is a major CivicQuest feature.

## CivicQuest purpose

The leaderboard converts individual reports into area-level public accountability.

Users can quickly understand:

- how many issues remain unresolved,
- how many were resolved,
- approximate resolution rate,
- which wards are struggling most.

## KPI cards

Recommended:

```text
Unresolved
Resolved
Resolution Rate
```

Optional future:

```text
Median Days Open
Hotspots
Reports This Month
```

---

# 68. Resolution Rate

The screenshot shows:

```text
3.6% RATE
```

CivicQuest should define this transparently.

Recommended formula:

```text
resolution_rate =
resolved_reports
/
(resolved_reports + unresolved_reports)
```

Use a clearly documented time window if not lifetime.

Example:

```text
Resolution rate · Last 90 days
```

Avoid ambiguous metrics.

---

# 69. Worst Wards Ranking

The screenshot ranks wards by unresolved report count.

Observed row fields:

```text
Rank
Ward name
Zone
Ward number
Unresolved count
Total reports
Percent resolved
Progress bar
```

Example:

```text
1 Sunkenahalli  Central #42        140
  141 reports · 1% resolved
```

## CivicQuest row model

```json
{
  "rank": 1,
  "ward_id": "...",
  "ward_name": "Sunkenahalli",
  "zone_name": "Central",
  "ward_number": 42,
  "unresolved_count": 140,
  "total_reports": 141,
  "resolution_rate": 0.01
}
```

## Interaction

Tapping a ward row should open:

- ward detail,
- map focused on ward,
- ward report list,
- responsible authority / ward office,
- elected representatives,
- recent reports,
- resolution performance.

---

# 70. Ranking Bar Visualization

Rows include a horizontal bar indicating unresolved burden.

CivicQuest can calculate:

```text
bar_width =
ward_unresolved
/
max_unresolved_among_visible_wards
```

Use bars for comparative visualization only.

Do not imply absolute performance solely by bar color.

---

# 71. Analytics Deep Link

The leaderboard screenshot includes:

```text
See more data on Analytics
```

## CivicQuest future analytics page

Possible sections:

- report trends over time,
- resolution trends,
- severity mix,
- category mix,
- ward comparisons,
- average age of unresolved issues,
- top hotspots,
- authority response metrics,
- Civic Action impact.

Phase 1 can keep this lightweight.

---

# 72. Map/List Bottom Navigation State

The screenshots show a bottom control area with:

- a community/people icon,
- an analytics/leaderboard icon,
- report count indicator,
- primary `Report Garbage` CTA.

## CivicQuest interpretation

A compact mobile bottom utility bar could contain:

```text
Explore
Community
Impact / Leaderboard
+ Report Issue
```

But avoid overloading the bar.

Recommended Phase 1:

```text
Explore
Impact
+ Report Issue
```

and keep Community accessible from a secondary surface if needed.

---

# 73. List View as Ward-Level Browsing

The screenshot's `List` mode is not simply a list of individual garbage reports.

It shows **ward-level rows**.

Observed fields:

```text
141
Sunkenahalli Central #42
140 unresolved · Uday B. Garudachar
```

and similar rows.

This suggests list mode can act as a **ward summary list** at the current map scale.

## CivicQuest requirement

List behavior can be context-sensitive.

At city zoom:

```text
List = ward summaries
```

At neighborhood zoom:

```text
List = individual reports
```

This is a strong design pattern.

---

# 74. Ward List Row

Recommended fields:

- total reports or report score,
- ward name,
- zone,
- ward number,
- unresolved count,
- elected representative / responsible ward official if available,
- expand chevron.

Example:

```text
141

Sunkenahalli
Central · Ward #42

140 unresolved · Ward representative
```

For CivicQuest Mumbai, use authoritative role naming and do not display a person if the data is stale or unverified.

---

# 75. Expandable Ward Row

The chevron suggests each ward row can expand.

Recommended expanded content:

```text
Unresolved
Resolved
Average age
Top issue categories
Top hotspot
Ward authority
MLA
MP
[ View ward ]
```

If expansion becomes too dense, use the chevron to navigate to a dedicated ward page instead.

---

# 76. Volunteer Communities Directory

The screenshots show a `Volunteer Communities` bottom sheet / modal.

Observed structure:

```text
Volunteer Communities
3 communities cleaning up Bengaluru
```

Then community cards containing:

- logo,
- name,
- geographic coverage,
- description,
- social/contact buttons.

Examples of contact buttons:

```text
WhatsApp
Instagram
X
Facebook
```

## CivicQuest adaptation

This fits directly into our **Civic Actions** pillar.

The directory can contain:

- NGOs,
- cleanup groups,
- resident groups,
- plogging communities,
- environmental organizations,
- civic volunteer collectives.

---

# 77. Community Card Data Model

Recommended fields:

```text
community_id
name
logo_url
description
coverage_type
coverage_area
website_url
whatsapp_url
instagram_url
x_url
facebook_url
verification_status
active
```

Example:

```json
{
  "name": "Mumbai Ploggers",
  "coverage_type": "citywide",
  "coverage_area": "Mumbai",
  "description": "Community cleanup and plogging group.",
  "verification_status": "verified"
}
```

---

# 78. Community Social / Contact Links

Each card can expose only the channels actually available.

Examples:

```text
WhatsApp
Instagram
X
Facebook
Website
Email
```

These should open externally.

Track clicks as analytics events, but do not imply an organization responded unless CivicQuest receives confirmation.

---

# 79. Register Your Community

The screenshot includes:

```text
+ Register your community
```

## CivicQuest flow

This can allow organizers to submit:

```text
Community name
Logo
Description
Operating area
Contact person
Email
Website
Social links
Typical activities
Proof / verification links
```

Submission state:

```text
draft
submitted
under_review
verified
rejected
```

Do not publish unverified organizations automatically.

---

# 80. Community Verification

CivicQuest should show status:

```text
Verified Community
Community-submitted
Pending verification
```

Verification can include:

- official website,
- social presence,
- organizer identity,
- prior cleanup history,
- manual review.

This matters if the community will later host Civic Actions and award participation verification.

---

# 81. Volunteer Communities vs Civic Actions

These are related but distinct.

## Community

Persistent organization/profile:

```text
Mumbai Ploggers
```

## Civic Action

Specific event:

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

Do not model every event as a separate "community."

---

# 82. Community Directory Entry Points

Possible entry points:

- bottom navigation community icon,
- Civic Actions section,
- hotspot page,
- ward page,
- NGO event page.

Example:

```text
Nearby communities helping in this area
```

This creates a positive-action bridge from problem discovery to participation.

---

# 83. Social Platform Icon Variants

Different screenshots show top-right social icons that appear to vary.

This should not become hardcoded app behavior.

For CivicQuest, top-level external social links should be configurable and low priority.

Possible product uses:

- CivicQuest Instagram
- X
- Telegram/WhatsApp community
- newsletter

Keep them in settings/about/footer rather than competing with core map actions.

---

# 84. Resolved Mode Reinforces Impact

The screenshot batch again shows a green-cluster `Resolved` map.

This confirms that resolved issues are a first-class browse mode.

CivicQuest should preserve:

```text
unresolved map
resolved map
```

This is critical for trust because users can see that issues do not simply disappear.

---

# 85. City-Level All-Status Map

The screenshot shows:

```text
All Severity
All Status
```

with:

```text
7,578 Active
7,857 Reports
```

This suggests:

```text
total reports = active + resolved
```

or similar.

## CivicQuest map modes

Recommended:

### All Status

Shows:
- unresolved,
- resolved,
- under review.

### Unresolved

Focus:
- current civic problems.

### Resolved

Focus:
- impact / success.

The visual distinction should remain clear.

---

# 86. CivicQuest Ward-Level Data Model

To support leaderboard + map drill-down + list mode, each ward needs derived metrics.

Example:

```json
{
  "ward_id": "...",
  "name": "G/North",
  "number": "...",
  "zone": "...",
  "boundary": "...",
  "active_report_count": 140,
  "resolved_report_count": 32,
  "total_report_count": 172,
  "resolution_rate": 0.186,
  "average_open_days": 67,
  "critical_count": 8,
  "hotspot_count": 5,
  "top_category": "garbage",
  "updated_at": "..."
}
```

These metrics may be computed:

- live for small scale,
- via materialized view / periodic aggregation as usage grows.

---

# 87. Suggested Ward APIs

```http
GET /wards
GET /wards/{wardId}
GET /wards/{wardId}/metrics
GET /wards/{wardId}/reports
GET /wards/{wardId}/hotspots
GET /wards/{wardId}/accountability
GET /wards/leaderboard
```

Leaderboard example:

```http
GET /wards/leaderboard
    ?metric=unresolved
    &sort=desc
    &limit=50
```

---

# 88. Suggested Community APIs

```http
GET  /communities
GET  /communities/{id}
POST /communities/applications
GET  /communities/{id}/civic-actions
```

Admin:

```http
GET  /admin/community-applications
POST /admin/community-applications/{id}/approve
POST /admin/community-applications/{id}/reject
```

---

# 89. Map Drill-Down API Strategy

At low zoom:

```http
GET /explore/clusters
```

At medium zoom:

```http
GET /explore/ward-summaries
```

At high zoom:

```http
GET /explore/issues
```

This prevents the browser from downloading thousands of report points unnecessarily.

---

# 90. Recommended Explore Rendering Levels

Example:

```text
Zoom 8–10
→ city/zone clusters

Zoom 11–13
→ ward clusters / ward summaries

Zoom 14–16
→ smaller clusters / hotspots

Zoom 17+
→ individual issue markers
```

Exact levels depend on the map provider and density.

---

# 91. Ward Leaderboard vs User Leaderboard

CivicQuest already has a planned **user XP leaderboard**.

This screenshot introduces a different concept:

## User leaderboard

Ranks:

```text
Citizens by Civic XP / verified impact
```

## Ward leaderboard

Ranks:

```text
Areas by unresolved civic burden / resolution performance
```

These must remain separate.

Naming recommendation:

```text
Civic Leaders
```

for users, and:

```text
Ward Accountability
```

or:

```text
Ward Performance
```

for geographic analytics.

Avoid confusing "leaderboard" with a positive score when showing worst-performing wards.

---

# 92. Avoid Gamifying Poor Civic Performance

If CivicQuest ranks wards by unresolved issues, do not make it feel celebratory.

Use language like:

```text
Highest unresolved burden
Needs attention
Lowest resolution rate
```

rather than:

```text
Top ward
Winner
#1
```

The ranking is accountability analytics, not a competition to have more garbage.

---

# 93. Volunteer Communities + CivicQuest Rewards

Volunteer communities can become a bridge into the XP system.

Example:

```text
User discovers community
   ↓
Views upcoming Civic Action
   ↓
Joins cleanup
   ↓
GPS check-in
   ↓
Participation verified
   ↓
Civic XP awarded
```

Organizations should never directly set arbitrary XP amounts.

The server owns reward rules.

---

# 94. Volunteer Community Moderation

Because this directory could be abused for spam or impersonation:

- verify submitted groups,
- moderate logos/descriptions,
- validate URLs,
- block unsafe external links,
- keep a report-community feature,
- store approval history.

---

# 95. Analytics Events Added by Part 3

```text
severity_filter_menu_opened
severity_filter_selected
status_filter_selected
language_menu_opened
language_selected

map_cluster_drilled_down
ward_summary_opened
ward_summary_clicked

ward_leaderboard_viewed
ward_leaderboard_row_clicked
analytics_link_clicked

explore_list_viewed_city_scope
ward_row_expanded
ward_detail_opened

community_directory_opened
community_card_clicked
community_whatsapp_clicked
community_instagram_clicked
community_x_clicked
community_facebook_clicked
community_registration_started
community_registration_submitted

resolved_map_viewed
all_status_map_viewed
```

---

# 96. Suggested Additional Components

```text
SeverityFilterMenu
StatusFilterMenu
LanguageMenu

WardSummaryPopup
WardLeaderboardPage
├── CityMetricCards
├── ResolutionRateCard
├── WardRankingList
└── WardRankingRow

WardListView
├── WardListRow
└── WardExpandedSummary

VolunteerCommunitiesSheet
├── CommunityCard
├── CommunityContactLinks
└── RegisterCommunityButton

CommunityRegistrationForm
```

---

# 97. User Journey: City → Ward → Issue

```text
Open Explore
    ↓
See city-level clusters
    ↓
Tap cluster
    ↓
Map zooms / loads ward-level detail
    ↓
Tap ward/locality marker
    ↓
See compact ward summary
    ↓
Open ward
    ↓
See ward metrics + report list + accountability
    ↓
Open specific issue
```

---

# 98. User Journey: Accountability Analytics

```text
Open Impact / Ward Accountability
    ↓
See unresolved / resolved / rate
    ↓
See highest unresolved wards
    ↓
Tap ward
    ↓
View ward report burden
    ↓
See responsible authority
    ↓
Inspect recent reports / hotspots
```

---

# 99. User Journey: Volunteer Discovery

```text
Open Community / Civic Actions
    ↓
Volunteer Communities
    ↓
Browse organizations
    ↓
Open contact/social channel
or
    ↓
View their upcoming Civic Actions
    ↓
Join event
```

---

# 100. Copilot Implementation Rules Added by Part 3

1. Keep severity and status filter state shared across map/list modes.
2. Render different geographic aggregation levels based on zoom.
3. Do not send every report point to the browser at city zoom.
4. Treat ward leaderboard metrics as derived analytics.
5. Clearly define resolution-rate formulas.
6. Keep ward accountability ranking separate from user XP ranking.
7. Do not gamify civic failure with celebratory language.
8. Community organizations require verification before public publication.
9. Social/contact links must be data-driven.
10. Every ward/representative field must include source/freshness metadata.
11. Use accessible non-color cues for severity/status.
12. Keep resolved reports available as an impact view.
13. Preserve user's filter/map position when moving into a ward and back.
14. Support city → ward → issue drill-down without page-state loss.
15. Keep volunteer organizations separate from event objects.

---

# 101. Part 3 Feature Checklist

- [ ] Severity dropdown popover
- [ ] Status dropdown
- [ ] Language switcher
- [ ] Map zoom drill-down
- [ ] Ward/locality summary popup
- [ ] Severity-colored individual markers
- [ ] Accessible marker labels
- [ ] Ward leaderboard
- [ ] Unresolved KPI
- [ ] Resolved KPI
- [ ] Resolution-rate KPI
- [ ] Worst/highest-unresolved ward ranking
- [ ] Ward comparison bars
- [ ] Analytics deep link
- [ ] Ward-level list view
- [ ] Expandable ward row / ward-detail navigation
- [ ] City-scale list vs neighborhood-scale list behavior
- [ ] Volunteer communities directory
- [ ] Community logo/name/description
- [ ] Geographic coverage
- [ ] WhatsApp link
- [ ] Instagram link
- [ ] X link
- [ ] Facebook/website support
- [ ] Register community CTA
- [ ] Community application workflow
- [ ] Community verification state
- [ ] Community moderation
- [ ] Community → Civic Action relationship
- [ ] All-status map
- [ ] Resolved map
- [ ] Ward metrics model
- [ ] Ward leaderboard API
- [ ] Community directory API
- [ ] Zoom-aware map APIs
- [ ] Separate user leaderboard vs ward accountability ranking

---

## Status

**Part 3 captured from the third screenshot batch.**

Future screenshots should continue from Section 102.
