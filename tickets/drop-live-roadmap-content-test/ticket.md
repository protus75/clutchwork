---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
none

## Context
- tests/integration/test_roadmap_release_audit.py
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks
- clutch/roadmap.py

## Goal / Why
Main is red. `tests/integration/test_roadmap_release_audit.py::test_release_audit_row_and_gates`, merged with `release-audit-030`, asserts the current content of the live roadmap: that row 122 `release-audit-040` is the last, unstruck row of the 0.4.0 table, the exact commands of the 0.3.0 and 0.4.0 gate blocks, and two phrases of section 9. The driver and `clutch roadmap accept` rewrite that content in normal operation. On 2026-11-17 `roadmap accept 0.3.0` (commit 511967cd) deferred rows 125-127 into the 0.4.0 table after row 122, as it is designed to, and the test has failed on main since then (box-000669, box-000673), so the release gate's `./dev.py test` cannot pass and 0.3.0 cannot ship. The test's other assertions break the same way the next time the driver strikes row 122 or the audit edits section 9. The owner ruled on 2026-11-16 that tests pinning roadmap content are gold plating; the one standing check that matters, that every gate block parses and runs valid commands, is `tests/integration/test_roadmap_gate.py`. After this change the file is gone and the suite passes on main.

## Scope in / Scope out
In: delete `tests/integration/test_roadmap_release_audit.py`.

Out: every other file, including `tests/integration/test_roadmap_gate.py`, the roadmap document, and the release audit row.

## Scope fence
- tests/integration/test_roadmap_release_audit.py

## Acceptance criteria
1. `tests/integration/test_roadmap_release_audit.py` does not exist on the branch, checked by `test ! -e tests/integration/test_roadmap_release_audit.py`.
2. `./dev.py test tests/integration` exits 0 on the branch, so no other test depended on the deleted file.

## Verification
```
./dev.py test tests/integration
```

## Definition of rejected
The branch is rejected if it changes any file other than deleting `tests/integration/test_roadmap_release_audit.py`, edits `docs/roadmap.md` to make the old test pass, or weakens another test.

## Time budget
- expected: 10m
- stuck: 20m
