---
state: draft
source: box:suggestion
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Runs before
- roadmap-release-audit-last

## Context
- clutch/roadmap.py::author_ahead
- clutch/roadmap.py::choose
- tests/unit/test_roadmap_refile.py
- tests/unit/test_roadmap_author.py

## Goal / Why
After this ticket, `author_ahead` re-files a rejected roadmap row only when every stem in the row's Depends on is done, by the same test `choose` applies. A rejected row with an unmerged dependency is left as it is. It gets no new stem, no roadmap row rewrite and no `roadmap_row` message, and the output has a `waits:` line that names the unmerged dependency.

Today the re-file loop checks only the held release and the re-file cap. On 2026-11-17 the supervising session rejected `release-audit-040` so that its row would wait for its 0.4.0 dependencies. The driver re-filed it as `release-audit-040-r1` at once, and the audit ran while its release was still open. Operator rejection is the only way to park a row, so the re-file loop has to respect the park.

The fix reuses one dependency predicate in both `choose` and the re-file loop. It does not copy the predicate. It does not change when `choose` makes an audit row ready, which `roadmap-release-audit-last` owns. It does not change how Author handles Depends on stems that have no ticket yet. Neither is in scope here.

## Boundary contract
### Roadmap re-file readiness
- disposition: extend
- owner: clutch/roadmap.py
- consumers: `clutch roadmap author`, the roadmap driver (callers of `author_ahead`)
- observable change: a rejected row whose Depends on names a stem that is not done is skipped by the re-file loop. The output gains `roadmap: row N STEM waits: <reason naming the dependency> -- <road>`. Rows with all dependencies done re-file exactly as before.
- compatibility: the re-file cap, held-release skip, stem numbering, reason text and message summary are unchanged. `choose` returns the same Choice for every input; the predicate is only moved into a helper.
- acceptance: a rejected row with an unsettled dependency produces no write and no message and gets a wait line. With the dependency settled it re-files.
- tests: new unit test file for `author_ahead` re-file readiness
- post-merge source of truth: clutch/roadmap.py

## Scope in / Scope out
Scope in: in `clutch/roadmap.py`, move the dependency-done test now inline in `choose` into one helper that `choose` and the rejected-row loop in `author_ahead` both call. In the loop, call `depends_on(row, rows)` and the helper before the re-file cap check. When a dependency is not done, append a `waits:` line that names the dependency and a road (wait for the dependency to merge, or edit the Depends on cell), then `continue`. When `depends_on` raises ValueError, append a wait line with the error text and `continue`. A stem counts as done when it was struck in this pass or is struck in the table, and for stems outside the table when its journal state is settled, exactly as `choose` has it today. Add the tests in a new file.

Scope out: `choose` readiness behaviour, audit-row ordering, Author's handling of Depends on stems with no ticket, and the re-file cap logic. The driver docs describe the re-file loop only in general terms, so no document changes.

## Scope fence
- clutch/roadmap.py
- tests/unit/test_roadmap_refile_ready.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_roadmap_refile_ready.py` has a test that runs `author_ahead` on a rejected row whose Depends on names an unsettled stem. It asserts the roadmap file bytes are unchanged, `box.messages()` holds no `roadmap_row` message, and the returned lines contain a `waits:` line containing that dependency stem. The old behaviour fails it: it re-files the row under a `-r1` stem.
2. The same test file has a case where the dependency is settled in the journal. It asserts the rejected row is re-filed under the `-rN` stem, not skipped.
3. The same test file has a case with a malformed Depends on cell on a rejected row. It asserts a `waits:` line and no row rewrite, not an uncaught ValueError.
4. `./dev.py test tests/unit/test_roadmap_refile.py tests/unit/test_roadmap_author.py tests/integration/test_roadmap_refile.py tests/integration/test_roadmap_start_gates.py` passes unchanged. A moved `choose` predicate that changes any of these results fails them.

## Verification
```
./dev.py test tests/unit/test_roadmap_refile_ready.py tests/unit/test_roadmap_refile.py tests/unit/test_roadmap_author.py tests/integration/test_roadmap_refile.py tests/integration/test_roadmap_start_gates.py
```

## Definition of rejected
The branch is thrown away if the re-file loop keeps its own copy of the dependency test instead of sharing one helper with `choose`. It is also thrown away if a rejected row with an unmerged dependency still gets a new stem or a `roadmap_row` message, or if any existing re-file test is edited to pass.

## Time budget
- expected: 15m
- stuck: 30m
