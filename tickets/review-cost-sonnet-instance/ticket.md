---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- config.yaml
- clutch/providers.py::_route
- clutch/providers.py::resolve
- clutch/config.py::Route
- tests/integration/test_config.py

## Goal / Why
Stop the current instance of routine ticket buildability reviews inheriting the Opus-pinned review route in this repository. The November 21 owner audit measured 779 matched review invocations across 245 stems since November 18, with about 41% of weighted Claude demand in requisition_review. Add explicit Sonnet routes for low and medium requisition_review while preserving high and max review capability. This is the minimal instance correction; shipped subagent policy and repeated-review/context changes are separate tickets.

## Boundary contract
### Repository model routing
- disposition: extend
- owner: config.yaml
- consumers: clutch/providers.py::resolve and requisition_review callers
- observable change: low and medium requisition_review select the declared Claude provider and claude-sonnet-5-5 instead of falling back to the Opus-pinned review row; high and max still resolve to Opus.
- compatibility: no schema, CLI, provider identity, Implement ladder, Author route, or implemented-diff review route changes.
- acceptance: a real configuration load and resolution proves the four requisition_review tiers and preservation of the existing Implement and review routes.
- tests: tests/integration/test_repo_requisition_sonnet.py
- post-merge source of truth: config.yaml and clutch/providers.py::_route

## Scope in / Scope out
Scope in:
- Add explicit low and medium requisition_review rows selecting claude-sonnet-5-5 in config.yaml; preserve every existing route and provider declaration.
- Add a new integration test loading this repository's config through a Path(__file__) anchor and resolving all four tiers; assert the two new selections and unchanged high/max requisition_review, implemented-diff review and Implement routes.
Scope out:
- No provider calls, package updates, global Claude settings, other host checkout edits, supervisor restarts, or engine changes.

## Scope fence
- config.yaml
- tests/integration/test_repo_requisition_sonnet.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_repo_requisition_sonnet.py` proves low and medium requisition_review resolve to claude-sonnet-5-5 rather than claude-opus-5-5.
2. `./dev.py test tests/integration/test_repo_requisition_sonnet.py` proves high and max requisition_review retain Opus and all existing Implement and implemented-diff review selections remain unchanged.

## Verification
```
./dev.py test tests/integration/test_repo_requisition_sonnet.py
```

## Definition of rejected
The change weakens the implemented-diff review route, changes the Codex Implement ladder, mutates another checkout, or changes routing code or configuration schema.

## Time budget
- expected: 5m
- stuck: 10m
