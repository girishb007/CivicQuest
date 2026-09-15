## 1. Implementation and verification

- [ ] 1.1 Implement sessions, CSRF, role authorization and Google adapter; auth tests pass
- [ ] 1.2 Preserve guest history on new/existing account claims; merge/deduplication tests pass

## 2. Portrait persistence

- [x] 2.1 Migrate optional portrait selection and expose an authenticated, CSRF-protected allowlisted update for guests and registered users
- [x] 2.2 Preserve portraits during linking, prefer an existing account selection and clear portraits on deletion; verify on PostGIS
