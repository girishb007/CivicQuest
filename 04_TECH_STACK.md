# CivicQuest Recommended Tech Stack

## 1. Stack selection criteria

The stack should be:

- fast to build,
- easy to open source,
- strong for geospatial workloads,
- good for mobile web,
- familiar to backend/data engineers,
- affordable in a pilot,
- replaceable where possible.

## 2. Recommended Phase 1 stack

| Layer | Recommendation | Why |
|---|---|---|
| Web frontend | Next.js + React + TypeScript | SSR/SEO, responsive UI, PWA-ready |
| Styling | Tailwind CSS + accessible component primitives | fast consistent UI |
| Server state | TanStack Query | caching, retries, async state |
| Forms | React Hook Form + schema validation | robust mobile forms |
| Maps | MapLibre GL JS | open-source map rendering |
| API backend | FastAPI + Python | fast development, typed APIs |
| Validation | Pydantic | API schemas |
| ORM / DB access | SQLAlchemy 2 + GeoAlchemy | Postgres/PostGIS support |
| Migrations | Alembic | schema migrations |
| Primary DB | PostgreSQL + PostGIS | relational + geospatial |
| Cache | Redis | rate limits, cached feeds, jobs metadata |
| Object storage | Amazon S3 | report/action media |
| CDN | CloudFront | fast public derivatives |
| Queue | Amazon SQS | async processing |
| Workers | Python worker service or Lambda | classification/moderation/media |
| Auth | Guest session + Cognito/provider abstraction | frictionless start + later accounts |
| Cloud runtime | ECS Fargate or Lambda for suitable jobs | AWS-first and scalable |
| IaC | Terraform | reproducible infrastructure |
| CI/CD | GitHub Actions | OSS-friendly |
| Monitoring | OpenTelemetry + CloudWatch; Sentry optional | app + infra visibility |
| Product analytics | PostHog or equivalent | funnels/retention |
| AI | provider-agnostic multimodal API | classification/moderation assistance |
| Image processing | Pillow/libvips | resizing/redaction/EXIF stripping |
| Duplicate image baseline | pHash + spatial/time proximity | cheap V1 duplicate detection |
| Embeddings later | pgvector | optional semantic/image similarity |
| Testing | Pytest + Playwright + Vitest | backend/frontend/E2E |
| API docs | OpenAPI generated from FastAPI | developer experience |

## 3. Frontend

Use Next.js with TypeScript, server-rendered public report/hotspot pages, and client components for maps/camera/upload.

### PWA
Phase 1 remains a normal website, but can later support installation using:
- manifest,
- icons,
- service worker,
- cached app shell,
- push notifications where supported.

PWA installation must never be mandatory.

## 4. Backend

FastAPI is recommended because CivicQuest needs Python-friendly image, AI, and geospatial tooling while still benefiting from typed API schemas and generated OpenAPI docs.

## 5. Database

PostgreSQL + PostGIS should be the system of record.

Do not introduce a second database simply because some entities are flexible; JSONB covers configuration/rule payloads well.

## 6. Maps

Preferred client renderer: MapLibre GL JS.

Keep tile/geocoding provider behind a configuration abstraction. Import Mumbai ward boundaries into PostGIS as versioned datasets.

## 7. Identity

Phase 1 is not login-first.

Guest:
- signed HTTP-only secure cookie,
- server-side guest identity,
- rate-limit state.

Registered:
- link guest account to Google/Apple/phone later.

## 8. AI

Phase 1 uses:
- category suggestion,
- severity suggestion,
- risky-content flagging,
- before/after assistance,
- moderator assistance.

Avoid identity recognition and automated punishment.

## 9. Duplicate detection

V1:
1. same/similar category,
2. nearby radius,
3. recent time window,
4. pHash similarity.

V2:
- embeddings,
- pgvector,
- semantic similarity.

## 10. Local development

Docker Compose services:

```text
web
api
worker
postgres-postgis
redis
minio (optional S3 emulator)
```

A contributor should be able to run the core stack with one command.
