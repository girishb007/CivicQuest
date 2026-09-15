# CivicQuest Observability & Analytics

## 1. Three layers

### Technical
- errors,
- latency,
- database health,
- queue health,
- worker failures.

### Product
- onboarding,
- report funnel,
- retention,
- quests,
- account conversion.

### Civic impact
- valid reports,
- hotspots,
- resolutions,
- cleanup participation.

## 2. Structured logs

Fields:
- timestamp,
- environment,
- service,
- request_id,
- pseudonymous user/anonymous ID where allowed,
- route,
- status_code,
- latency_ms,
- error_code.

Do not log raw media, auth tokens, private object keys, or unnecessary PII.

## 3. Metrics

API:
- request rate,
- p50/p95/p99 latency,
- 4xx/5xx.

Database:
- connections,
- slow queries,
- CPU/storage,
- locks.

Queue:
- depth,
- oldest message age,
- retries,
- DLQ count.

Worker:
- processing latency,
- failure rate,
- AI provider errors.

## 4. Tracing

Use OpenTelemetry for browser → API → DB / queue → worker → provider flows.

Trace IDs should appear in logs.

## 5. Alerts

P1:
- API unavailable,
- DB unavailable,
- queue stalled,
- upload failure spike.

P2:
- moderation backlog,
- AI error spike,
- worker failures,
- stale hotspot jobs.

## 6. Product events

```text
landing_viewed
guest_session_created
location_permission_requested
location_permission_granted
explore_viewed
report_started
photo_uploaded
report_category_suggested
report_submitted
report_published
report_upvoted
hotspot_viewed
account_link_prompted
account_linked
quest_started
quest_completed
civic_action_joined
civic_action_checked_in
impact_proof_submitted
share_card_created
```

## 7. Primary funnel

```text
Landing
→ Explore
→ Start Report
→ Upload
→ Review
→ Submit
→ Published/Verified
→ Return within 7 days
```

## 8. Metrics

Activation:
- start-to-explore,
- first report completion,
- time to first report.

Retention:
- D1,
- D7,
- D30.

Quality:
- invalid report rate,
- duplicate rate,
- moderation rate.

Impact:
- hotspots created,
- issues resolved,
- resolution time,
- Civic Action completions.

## 9. Privacy

Use pseudonymous analytics identifiers and never send private evidence to third-party analytics.
