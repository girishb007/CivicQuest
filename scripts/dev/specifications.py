"""Materialize the approved work breakdown; never mark unverified work complete."""
from pathlib import Path

chunks = [
('specifications', 'Approved delivery contract', ['Record approved decisions and acceptance matrix; inspect docs/DECISIONS.md', 'Validate all OpenSpec change artifacts with openspec validate --all --strict']),
('foundation', 'Reproducible local stack', ['Create pinned web/API/worker toolchains and lockfiles; dependency installation passes', 'Create Compose and seed/start commands; health checks pass on a clean database']),
('reliability', 'Durable data and jobs', ['Implement schema migrations and domain constraints; PostgreSQL integration tests pass', 'Implement transactional outbox, receipts and retry/DLQ; crash and replay tests pass']),
('identity', 'Guest identity and account linking', ['Implement sessions, CSRF, role authorization and Google adapter; auth tests pass', 'Preserve guest history on new/existing account claims; merge/deduplication tests pass']),
('web-shell', 'Accessible responsive navigation', ['Implement light visual system and all five navigation sections; typecheck passes', 'Provide keyboard/touch and loading/error states; browser accessibility checks pass']),
('geospatial', 'Mumbai discovery and accountability', ['Implement sourced boundary import and ambiguous ownership; PostGIS edge tests pass', 'Implement map, viewport, search and list fallback; browser exploration tests pass']),
('media', 'Private evidence and safe derivatives', ['Implement signed upload, completion and validated transformation; media security tests pass', 'Implement classification/safety adapters and duplicate candidates; fail-closed tests pass']),
('reporting', 'Guest capture to publication', ['Implement draft/review/finalize/status/history; reporting integration test passes', 'Enforce low-risk publication and Civic Catch gates; visibility tests pass']),
('attention', 'Public feeds and hotspots', ['Implement feeds, votes and deterministic hotspots; voting and clustering tests pass', 'Implement public report/hotspot details and safe history; browser tests pass']),
('trust', 'Verification resolution and appeals', ['Implement verification quorum, disputes and resolution proof; transition tests pass', 'Implement moderator review/redaction/abuse/appeals/duplicates; security and audit tests pass']),
('progress', 'Verified civic progress', ['Implement ledger, reversals, caps, quests and badges; XP invariants pass', 'Implement profiles, CivicDex, streaks and leaderboards; rebuild and browser checks pass']),
('actions', 'Admin-managed civic actions', ['Implement admin event CRUD, join/capacity/check-in; geofence and replay tests pass', 'Implement before/after evidence, approval and rewards; complete action journey passes']),
('sharing', 'Sharing notifications and PWA', ['Implement three share cards, safe invalidation and Web Share; sharing tests pass', 'Implement inbox, opt-in push and shell-only PWA cache; notification/browser tests pass']),
('operations', 'Deployment and recovery', ['Implement Terraform, release workflows and telemetry; static infrastructure validation passes', 'Implement retention, deletion, backup/restore and rebuild commands; local recovery drill passes']),
('acceptance', 'End-to-end release evidence', ['Run integrated local tests, accessibility, browser and 100k-report load checks; record actual results', 'Document contributor/admin runbooks and outstanding live-provider/phone/data gates; review release checklist']),
]
for i,(slug,title,tasks) in enumerate(chunks):
    name=f'cq-{i:02d}-{slug}'
    p=Path('openspec/changes')/name
    p.mkdir(parents=True,exist_ok=True)
    (p/'.openspec.yaml').write_text('schema: spec-driven\ncreated: 2026-09-11\n')
    (p/'proposal.md').write_text(f'## Why\n\nDeliver {title.lower()} as part of the user-approved CivicQuest V1 implementation.\n\n## What Changes\n\n'+''.join(f'- {t}\n' for t in tasks)+f'\n## Capabilities\n\n### New Capabilities\n- `{slug}`: {title}.\n\n### Modified Capabilities\n\nNone.\n\n## Impact\n\nLocal web/API/worker, contracts and checks. Depends on CQ-{max(0,i-1):02d}. See docs/DECISIONS.md.\n')
    (p/'design.md').write_text(f'## Context\n\nThis is CQ-{i:02d} of the approved V1 delivery. See docs/DECISIONS.md and proposal.md.\n\n## Goals / Non-Goals\n\nDeliver {title.lower()}; no paid deployment or public launch.\n\n## Decisions\n\nUse typed domain services, PostgreSQL transactions, generated API contracts and provider interfaces from the approved architecture. Local synthetic fixtures stay clearly labeled. Test observable behavior, not internal implementation shape.\n\n## Risks / Trade-offs\n\nExternal credentials and reviewed civic datasets are unavailable → separate local acceptance from live release checks.\n')
    s=p/'specs'/slug
    s.mkdir(parents=True,exist_ok=True)
    (s/'spec.md').write_text(f'## Purpose\n\nProvide {title.lower()} for the approved Mumbai civic participation workflows with verifiable local acceptance.\n\n## ADDED Requirements\n\n'+''.join(f'### Requirement: {title} {j}\nThe system SHALL deliver the following approved capability: {t.split(";")[0].lower()}.\n\n#### Scenario: Validated delivery {j}\n- **WHEN** the capability is exercised using the approved local acceptance fixtures\n- **THEN** {t.split(";")[-1].strip()}\n\n' for j,t in enumerate(tasks,1)))
    (p/'tasks.md').write_text('## 1. Implementation and verification\n\n'+''.join(f'- [ ] 1.{j} {t}\n' for j,t in enumerate(tasks,1)))
Path('docs/IMPLEMENTATION_STATUS.md').write_text('# V1 implementation status\n\nCheck boxes are evidence-based. Incomplete work remains open.\n\n| Chunk | Capability | Acceptance record |\n|---|---|---|\n'+''.join(f'| CQ-{i:02d} | {title} | [Tasks](../openspec/changes/cq-{i:02d}-{slug}/tasks.md) |\n' for i,(slug,title,_) in enumerate(chunks)))
