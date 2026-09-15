## 1. Implementation and verification

- [ ] 1.1 Implement draft/review/finalize/status/history; reporting integration test passes
- [ ] 1.2 Enforce low-risk publication and Civic Catch gates; visibility tests pass

### 12 September checkpoint

Same-page capture retries now retain draft/finalize idempotency keys and media-upload state. Direct Node assertions passed for a lost upload-completion response without duplicate authorization or upload. New Vitest/TypeScript verification stalled and remains open; reload/expiry recovery and the rest of this chunk are not complete. See docs/IMPLEMENTATION_STATUS.md for the full ledger.
