## Purpose

Provide reproducible local stack for the approved Mumbai civic participation workflows with verifiable local acceptance.

## ADDED Requirements

### Requirement: Reproducible local stack 1
The system SHALL deliver the following approved capability: create pinned web/api/worker toolchains and lockfiles.

#### Scenario: Validated delivery 1
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** dependency installation passes

### Requirement: Reproducible local stack 2
The system SHALL deliver the following approved capability: create compose and seed/start commands.

#### Scenario: Validated delivery 2
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** health checks pass on a clean database

