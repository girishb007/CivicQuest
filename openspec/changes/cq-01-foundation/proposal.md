## Why

Deliver reproducible local stack as part of the user-approved CivicQuest V1 implementation.

## What Changes

- Create pinned web/API/worker toolchains and lockfiles; dependency installation passes
- Create Compose and seed/start commands; health checks pass on a clean database

## Capabilities

### New Capabilities
- `foundation`: Reproducible local stack.

### Modified Capabilities

None.

## Impact

Local web/API/worker, contracts and checks. Depends on CQ-00. See docs/DECISIONS.md.
