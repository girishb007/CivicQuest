# CivicQuest Security, Privacy & Authentication

## 1. Authentication model

Phase 1 is guest-first.

### Guest identity
On first meaningful interaction:
- create server-side guest user,
- set signed HTTP-only secure session cookie,
- rotate session tokens,
- store only a token hash server-side.

Do not use localStorage for long-lived authentication tokens.

### Account conversion
Later link guest identity to Google, Apple, or phone OTP if required. Preserve the same user record so XP and history survive conversion.

## 2. Authorization

Roles:
- guest
- registered user
- NGO organizer
- moderator
- admin

Enforce authorization in the backend on every protected resource.

## 3. Browser security

Use:
- SameSite cookies,
- CSRF protection,
- CSP,
- HSTS,
- `X-Content-Type-Options`,
- frame restrictions,
- secure cookies,
- strict CORS.

## 4. Rate limiting

Redis-backed limits for:
- report creation,
- media uploads,
- upvotes,
- account linking,
- abuse reports,
- share-card generation.

## 5. Media security

### Original media
- private bucket/prefix,
- server-controlled signed URLs,
- short TTL,
- no public ACL,
- access logged.

### Public derivatives
- separate prefix/bucket,
- metadata stripped,
- resized/transformed,
- CDN delivery.

## 6. EXIF and metadata

Remove EXIF from public media.

Never expose private EXIF or object-storage keys through public APIs.

## 7. Location privacy

Do not expose:
- reporter home location,
- location history,
- private Civic Action check-in coordinates.

Use report location, not reporter history.

## 8. PII minimization

Collect only what is required.

Possible PII:
- email,
- phone,
- auth subject,
- security/IP metadata.

Keep public profile data separate from private identity data.

## 9. Secrets

Use AWS Secrets Manager / Parameter Store.

Never store secrets in:
- repo,
- frontend bundle,
- logs,
- analytics events.

## 10. Database security

- TLS connections,
- least-privilege DB roles,
- separate app/migration roles,
- encrypted storage,
- automated backups,
- no public database endpoint.

## 11. API security

- request size limits,
- schema validation,
- upload limits,
- idempotency,
- replay protection for Civic Action check-ins,
- request IDs.

## 12. Admin security

Moderators/admins should use:
- registered accounts,
- MFA where possible,
- shorter session TTL,
- audit logs,
- strict permissions.

## 13. Data deletion

Need workflows for:
- account deletion,
- unlinking public handle,
- removing public media where policy requires,
- retaining required security/audit records with documented rules.

## 14. Privacy-by-design rule

If a datum is not needed to deliver CivicQuest, do not collect it.
