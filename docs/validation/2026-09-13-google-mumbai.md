# Google identity and Mumbai reference validation — 13 September 2026

## Delivered

- Google account action remains visible for guest and registered/demo sessions.
- API reports readiness only when both OAuth client ID and secret exist and publishes the exact callback URL.
- Profile returns linked provider names without exposing them on public profiles.
- Active local geography: one Greater Mumbai boundary, 24 BMC administrative wards, 36 Assembly constituencies and six Parliamentary constituencies.
- Dated representatives: 36 MLAs from the Maharashtra CEO/ECI Gazette and six sitting MPs from Digital Sansad.
- Postal search: 230 in-boundary Department of Posts office points across 89 Mumbai City/Suburban pincodes.
- Credential-free local map now has an attributed OpenStreetMap raster basemap; MapTiler remains the configured production adapter.
- Admins can create and expire reviewed ward/category ownership rules, update or expire ward contacts, and cannot publish overlapping effective periods for the same ward/category family.
- Ward pages present active ownership rules separately from ward contacts and MLA/MP context; absent rules remain visibly “Owner not confirmed.”
- Community Group admins can edit, deactivate and reactivate records; inactive records leave the citizen directory, and sources older than 90 days show a review-due state.
- A transactional `refresh-reference` command validates official India Post, BMC ward, BMC contact and Digital Sansad snapshots. AWS schedules are defined but disabled until reviewed deployment prerequisites exist.

## Evidence

- Backend/PostGIS: 43 tests passed using the prepared native runtime environment. The repository `.venv` currently has a partially hydrated `psycopg_binary` library and is not the validated environment.
- TypeScript: `tsc --noEmit` passed.
- Ruff and Python compilation passed.
- Geography: 8 Playwright cases passed across deskt