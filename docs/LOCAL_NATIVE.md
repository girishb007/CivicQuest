# Local macOS demo runtime

From the repository root, start the prepared runtime:

```sh
python3 scripts/dev/start-native.py
```

Open **http://localhost:3000**. The API listens on `127.0.0.1:8001`; the dedicated PostgreSQL 16/PostGIS instance listens on `127.0.0.1:55434`. The worker polls the database outbox. This is a native local demo, not validation of Docker, Redis, SQS or live providers. Civic reports and local identities are synthetic. The active reference geography, representatives, post offices and BMC ward contacts are separately labeled with their reviewed sources; BMC redistribution approval remains required before public deployment. In Profile, local demo identities provide citizen/moderator/admin access.

The prepared runtime is under `~/Library/Caches/CivicQuest`. Preserve this folder: it contains the database, uploaded media and dependencies. Back it up before clearing caches. It survives ordinary terminal closure/reboot, but services must be started again after reboot. The previous temporary database was unavailable; this instance was seeded afresh.

The launcher applies migrations, seeds idempotently, synchronizes `apps/web` into the runtime and starts detached API, worker and web processes. Run it again after web source edits to synchronize changes. Backend source is read directly from the repository. Dependencies are outside cloud-synced Desktop to avoid cloud hydration stalls. Dependency changes require reinstalling the corresponding runtime environment. Logs and PID files are in the runtime folder (`api.log`, `worker.log`, `web.log`, `postgres.log`). It does not stop or replace an unrelated process occupying a service port.

## Preparing a replacement runtime

This restart script expects dependencies already installed; it is not a clean-checkout bootstrap. Preparation used Python 3.11, Node 22.23.2, a bootstrap Python venv containing uv, and:

```sh
UV_PROJECT_ENVIRONMENT="$HOME/Library/Caches/CivicQuest/api-env" \
  "$HOME/Library/Caches/CivicQuest/python/bin/uv" sync --frozen --extra dev
```

Copy `apps/web/` to the runtime `web/`, excluding `node_modules`, `.next` and `tsconfig.tsbuildinfo`, then run `npm install --no-audit --no-fund` there. This web install resolves package.json and **does not validate the repository's frozen pnpm lockfile**.

PostgreSQL binaries are copied from the official [Postgres.app PostgreSQL 16 download](https://postgresapp.com/downloads.html) into runtime `Postgres.app` (v2.9.6 with PostgreSQL 16.15/PostGIS 3.4.6). Initialize `pgdata` with `initdb -U civicquest -A trust --locale=C --encoding=UTF8`, start it on the loopback port above, then create database `civicquest`. Trust authentication is for this loopback-only demo. Other installed PostgreSQL instances are untouched.

## Stopping

Inspect the commands for the PIDs in `api.pid`, `worker.pid` and `web.pid`, then terminate those processes with `kill <pid>`. Stop this database with:

```sh
"$HOME/Library/Caches/CivicQuest/Postgres.app/Contents/Versions/16/bin/pg_ctl" \
  -D "$HOME/Library/Caches/CivicQuest/pgdata" stop -m fast
```

Keep database and media together when backing up. Use the existing operations runbook for logical backup and restore. Do not delete the runtime to restart the app.
