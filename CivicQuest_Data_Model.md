# CivicQuest Product Data Model

This document defines the product-level data model for CivicQuest. It supports guest-first participation, geospatial discovery, community attention, accountability, verified civic action, and an auditable XP history. It is a product contract, not a final database schema.

## Core Entities

### User

A claimed CivicQuest identity. Guest activity may exist before a User record is created.

```text
User
  id
  username
  display_name
  account_state             # GUEST, ACTIVE, SUSPENDED, DELETED
  home_city
  xp_total
  level
  credibility_score
  impact_streak_days
  created_at
  updated_at
```

### GuestSession

Temporarily associates reports and XP events with a device or anonymous session until progress is claimed. It must not store unnecessary personal data.

```text
GuestSession
  id
  device_reference
  claim_status              # UNCLAIMED, CLAIMED, EXPIRED
  expires_at
  created_at
```

### Report

Represents a Places issue or Civic Catch submitted by a citizen.

```text
Report
  id
  reporter_user_id          # nullable while guest activity is unclaimed
  guest_session_id          # nullable after account claim
  report_type               # PLACE or CIVIC_CATCH
  category
  status                    # SUBMITTED, SCREENED, VERIFIED, ACTIONED,
                            # RESOLVED, REJECTED, DISPUTED, CLOSED
  description
  evidence_media_id
  location_point
  address_text
  city
  ward_id
  authority_id
  severity
  credibility_at_submission
  created_at
  updated_at
```

### ReportVote and Verification

Votes signal that a report deserves attention; they are not proof. Verification records whether a report or resolution was checked.

```text
ReportVote
  id
  report_id
  user_id                    # nullable for supported guest voting
  guest_session_id           # nullable for authenticated voting
  created_at

Verification
  id
  target_type                # REPORT or RESOLUTION
  target_id
  verifier_user_id
  verification_type          # COMMUNITY, MODERATOR, AUTHORITY, ORGANIZER
  result                     # CONFIRMED, NOT_FOUND, DISPUTED
  notes
  created_at
```

### Hotspot, Authority, and AdministrativeBoundary

Hotspots aggregate related reports in a geographic area. Administrative boundaries map a location to the responsible civic owner.

```text
Hotspot
  id
  area_name
  center_point
  radius_meters
  ward_id
  authority_id
  status                    # ACTIVE, ACTIONED, RESOLVED, CLOSED
  active_report_count
  upvote_count
  score
  score_updated_at
  created_at
  updated_at

AdministrativeBoundary
  id
  boundary_type              # CITY, WARD, CONSTITUENCY
  name
  geometry
  parent_boundary_id
  source_reference
  valid_from
  valid_until

Authority
  id
  name
  authority_type             # MUNICIPAL_BODY, WARD, DEPARTMENT, RAILWAY,
                             # NGO, OTHER
  jurisdiction_boundary_id
  contact_reference
  active

Representative
  id
  name
  role                       # COUNCILLOR, MLA, MP, OTHER
  jurisdiction_boundary_id
  source_reference
  term_start
  term_end
  active
```

### CivicAction and ActionParticipation

These entities model positive offline participation and its verification workflow.

```text
CivicAction
  id
  organizer_id
  name
  description
  start_time
  end_time
  location_point
  location_name
  capacity
  xp_reward
  status                    # DRAFT, PUBLISHED, FULL, COMPLETED, CANCELLED
  created_at

ActionParticipation
  id
  action_id
  user_id
  joined_at
  checked_in_at
  before_media_id
  after_media_id
  team_media_id
  verification_status       # PENDING, VERIFIED, REJECTED
  xp_awarded
  completed_at
```

### Media, Resolution, and Progress

Media is stored as metadata while the binary object lives in object storage. XP is event-based so awards can be audited, reversed, and explained.

```text
Media
  id
  owner_user_id
  storage_key
  media_type                 # IMAGE or VIDEO
  content_hash
  moderation_status
  captured_at
  created_at

Resolution
  id
  report_id
  submitted_by_user_id
  action_description
  after_media_id
  status                    # SUBMITTED, VERIFIED, DISPUTED, REJECTED
  verified_at
  created_at

XPEvent
  id
  user_id
  source_type               # REPORT, VERIFICATION, RESOLUTION, ACTION,
                            # BADGE, ADMIN_ADJUSTMENT
  source_id
  points
  reason
  idempotency_key
  created_at

CivicDexEntry
  user_id
  category
  rarity
  first_discovered_at
  verification_status

QuestProgress
  user_id
  quest_id
  progress
  completed_at

LeaderboardSnapshot
  id
  scope                     # CITY, WARD, GLOBAL
  scope_id
  period_start
  period_end
  user_id
  rank
  xp_total
  generated_at
```

## Relationships

```text
User / GuestSession
       |
       +--> Report --> Media
       |      |
       |      +--> ReportVote
       |      +--> Verification
       |      +--> Resolution --> Media
       |      +--> Hotspot --> Authority --> AdministrativeBoundary
       |
       +--> XPEvent --> CivicDexEntry / QuestProgress / LeaderboardSnapshot
       |
       +--> ActionParticipation --> CivicAction
```

## Data Invariants

1. A report has exactly one `report_type` and one supported category.
2. A report location is required and is mapped to a supported city and ward when boundary data is available.
3. A user or guest session cannot vote more than once on the same report.
4. An XP source uses an idempotency key so retries cannot award XP twice.
5. Upvotes affect attention and ranking but do not directly award reporter XP.
6. Only verified reports and verified action participation can award impact XP.
7. Civic Catch identity and evidence visibility must pass moderation policy before public display.
8. Media deletion, moderation, and retention events are auditable.
9. Authority mappings retain their source and validity period.
10. Derived hotspot and leaderboard values can be rebuilt from source records.
