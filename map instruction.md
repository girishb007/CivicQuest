# Build Instructions — Accountability Feature (CivicQuest)

**Audience:** coding agent / copilot working in this repo.
**Scope:** the map → report → accountability chain (ward → officer chain → elected reps), backed by real government data.

Read this whole file before writing code. It replaces guessing with confirmed sources and confirmed UX — every API and every screen behavior below was verified against a live reference app, not assumed.

---

## 0. Before you write any code: study the reference screenshots

Reference screenshots live at:

```
/Users/girishbisane/Desktop/CivicQuest/screenshots
```

Go through every image in that folder in order. They capture the exact **map-click → report populates → accountability tree → contact panel** journey we are cloning. For each screenshot, extract:

1. What UI state it shows (map, report sheet, a specific tapped panel, a modal)
2. Every piece of text verbatim (labels, chip text, button text, helper copy)
3. Every interactive element and where tapping it leads (which screenshot comes next)
4. Colors/icons used for state (severity, status, vacancy warnings)

Build a mental (or literal, in a scratch file) storyboard: `map pin tap → report sheet opens → user sees X → taps Y → panel Z opens`. The spec in §2 below describes this flow from an equivalent live app — cross-check it against what the screenshots actually show for CivicQuest's own report, since your data (ward names, rep names, corporation zones) will differ from the reference app's Bengaluru data.

Do not skip this step and build from §2 alone — the screenshots are ground truth for your product's specific copy and layout; §2 is the behavioral spec.

---

## 1. What we're building

Tapping a report pin on the map opens a **report detail sheet**. That sheet contains an **Accountability** section: a drawn hierarchy from "Your Ward" down through a static officer chain, plus the ward's elected representatives (MLA, MP) shown separately below a divider. Tapping different cards in this hierarchy does **two different things** depending on card type — this distinction is the core of the feature and must not be collapsed into one behavior:

- **Officer/utility cards** (waste utility, Commissioner, Additional Commissioner, AEE, Junior Health Inspector) → open a **contact panel**: WhatsApp deep link, mailto link, tel link to a helpline.
- **Elected representative cards** (MLA, MP) → open an **accountability analytics panel**: aggregate report stats for their whole constituency, not contact info.

This split is intentional and confirmed from a live reference implementation — do not add contact info to the MLA/MP panel, and do not add analytics to the officer panels.

---

## 2. Confirmed UX flow — map to accountability, step by step

### Step 1 — Map view
- Pins colored by severity (e.g., low → high on a 3–4 step scale), plus a distinct "resolved" color.
- Clustering at low zoom: a numbered circle marker representing N reports.
- Ward polygons rendered as a choropleth — fill opacity/intensity scales with report count in that ward.
- Hovering/tapping a ward polygon (not a pin) shows a small card: ward name, corporation + ward number, zone/division, assembly constituency, report count.
- Filter controls for severity and status; a Map/List view toggle.

### Step 2 — Tap a pin → Report detail sheet opens
Sheet contents, top to bottom:
- Severity chip + status chip (top-left), share icon + close icon (top-right)
- Ward name (large heading)
- Free-text address/location description the reporter typed
- "Get directions" link → opens native maps app to the report's coordinates
- Report photo, with an "I've seen this" / confirm-sighting control overlaid on it
- Stat tiles: also-seen count, days-open count, waste-type/category label
- **Accountability** section header, then the hierarchy (Step 3)
- Footer: "Reported Xd ago · N citizen(s) reported · Xd unresolved", a privacy note ("All reports are anonymous"), a secondary "File a complaint" action for this same location
- Two primary action buttons: **Verify Cleanup** (positive/green) and **Flag as Incorrect** (negative/red)

### Step 3 — The Accountability hierarchy (draw this exactly)

```
                     Your Ward
                  <Corp Zone> #<Ward Number>
                            |
        ┌───────────────────┴───────────────────┐
   <Waste Utility>                          Corporator
  "Reports to <parent body>"          <Vacant since DATE> OR <Name, party>
        |
   Commissioner        — <Parent body> / Corporation head · Top of chain
        |
   Additional Commissioner — <Zone>-level oversight
        |
   Asst. Executive Engineer (AEE) — Engineering oversight
        |
   Junior Health Inspector (JHI) — Frontline ward officer
──────────────────────────────────────────────────────
ELECTED REPRESENTATIVES FOR THIS WARD
 [photo] <MLA Name>              [photo] <MP Name>
         <Party> · MLA                    <Party> · MP
"Tap any card for contact options · <any relevant footnote, e.g. election status>"
```

**Corporator/ward-council seat must be modeled as nullable**, with a `seat_status: filled | vacant` and, when vacant, a `vacant_since` date rendered as a warning-styled card instead of a name. Do not hardcode "vacant" — this is real, time-sensitive civic data and must be updatable.

### Step 4a — Tap an officer/utility card → Contact panel (bottom sheet, stacks over the report sheet)

Confirmed layout:
- Small eyebrow label: tier (e.g. "FRONTLINE", "MID-TIER")
- Card title (role name) + subtitle (one-line scope description, e.g. "Ward-level SWM officer · First point of escalation")
- Close (X)
- A stack of full-width action buttons, in this style:
  - **WhatsApp <ServiceName>** — green/primary when present, opens `https://wa.me/<number>?text=<url-encoded message>`
  - **Email <Role>** — opens `mailto:<address>?subject=...&body=...`
  - **Call helpline (<number>)** — opens `tel:<number>`

The WhatsApp message must be pre-filled with: the photo reference/filename, a short instruction line ("Please arrange for cleanup at the earliest."), an attribution line ("Reported via <YourAppName> (<yourdomain>)"), and ideally the location as a Google Maps link or coordinates. Build this as a template function, not hardcoded strings, since every officer/utility card reuses the same shape with different numbers/emails.

The helpline number is a single constant across all officer cards for a given city (do not fetch/join it per-officer — it's static config).

### Step 4b — Tap the MLA or MP card → Accountability analytics panel (NOT a contact panel)

Confirmed fields:
- Representative name, role (MLA/MP), constituency name, party — as the panel header
- Four stat tiles: **Active** (unresolved reports across their whole constituency), **Reports** (total, all-time), **Avg Days** (average days unresolved), **Wards** (count of wards in their constituency)
- A list/chips of the **assembly constituencies** or **wards** covered (MPs cover many assembly constituencies; this list can be long and should lazy-load/paginate, not render all at once)
- No phone, no email, no social handle in this panel — do not add any

This is the actual "accountability" mechanism of the product: it shows the aggregate evidence against a representative's entire constituency, ranked/quantified, not just the one photo the user is looking at. Treat this as the most important panel to get right.

### Step 5 — "Flag as Incorrect" flow (confirmed, not a simple toggle)

Tapping it opens a modal:
- Title: something like **"This isn't garbage"**
- Body copy explaining the user must submit counter-evidence: "Take a photo of the spot to show it's not garbage. Our team will review within N hours."
- A required photo-capture control: "Take a Photo of the Spot"
- An info callout explaining consequences: *"if approved, this report is removed from the public map and analytics. If rejected, it stays where it is. Disputes that are clearly fraudulent may be ignored."*
- A **Submit for Review** button (this goes to a moderation queue — it is NOT an instant hide/delete)

Build flagging as a dispute-with-evidence workflow with a moderation queue and a stated SLA, not a one-tap hide.

### Step 6 — "Verify Cleanup"

Confirmed as a distinct, positive-styled action (green, checkmark icon) sitting beside Flag as Incorrect. Exact backend behavior (does it require an after-photo, does it need N confirmations, does it flip status immediately) was not observed in production and should be a deliberate product decision for CivicQuest — recommendation: require an after-photo before flipping status, to keep the resolution signal trustworthy (this is the weakest part of comparable products — do it properly here).

---

## 3. Data sources — use exactly these, in this combination

There is no single API that returns "MLA + MP + ward rep with photo" for a location. Build a two/three-stage pipeline instead.

### 3.1 MLAs — name, constituency, party, education, photo

**Source: PRS Legislative Research.** One CSV per state per assembly term, at a predictable path:

```
https://prsindia.org/files/mlatrack/<state-slug>/<term>/<state-slug>_assembly_term_<term>.csv

# Example (Karnataka, current/16th assembly):
https://prsindia.org/files/mlatrack/karnataka/16/karnataka_assembly_term_16.csv
```

Columns (verified header):
```
MLA Name, Age, Constituency, Gender, Party, Membership, Education,
Start of term, End of Term, Attendance, Attendance -State average,
No. of Questions Asked, Question -State Average, Number Of Debates,
Debate State Average, Note, Term, State, Images
```

`Images` is a filename (may contain spaces — URL-encode when fetching). The photo lives at:

```
https://prsindia.org/files/mlatrack/<state-slug>/<term>/mla_images/<Images>

# Verified working examples:
https://prsindia.org/files/mlatrack/karnataka/16/mla_images/A C Srinivasa.jpg
https://prsindia.org/files/mlatrack/kerala/15/mla_images/P Prasad.jpg
```

Join key: **Constituency** (assembly constituency name — string match, normalize casing/whitespace before joining against your boundary data's constituency names).

### 3.2 MPs — official, live, name + constituency + party + photo + contact

**Source: Digital Sansad (Lok Sabha's own portal).**

```
https://sansad.in/api_ls/member
```

Live JSON, undocumented but working. Verified fields per member:

```
mpsno, firstName, lastName, mpFirstLastName, mpLastFirstName,
stateName, constName, partyFname, partySname,
imageUrl, status, email, phone, dob, age, qualification,
profession, noOfTerms, lsExpr
```

**Critical: this endpoint returns every Lok Sabha member across many terms (thousands of records), not just the current 543.** Filter `status === "Sitting"` before treating a record as your current roster.

**Critical: `imageUrl` is a per-person UUID from Digital Sansad's document system** (`https://sansad.in/getFile/dms/fetch/<uuid>?source=dsp2`) — it is NOT a predictable filename pattern like the PRS MLA photos are. You must read this field from the JSON response and store it; do not try to construct it.

Join key: **constName** (parliamentary constituency name — string match against your boundary data).

Snapshot this endpoint into your own database on a nightly job. Never call it live from a client — it's an unversioned internal API and could change without notice.

### 3.3 Ward/corporation boundaries — turn a location into a ward

```
https://data.opencity.in/dataset/gba-wards-delimitation-2025
```

369 wards across 5 corporations, notified 19 Nov 2025. Formats: KML, CSV. Public domain / Open Data certified. This is your ward polygon source — load into PostGIS, one row per ward with `corporation`, `ward_number`, `zone`, `boundary geography(Polygon)`.

### 3.4 Assembly + parliamentary constituency boundaries

```
https://github.com/datameet/maps
```

Shapefiles, CC BY 4.0. Contains assembly-constituencies and parliamentary-constituencies folders. Convert to GeoJSON/PostGIS with `ogr2ogr`. This is how you resolve a lat/lng to "which MLA constituency" and "which MP constituency" independent of ward boundaries (a ward's MLA is not always geographically the same shape as the ward itself).

### 3.5 Local bodies + pincodes (secondary, do not use pincode as your primary key)

```
https://www.data.gov.in/resource/local-government-directory-lgd-local-bodies-pin-codes
https://github.com/planemad/india-local-government-directory   (mirror)
```

**Pincodes are postal delivery routes and cross ward/constituency boundaries.** There is no official pincode → constituency mapping. If your UI accepts a pincode as input, resolve it to a centroid point, then run the same point-in-polygon logic as a GPS coordinate would use — never join directly on pincode. If a pincode's centroid is ambiguous or near a boundary, surface that to the user rather than silently picking one constituency.

### 3.6 Officer chain (Commissioner, Additional Commissioner, AEE, JHI) and the waste utility

**No dataset exists for this — anywhere.** This is real: national and state governments do not publish a structured directory of this administrative chain. Hand-author it as static seed data per corporation (there are only 5 corporations in the GBA structure), reviewed and updated quarterly from the corporation's own published contact page. Example seed shape:

```json
{
  "corporation": "North",
  "chain": [
    { "role": "Commissioner", "scope": "GBA / Corporation head", "tier": "TOP" },
    { "role": "Additional Commissioner", "scope": "North-level oversight", "tier": "MID", "email": "...", "phone": "1533" },
    { "role": "Asst. Executive Engineer (AEE)", "scope": "Engineering oversight", "tier": "MID" },
    { "role": "Junior Health Inspector (JHI)", "scope": "Ward-level SWM officer · First point of escalation", "tier": "FRONTLINE", "phone": "1533", "whatsapp": "+91XXXXXXXXXX" }
  ],
  "waste_utility": { "name": "...", "reports_to": "GBA", "whatsapp": "+91XXXXXXXXXX", "email": "..." }
}
```

### 3.7 Ward-level elected member / corporator

**No dataset exists for this either.** Model it as a nullable, dated field per ward (`seat_status: filled|vacant`, `vacant_since`, `name`, `party` when filled) and update it manually as elections resolve seats. Do not assume permanently vacant or permanently filled — build the schema to change over time.

---

## 4. Data model (Postgres / PostGIS)

```sql
wards (
  id, name, slug unique, ward_number, corporation, zone,
  boundary geography(Polygon,4326),
  assembly_constituency_id fk, parliamentary_constituency_id fk
)

constituencies (
  id, name, slug unique, type enum('assembly','parliamentary'),
  boundary geography(Polygon,4326)
)

representatives (
  id, role enum('MLA','MP'), name, party, constituency_id fk,
  photo_url, source enum('prs','sansad'), source_id, fetched_at
)

constituency_stats (            -- powers the MLA/MP analytics panel
  constituency_id fk, role enum('MLA','MP'),
  active_reports int, total_reports int, avg_days_unresolved numeric,
  ward_count int, updated_at
)

ward_officials (                -- the static hand-maintained chain, per corporation/zone
  id, corporation, tier enum('TOP','MID','FRONTLINE'),
  role_title, scope_description, email, phone, whatsapp
)

ward_seats (                    -- the corporator / ward-level elected seat
  ward_id fk primary, seat_status enum('filled','vacant'),
  name null, party null, vacant_since date null
)

reports (
  id, ward_id fk, location geography(Point,4326),
  address_text, photo_url, severity, status, waste_type,
  also_seen_count, created_at, resolved_at, resolution_photo_url
)
```

---

## 5. Pipeline / jobs to build

1. **Nightly**: pull PRS state CSV(s) for every state you cover → upsert `representatives` (role=MLA), download and re-host each photo (don't hotlink PRS's servers).
2. **Nightly**: pull `sansad.in/api_ls/member`, filter `status="Sitting"`, upsert `representatives` (role=MP), re-host `imageUrl` similarly.
3. **Nightly/on-write**: recompute `constituency_stats` from your live `reports` table, grouped by each representative's constituency.
4. **One-time + on-boundary-change**: load ward and constituency boundaries from OpenCity and datameet/maps into PostGIS.
5. **On report create**: run point-in-polygon against ward + assembly constituency + parliamentary constituency to stamp `ward_id`, then join to `representatives` and `ward_officials` for display — do this server-side, never trust a client-resolved ward.

---

## 6. Explicit do-nots

- Do not use pincode as a join key for constituency/ward resolution — resolve to a centroid first.
- Do not construct MP photo URLs — read `imageUrl` from the JSON, it's not a predictable pattern.
- Do not put contact info (phone/email/handle) on the MLA/MP panel — that panel is analytics only.
- Do not put analytics on the officer/utility panels — those are contact-only.
- Do not treat `sansad.in/api_ls/member`'s full response as "current MPs" without filtering `status="Sitting"` — it includes historical members.
- Do not call `sansad.in/api_ls/member` live from the client app — snapshot it server-side.
- Do not hardcode the corporator seat as permanently vacant or invent a name — model it as nullable/dated and keep it updatable.
- Do not make "Flag as Incorrect" an instant hide — it's a photo-evidence dispute with a moderation queue and a stated review SLA.

---

## 7. Definition of done

- [ ] Tapping any report pin opens the report sheet with the exact section order in §2, Step 2
- [ ] Accountability hierarchy renders ward → utility+corporator → officer chain → elected reps, matching §2 Step 3
- [ ] Officer/utility card taps open a contact panel with working `wa.me`, `mailto:`, `tel:` links (§2 Step 4a)
- [ ] MLA/MP card taps open an analytics panel with the 4 stat tiles + constituency list, and nothing else (§2 Step 4b)
- [ ] Flag as Incorrect requires a counter-photo and routes to a moderation queue (§2 Step 5)
- [ ] MLA data is joined from the PRS CSV per state/term; photos load from the `mla_images` path
- [ ] MP data is joined from `sansad.in/api_ls/member`, filtered to `status="Sitting"`, photos read from `imageUrl`
- [ ] Ward boundaries loaded from OpenCity GBA dataset; constituency boundaries from datameet/maps
- [ ] Corporator seat and officer chain are stored as editable data, not hardcoded copy
- [ ] Every screenshot in `/Users/girishbisane/Desktop/CivicQuest/screenshots` has been cross-checked against the implemented flow