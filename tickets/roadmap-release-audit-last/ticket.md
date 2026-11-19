---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::choose
- clutch/roadmap.py::Row
- clutch/roadmap.py::release_name
- tests/unit/test_roadmap_release_boundary.py

## Goal / Why
A release's audit row becomes ready only after every other row of its release is merged or struck. Today `choose` decides readiness only from `depends_on(row, rows)`. On 2026-11-17 `release-audit-040` (row 122) had an empty Depends on, so the driver authored it as soon as 0.4.0 opened and intake auto-confirmed it while 18 rows were still open. The audit would have recorded the docs mid-release. Each release ends with an audit row (row 105 for 0.3.0, row 122 for 0.4.0, a 0.5.0 row to come). A hand-written Depends on list goes stale whenever a row joins the release. The rule removes that list.

The audit row of a release is the row whose stem, after dropping any `-r<N>` re-file suffix, is `release-audit-` followed by `release_name(row.release)` with the dots removed (release `0.4.0` gives `release-audit-040`; release `0.5.0` gives `release-audit-050`).

## Boundary contract
### Roadmap row readiness
- disposition: extend
- owner: clutch/roadmap.py::choose
- consumers: the roadmap driver and `roadmap status`, which both call `choose`
- observable change: an audit row not yet linked or authored, whose dependencies are met, becomes a Wait with reason `release <release> has <n> open rows` and road `merge or strike the other rows of the release` while any other row of its release is neither struck nor in the strike list. When none remain, it is ready as before. Other rows are unchanged.
- compatibility: rows that are not audit rows, and audit rows already linked, authored, or in the journal, take the same paths as today and are counted as open rows for their siblings as today. An audit row with explicit Depends on entries still honors them first: the dependency check runs before the release hold, and a row with an unmet dependency stays in neither `ready` nor `waits`, as today.
- acceptance: the unit tests below
- tests: tests/unit/test_roadmap_release_audit_order.py
- post-merge source of truth: clutch/roadmap.py::choose

## Scope in / Scope out
In: one readiness rule in `choose`, applied after the dependency check and before the kind, priority, plan and evidence checks, with a small private helper that recognizes the audit stem from the row's own release. A new unit test file builds roadmap tables with `parse`.
Out: editing `docs/roadmap.md` rows, adding a 0.5.0 audit row, changing `depends_on`, the Row schema, or any other `choose` rule, and prose docs.

## Scope fence
- clutch/roadmap.py
- tests/unit/test_roadmap_release_audit_order.py

## Acceptance criteria
1. With a table holding an audit row `release-audit-040` with an empty Depends on and one open sibling row of the same release, `choose(...)` in `test_audit_waits_while_sibling_open` returns a Wait for the audit row and the audit row is not in `ready`, not ready.
2. When every sibling is struck, `test_audit_ready_when_siblings_struck` shows the audit row in `ready` with no Wait for it.
3. When a sibling is not struck but its stem is settled in `states` (merged), `test_audit_ready_when_siblings_settled` shows the audit row in `ready`.
4. A sibling in a different release does not hold the audit row: `test_other_release_does_not_block` shows the audit row ready, not waiting.
5. The re-file stem `release-audit-040-r1` is held the same way as `release-audit-040`: `test_refile_stem_is_audit_row` shows a Wait, not ready.
6. A non-audit row with an empty Depends on and open siblings stays ready: `test_ordinary_row_unaffected` shows it in `ready`, not in waits.
7. The audit stem follows the row's release, not a literal: `test_audit_stem_follows_release` with a `### 0.5.0` release holding `release-audit-050` and one open sibling shows a Wait for `release-audit-050`, and `release-audit-040` placed under 0.5.0 is not treated as that release's audit row and is in `ready`, not waiting.
8. A linked audit row is unaffected: in `test_linked_audit_row_unaffected`, a linked `release-audit-040` row with an open sibling is counted in the open-rows count and has no release-hold Wait, not a Wait.
9. Dependencies are checked first: in `test_audit_depends_checked_first`, an audit row whose Depends on names an unmerged row, with an open sibling in its release, is in neither `ready` nor `waits`, so it has no release-hold Wait and no Wait at all; once that dependency is settled in `states` and the sibling is still open, the same row has the release-hold Wait and is not in `ready`.
10. The existing tests still pass: `./dev.py test tests/unit/test_roadmap_release_boundary.py tests/unit/test_roadmap_drive.py tests/integration/test_roadmap_table.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_release_audit_order.py tests/unit/test_roadmap_release_boundary.py tests/unit/test_roadmap_drive.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
The rule keys on a row number or on a hardcoded release. Any non-audit row's readiness changes. The audit row can be ready while a sibling of its release is open. A linked or authored audit row is held, or the release hold runs before the dependency check.

## Time budget
- expected: 15m
- stuck: 30m
