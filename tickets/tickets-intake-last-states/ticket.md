---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
none

## Context
- clutch/tickets.py::intake
- clutch/status.py::last_states
- clutch/scheduler.py

## Goal / Why
`intake` in `clutch/tickets.py` builds its `states` map with a comprehension that is a verbatim copy of `clutch.status.last_states`. Two copies of the "latest run-state per stem" fold can drift; drain, scheduler, and rework already call `last_states`. After this change `intake` calls `last_states(journal.read())` and the copy is gone, so the fold has one definition.

`clutch/status.py` imports `clutch.tickets` at module level (`from clutch.tickets import INTAKE_SIGNAL`), so a module-level import of `clutch.status` in `clutch/tickets.py` would be circular. The repo already breaks such cycles with a function-local import (for example `from clutch.rework import settled_dependencies, supersedes_maps` inside a function in `clutch/scheduler.py`); `intake` does the same.

## Scope in / Scope out
- In: in `clutch/tickets.py` `intake`, replace the `states = {...}` comprehension with a function-local `from clutch.status import last_states` and `states = last_states(journal.read())`. The set of settled states checked against `states` stays as is.
- Out: moving `last_states` out of `clutch/status.py`; any other caller of `last_states`; the settled-state set literal in `intake`; tests (`tests/integration/test_tickets.py::test_settled_bug_is_not_rejudged_for_evidence` already covers the journal-state exemption and `test_bug_without_evidence_refused_at_intake` covers the non-exempt path).

## Scope fence
- clutch/tickets.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_tickets.py -k "settled_bug_is_not_rejudged_for_evidence or bug_without_evidence_refused_at_intake"` exits 0: a `confirmed` bug whose journal's last transition is `merged`, `already_satisfied`, or `rejected` is committed, not refused for missing evidence, and a bug with no evidence and no settled journal state is still refused.
2. `clutch/tickets.py` contains no `e.body["to"]` comprehension over `journal.read()`, and `intake` calls `last_states`.
3. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_tickets.py -k "settled_bug_is_not_rejudged_for_evidence or bug_without_evidence_refused_at_intake"
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `last_states` is moved out of `clutch/status.py` or a second copy of it is defined anywhere;
- `clutch/tickets.py` imports `clutch.status` at module level;
- any file outside `clutch/tickets.py` changes.

## Time budget
- expected: 10m
- stuck: 30m
