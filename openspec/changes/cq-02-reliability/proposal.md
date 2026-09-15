## Why

Deliver durable data and jobs as part of the user-approved CivicQuest V1 implementation.

## What Changes

- Implement schema migrations and domain constraints; PostgreSQL integration tests pass
- Implement transactional outbox, receipts and retry/DLQ; crash and replay tests pass

## Capabilities

### New Capabilities
- `reliability`: Durable data and jobs.

### Modified Capabilities

None.

## Impact

Local web/API/worker, contracts and checks. Depends on CQ-01. See docs/DECISIONS.md.
