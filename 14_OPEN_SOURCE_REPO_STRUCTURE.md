# CivicQuest Open-Source Repository Structure

## 1. Recommended monorepo

```text
civicquest/
├── apps/
│   ├── web/
│   ├── api/
│   └── worker/
├── packages/
│   ├── ui/
│   ├── contracts/
│   ├── civic-routing/
│   ├── gamification/
│   ├── geo-data/
│   └── config/
├── infrastructure/
│   ├── terraform/
│   └── docker/
├── data/
│   ├── samples/
│   └── schemas/
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── API.md
│   ├── GEOSPATIAL.md
│   ├── TRUST_AND_SAFETY.md
│   ├── SECURITY.md
│   ├── GAMIFICATION.md
│   └── ROADMAP.md
├── scripts/
│   ├── import_boundaries/
│   ├── seed/
│   └── dev/
├── tests/
│   ├── e2e/
│   └── fixtures/
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── AGENTS.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
├── README.md
└── docker-compose.yml
```

## 2. Branching

Recommended:
- `main` always releasable,
- short-lived feature branches,
- PRs required.

## 3. PR requirements

Include:
- purpose,
- screenshots for UI,
- tests,
- migration notes,
- privacy/safety impact when relevant.

## 4. Civic data contribution

Administrative-boundary/accountability changes require:
- source URL,
- source date,
- license,
- geographic scope,
- effective date,
- reviewer.

Do not accept unsourced authority/representative metadata.

## 5. Security

`SECURITY.md` should include private vulnerability-reporting instructions.

## 6. Labels

- good first issue
- frontend
- backend
- geospatial
- gamification
- trust-safety
- data
- accessibility
- documentation
- security

## 7. AGENTS.md rules

Coding agents should:
- read docs first,
- not bypass moderation/security,
- create DB migrations,
- add tests,
- never expose original media,
- not add identity-recognition features,
- preserve provider abstraction.

## 8. License

Decide after commercialization/open-source review.

Candidates:
- Apache-2.0,
- MIT,
- AGPL.
