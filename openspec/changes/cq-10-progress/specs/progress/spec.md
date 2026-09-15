## Purpose

Provide verified civic progress for the approved Mumbai civic participation workflows with verifiable local acceptance.

## ADDED Requirements

### Requirement: Shared ward outcome goals
Admins SHALL create and edit audited, idempotent ward targets with an explicit start/end period and draft/published/cancelled status. Public goal progress SHALL count eligible waste resolutions and completed, approved Civic Actions once per report/event. Personal XP rules SHALL remain separate.

#### Scenario: Unique and reversible shared outcomes
- **WHEN** multiple approved resolution proposals reference one public waste report and multiple verified participants complete one event
- **THEN** the goal counts one report outcome and one event outcome
- **AND** restriction/duplicate merging, event cancellation or loss of all verified participants removes the ineligible contribution on the next read
- **AND** replay and derived-data rebuild require no additional rewards or counter increments

#### Scenario: Explicit period and geography
- **WHEN** the goal is read
- **THEN** report outcomes use resolution acceptance time and Action outcomes use event end time, within the inclusive start/exclusive end period
- **AND** report coordinates must lie in the assigned ward, while events matching multiple current wards await geographic clarification instead of counting twice
- **AND** current source/ward availability and public visibility rules apply

#### Scenario: Publication and cancellation
- **WHEN** an admin publishes a goal
- **THEN** a guest can see its target and actual progress on Quests/ward pages with no extra XP
- **WHEN** the admin cancels it
- **THEN** it disappears from citizen goal listings but remains available to admins

### Requirement: Verified civic progress 1
The system SHALL deliver the following approved capability: implement ledger, reversals, caps, quests and badges.

#### Scenario: Validated delivery 1
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** XP invariants pass

### Requirement: Verified civic progress 2
The system SHALL deliver the following approved capability: implement profiles, civicdex, streaks and leaderboards.

#### Scenario: Validated delivery 2
- **WHEN** the capability is exercised using the approved local acceptance fixtures
- **THEN** rebuild and browser checks pass
