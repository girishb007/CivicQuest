## Context

This is CQ-00 of the approved V1 delivery. See docs/DECISIONS.md and proposal.md.

## Goals / Non-Goals

Deliver approved delivery contract; no paid deployment or public launch.

## Decisions

Use typed domain services, PostgreSQL transactions, generated API contracts and provider interfaces from the approved architecture. Local synthetic fixtures stay clearly labeled. Test observable behavior, not internal implementation shape.

## Risks / Trade-offs

External credentials and reviewed civic datasets are unavailable → separate local acceptance from live release checks.
