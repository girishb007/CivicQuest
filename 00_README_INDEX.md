# CivicQuest Engineering Planning Pack

**Phase:** Phase 1 web rollout  
**Launch geography:** Mumbai, India  
**Primary client:** Responsive website / installable PWA, not a native mobile app  
**Product goal:** Let users discover civic issues, report them quickly, upvote attention-worthy problems, identify responsibility, earn Civic XP, join civic actions, and share their impact.

This pack converts the CivicQuest product vision into an engineering plan that can be reviewed before implementation starts.

## Documents

1. `01_PHASE1_PRODUCT_SCOPE.md` — what Phase 1 will and will not build.
2. `02_HIGH_LEVEL_ARCHITECTURE.md` — system architecture, services, request flows, and Mermaid diagrams.
3. `03_DATA_MODEL_AND_SCHEMA.md` — core entities, relationships, schema, indexes, and retention.
4. `04_TECH_STACK.md` — recommended frontend, backend, data, cloud, maps, AI, and tooling.
5. `05_API_AND_SERVICE_DESIGN.md` — API domains, endpoints, request/response conventions, and service boundaries.
6. `06_GEOSPATIAL_AND_ACCOUNTABILITY.md` — ward detection, hotspot logic, BMC/authority mapping, and representative ownership.
7. `07_GAMIFICATION_XP_QUESTS.md` — Civic XP, levels, CivicDex, quests, leaderboards, and anti-gaming rules.
8. `08_TRUST_SAFETY_MODERATION.md` — moderation, verification, abuse prevention, appeals, and civic-catch safety.
9. `09_SECURITY_PRIVACY_AUTH.md` — guest-first identity, account conversion, security controls, media privacy, and authorization.
10. `10_INFRA_DEPLOYMENT_CICD.md` — AWS deployment, environments, CI/CD, background jobs, backups, and DR.
11. `11_OBSERVABILITY_ANALYTICS.md` — logs, metrics, tracing, product events, dashboards, and alerting.
12. `12_TESTING_STRATEGY.md` — unit, integration, E2E, geospatial, moderation, load, and accessibility testing.
13. `13_ROADMAP_AND_MILESTONES.md` — implementation order from foundation to Mumbai pilot.
14. `14_OPEN_SOURCE_REPO_STRUCTURE.md` — monorepo layout, contribution model, documentation, and OSS controls.
15. `15_DECISIONS_AND_OPEN_QUESTIONS.md` — decisions already made and items that must be resolved before launch.

## Phase 1 architecture principles

- **Web-first:** no App Store / Play Store download requirement.
- **Guest-first:** users can browse and begin participation before creating an account.
- **Fast path:** report creation should feel like a few-step flow, not a government form.
- **Geospatial first-class:** reports, wards, hotspots, and accountability depend on coordinates and polygons.
- **Public vs private media separation:** keep original evidence separately from public derivatives.
- **Async by default for heavy work:** classification, duplicates, moderation assistance, notifications, share cards, and hotspot recomputation should not block report submission.
- **Open-source friendly:** avoid unnecessary proprietary coupling; keep providers behind interfaces.
- **Policy before enforcement:** CivicQuest should not automatically punish a person based on an unverified report.
- **Reporting matters; fixing matters more:** Civic Actions and verified resolution earn more XP than passive engagement.

## Recommended implementation order

`scope → architecture → schema → repo → auth/session → maps/geospatial → reporting → media → feed/upvotes → hotspots/accountability → XP → civic actions → moderation → observability → pilot`
