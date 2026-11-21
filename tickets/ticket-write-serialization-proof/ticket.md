---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- runner-ticket-writes-commit-edit
- author-ticket-writes-commit-edit
- rework-ticket-writes-commit-edit

## Runs before
- serve-confirm-during-check

## Context
- clutch/git.py::Git
- clutch/lockfile.py::CommitLock
- clutch/tickets.py::intake
- clutch/runner.py::verdict_locked
- clutch/author.py::author
- clutch/daemon.py::apply_rework
- tests/integration/test_tickets.py

## Goal / Why
Use real flock and real Git to prove that engine ticket writes are serialized end to end, and document the narrow ticket-write critical section. This is the last part of the split ticket-writes-atomic-commit. The paired serve-confirm-during-check ticket may remove Serve's coarse run barrier only after this proof shows that intake cannot adopt another writer's intermediate stamp.

## Boundary contract
### Atomic engine ticket edit and commit
- disposition: reuse
- owner: clutch/git.py::Git.commit_edit and existing commit.lock
- consumers: intake, runner confirm/reject/admission repair, Author publication and decision records, and Rework publication and compensation
- observable change: none in code. The integration tests and the how-clutch-works section describe the critical section that already exists.
- compatibility: merge squash serialization through the commit lock is unchanged, and no run-lifetime lock is added
- acceptance: races between intake and each writer commit exact bytes without adopting an intermediate stamp
- tests: tests/integration/test_ticket_write_serialization.py
- post-merge source of truth: clutch/git.py::Git.commit_edit

## Scope in / Scope out
Scope in:
- Add integration tests that race intake against confirm, reject, Author and Rework writes using real flock and a real Git repository built under tmp_path. Assert exact committed bytes, no adoption of another writer's intermediate stamp, lock release on failure, unchanged request replay, model and check work running outside the write lock, and preserved merge squash serialization.
- In docs/how-clutch-works.md section 10.2 The journal, document the narrow ticket-write critical section, its lock order (main_write before commit.lock) and its callback restrictions.
Scope out:
- Make no production code change. A defect these tests find goes to the Suggestion Box. Leave Serve's coarse run exclusion unchanged; removing it belongs to serve-confirm-during-check.

## Scope fence
- tests/integration/test_ticket_write_serialization.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/integration/test_ticket_write_serialization.py` proves the following: intake cannot commit an intermediate stamp from confirm, reject, Author or Rework; committed bytes are exact; locks are released on failure; request replay is unchanged.
2. `./dev.py test tests/integration/test_ticket_write_serialization.py` proves that model and check work run outside the narrow write lock, that existing merge squash and commit-lock serialization is preserved, and that there is no run-lifetime lock.

## Verification
```
./dev.py test tests/integration/test_ticket_write_serialization.py tests/integration/test_tickets.py tests/unit/test_commit_lock.py
```

## Definition of rejected
A production code change, a new Serve-only lock or run-lifetime lock, or tests that read the checkout's tickets/, .clutch/ or journal instead of a tmp_path repository.

## Time budget
- expected: 30m
- stuck: 60m