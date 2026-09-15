## Why

Deliver guest identity and account linking as part of the user-approved CivicQuest V1 implementation.

## What Changes

- Implement sessions, CSRF, role authorization and Google adapter; auth tests pass
- Preserve guest history on new/existing account claims; merge/deduplication tests pass

## Capabilities

### New Capabilities
- `identity`: Guest identity and account linking.

### Modified Capabilities

None.

## Impact

Local web/API/worker, contracts and checks. Depends on CQ-02. See docs/DECISIONS.md.
