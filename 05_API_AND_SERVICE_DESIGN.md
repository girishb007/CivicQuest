# CivicQuest API & Service Design

## 1. API style

Use REST for Phase 1.

Reasons:
- simple public/open-source developer experience,
- easy browser/mobile usage,
- easy caching,
- FastAPI/OpenAPI support.

Base path:

```text
/api/v1
```

Use JSON for metadata and presigned object-storage uploads for media.

## 2. API conventions

- UUID identifiers
- UTC timestamps in ISO-8601
- cursor pagination for feeds
- idempotency keys for XP/report-finalization/action completion
- structured error objects
- request IDs
- never expose private object-storage keys

Error shape:

```json
{
  "error": {
    "code": "REPORT_NOT_VISIBLE",
    "message": "This report is not available.",
    "request_id": "..."
  }
}
```

## 3. Identity

```text
POST /sessions/guest
GET  /me
POST /auth/link/google
POST /auth/logout
```

`GET /me` returns identity type, public handle, XP, level, CivicDex summary, and account-linking state.

## 4. Explore

```text
GET /explore?lat=&lng=&radius_m=&types=
GET /places/search?q=
GET /administrative-areas/lookup?lat=&lng=
```

Explore response returns lightweight map items instead of full report bodies.

## 5. Reports

```text
POST /reports/drafts
POST /reports/{id}/media/presign
POST /reports/{id}/finalize
GET  /reports/{id}
GET  /reports
POST /reports/{id}/upvotes
DELETE /reports/{id}/upvotes
POST /reports/{id}/abuse
```

### Draft request

```json
{
  "report_type": "place",
  "lat": 19.0178,
  "lng": 72.8478,
  "client_location_accuracy_m": 18
}
```

### Finalize response

```json
{
  "id": "...",
  "status": "processing",
  "visibility": "pending",
  "provisional_xp": 8
}
```

## 6. Category suggestion

```text
POST /reports/{id}/classification
GET  /reports/{id}/processing-status
```

Prefer server-triggered jobs rather than making the browser orchestrate AI work.

## 7. Feeds

```text
GET /feed/places?cursor=
GET /feed/civic-catches?cursor=
GET /feed/trending?area_id=&cursor=
```

## 8. Hotspots

```text
GET /hotspots?lat=&lng=&radius_m=
GET /hotspots/{id}
GET /hotspots/{id}/reports
```

## 9. Accountability

```text
GET /accountability/resolve?lat=&lng=&category_id=
GET /administrative-areas/{id}
GET /authorities/{id}
GET /representatives?area_id=
```

Expose source/provenance metadata for official-looking mappings.

## 10. Gamification

```text
GET /gamification/me
GET /levels
GET /badges
GET /civicdex
GET /civicdex/me
GET /leaderboards/mumbai
GET /leaderboards/local?area_id=
```

XP awards are internal service operations, not public add-XP endpoints.

## 11. Quests

```text
GET  /quests
GET  /quests/me
POST /quests/{id}/claim
```

Claim is server-validated.

## 12. Civic actions

```text
GET  /civic-actions
GET  /civic-actions/{id}
POST /civic-actions/{id}/join
POST /civic-actions/{id}/check-in
POST /civic-actions/{id}/proof/presign
POST /civic-actions/{id}/complete
```

## 13. Profiles and sharing

```text
GET /profiles/{handle}
POST /profiles/me/handle
POST /share-cards
GET /share-cards/{id}
```

Share cards use public-safe data only.

## 14. Notifications

```text
GET /notifications
POST /notifications/{id}/read
POST /push/subscriptions
DELETE /push/subscriptions/{id}
```

## 15. Moderation / admin

```text
GET  /admin/moderation/cases
GET  /admin/moderation/cases/{id}
POST /admin/moderation/cases/{id}/decision
POST /admin/reports/{id}/visibility
POST /admin/reports/{id}/merge-duplicate
POST /admin/actions/{id}/verify
```

## 16. Internal domain events

```text
report.created
report.media_uploaded
report.finalized
report.classified
report.flagged
report.published
report.upvoted
report.hotspot_linked
report.resolved
action.joined
action.checked_in
action.proof_uploaded
action.verified
xp.awarded
badge.earned
quest.completed
```

## 17. Service contract rule

Even in a modular monolith, modules should not mutate each other's tables arbitrarily.

Examples:
- reporting requests XP through GamificationService,
- civic actions request moderation through ModerationService,
- feeds read public report projections,
- accountability owns responsibility rules.
