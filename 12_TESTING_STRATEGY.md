# CivicQuest Testing Strategy

## 1. Testing pyramid

```text
Many unit tests
↓
Service/integration tests
↓
API contract tests
↓
Browser E2E tests
↓
Small number of production smoke tests
```

## 2. Backend unit tests

Cover:
- XP rules,
- category validation,
- report state transitions,
- accountability rules,
- hotspot score,
- quest progress,
- moderation transitions.

## 3. Database integration tests

Use real PostgreSQL/PostGIS in CI.

Test:
- ST_Contains ward lookup,
- ST_DWithin nearby search,
- geospatial indexes,
- duplicate queries,
- hotspot associations,
- transactions.

Do not mock core PostGIS behavior.

## 4. Frontend tests

Cover:
- report flow,
- category selection,
- feed cards,
- permission fallbacks,
- profile progress,
- loading/error states.

## 5. Playwright E2E

### Guest reporting
Visit → Explore → Report → Upload → Review → Submit → Success.

### Account conversion
Guest earns XP → links account → history preserved.

### Upvote
Upvote once → duplicate prevented → state persists.

### Civic Action
Join → check in → upload proof → pending verification.

### Moderator
Review flag → change visibility → audit entry.

## 6. Media tests

- oversized upload rejected,
- invalid type rejected,
- EXIF stripped from public derivative,
- original not publicly accessible.

## 7. Geospatial fixtures

Create synthetic Mumbai fixtures:
- ward A,
- ward B,
- boundary-edge point,
- outside-Mumbai point,
- reports 10m apart,
- reports 500m apart.

## 8. Load tests

Use k6/Locust for:
- map viewport reads,
- feed reads,
- report burst,
- upvote burst,
- upload flow,
- hotspot recompute.

## 9. Security tests

- session fixation,
- CSRF,
- IDOR,
- admin authorization,
- signed URL expiry,
- rate-limit bypass,
- Civic Action check-in replay.

## 10. Accessibility

Target WCAG AA.

Test:
- keyboard,
- labels,
- focus,
- contrast,
- screen readers,
- reduced motion,
- list alternative to maps.

## 11. Browsers

Pilot minimum:
- Chrome Android,
- Safari iOS,
- desktop Chrome,
- desktop Safari/Edge.

Test camera/upload on actual phones.
