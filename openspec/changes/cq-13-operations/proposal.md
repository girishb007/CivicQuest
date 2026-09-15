## Why

Deliver deployment and recovery as part of the user-approved CivicQuest V1 implementation.

## What Changes

- Implement Terraform, release workflows and telemetry; static infrastructure validation passes
- Implement retention, deletion, backup/restore and rebuild commands; local recovery drill passes

## Capabilities

### New Capabilities
- `operations`: Deployment and recovery.

### Modified Capabilities

None.

## Impact

Local web/API/worker, contracts and checks. Depends on CQ-12. See docs/DECISIONS.md.
