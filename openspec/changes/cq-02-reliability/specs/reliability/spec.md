## Purpose

Provide durable data and jobs for the approved Mumbai civic participation workflows with verifiable local acceptance.

## ADDED Requirements

### Requirement: Durable data and jobs 1
The system SHALL deliver the following approved capability: implement schema migrations and domain constraints.

#### Scenario: Validated delivery 1
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** PostgreSQL integration tests pass

### Requirement: Durable data and jobs 2
The system SHALL deliver the following approved capability: implement transactional outbox, receipts and retry/dlq.

#### Scenario: Validated delivery 2
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** crash and replay tests pass

