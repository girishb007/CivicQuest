# CivicQuest operations

## Local startup

The container stack is defined in `docker-compose.yml`: `docker compose up --build` runs migrations, synthetic seeding, API, worker, and web. Docker/Compose execution is not yet validated on this machine due disk limitations. The website uses `http://localhost:3000`; keep that exact origin in CQ_ORIGIN for cookie/CSRF checks.

For an existing isolated native PostGIS database, install the locked Python environment (`uv sync --frozen --extra dev`), run `uv run alembic upgrade head`, then `uv run civicquest seed`. Start `uv run uvicorn civicquest.main:app --host 127.0.0.1 --port 8000`, `CQ_QUEUE_MODE=database uv run civicquest worker`, and `pnpm dev`. Database worker mode is a clearly local alternative, not evidence of SQS delivery correctness. Redis is required in live environments; local/test mode tolerates an absent Redis instance.

## Failure recovery

Outbox records and civic changes commit together. A worker records its receipt and domain effects in one database transaction. Failures retry with exponential delay and become dead after five attempts. Moderators can inspect `/api/v1/admin/jobs` and retry an individual dead job; `civicquest retry-jobs` retries all dead records and is intended for a trusted operator.

Use `civicquest rebuild` to derive CivicDex, badges, and hotspots again from source records. The XP ledger remains authoritative and is never rewritten by rebuild. Restricting content makes origin media requests fail and revokes share-card access. CloudFront is configured with caching disabled; the service worker caches only the shell.

## Backup and restore

`scripts/ops/backup.py` stores a PostgreSQL custom archive, media tarball, and checksums. Set `CQ_DATABASE_URL` and `PG_BIN` (the directory containing pg_dump/pg_restore/psql). The destination must be new. Use an encrypted, access-controlled destination for real data.

```sh
python scripts/ops/backup.py backup --archive /secure/backups/civicquest-YYYYMMDD --media .local/media
# Point CQ_DATABASE_URL at a separate, newly created empty database first.
python scripts/ops/backup.py restore --archive /secure/backups/civicquest-YYYYMMDD --media /empty/restore/media
uv run civicquest rebuild
```

Restore refuses nonempty databases/media directories and checksum mismatches. Never point a drill at the live database. The local database/media restore was exercised; AWS RDS snapshot restore and S3 version recovery need a staging drill.

## Data deletion and retention

DELETE `/api/v1/account` requires the current session and CSRF token, removes public access to reports/cards, clears email/handle/linked identities/push endpoints, and revokes sessions. Private civic/audit source records remain for the documented retention period. The operator `civicquest retention` command deletes originals for closed report cases after the configured 30-day default; filesystem and S3 deletes are retryable. Audit/history purge policy, Action/resolution-media retention, and security-log retention approval remain release prerequisites.

## Reference refresh

Run `civicquest refresh-reference` manually before enabling the production schedule. It downloads and validates the Department of Posts pincode directory, BMC ward and office layers, and the Digital Sansad member roster in one database transaction. Incomplete snapshots fail without replacing the last reviewed data. EventBridge Scheduler definitions run this monthly at 03:00 Asia/Kolkata and retention daily; both remain disabled until `enable_schedules = true` is approved for a deployed environment.

## Deployment and rollback

Terraform inputs and prerequisites are documented in `infrastructure/terraform/README.md`. No live deployment is included in this implementation session. Build immutable API/web images and record digests; run CI and review the Terraform plan before approved provisioning. Populate application secrets, run the migration ECS task, import approved boundaries and owners, then scale services from zero only after readiness checks and staging acceptance.

For an application rollback, select the previous image digests/task definitions and use ECS deployment circuit-breaker recovery. Do not run destructive migration downgrades; the initial migration intentionally refuses one. Restore into a new database for a database recovery, verify it, and change the application secret only after review. Never seed synthetic civic data into a live environment.
