## Purpose

Provide guest identity and account linking for the approved Mumbai civic participation workflows with verifiable local acceptance.

## ADDED Requirements

### Requirement: Guest identity and account linking 1
The system SHALL deliver the following approved capability: implement sessions, csrf, role authorization and google adapter.

#### Scenario: Validated delivery 1
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** auth tests pass

### Requirement: Guest identity and account linking 2
The system SHALL deliver the following approved capability: preserve guest history on new/existing account claims.

#### Scenario: Validated delivery 2
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** merge/deduplication tests pass

