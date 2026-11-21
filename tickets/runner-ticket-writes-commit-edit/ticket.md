---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- git-commit-edit-owner

## Runs before
- ticket-write-serialization-proof

## Context
- clutch/git.py::Git
- clutch/lockfile.py::CommitLock
- clutch/tickets.py::intake
- clutch/runner.py::verdict_locked
- clutch/runner.py::reject_ticket
- clutch/runner.py::apply_admission

## Goal / Why
Move the runner's ticket state writers onto Git.commit_edit, so confirm, reject and admission replay repair can no longer stamp ticket.md before they take the commit lock. This is part of the split ticket-writes-atomic-commit: a concurrent intake must never stage another writer's intermediate stamp. That is required before Serve can stop waiting for run lifetimes.

## Boundary contract
### Atomic engine ticket edit and commit
- disposition: reuse
- owner: clutch/git.py::Git.commit_edit
- consumers: runner.verdict_locked draft confirmation, runner.reject_ticket, and the replay-repair commit in runner.apply_admission
- observable change: each consumer performs its final read/stamp/write and exact-path commit inside one commit_edit callback
- compatibility: commit messages, exact-path staging, journal and effect keys, refusal precedence and request replay are unchanged
- acceptance: no runner writer changes ticket bytes before it holds main_write and commit.lock
- tests: tests/unit/test_ticket_write_consumers_runner.py
- post-merge source of truth: clutch/git.py::Git.commit_edit

## Scope in / Scope out
Scope in:
- Move the actual read/stamp/write and commit steps of runner.verdict_locked draft confirmation, runner.reject_ticket and the apply_admission replay-repair commit onto commit_edit. Put the state revalidation the edit needs inside the callback and keep refusal precedence. Do not wrap the whole verdict_locked function around intake, because intake already takes commit.lock.
- Callbacks use only filesystem reads/writes/removes and read-only _run/rev_parse.
- Migrate the hand-built Git fixture in tests/unit/test_verdict_menu_parity.py to implement commit_edit explicitly, and keep its verdict admission expectations. Change the verdict fakes in tests/unit/test_verdict_extension.py and tests/unit/test_reject_reason_paths.py only where they reach commit_edit. Add no getattr fallback or default fake method to production code.
- Add event-controlled, fake-driven unit tests in tests/unit/test_ticket_write_consumers_runner.py. They prove that each migrated branch writes only inside the callback.
- In the run record, list each runner ticket.md stamp/write/commit site and name the owner that covers it.
Scope out:
- Do not touch Author, triage, Rework or Serve's run exclusion. Do not change scheduler, merge or command semantics.

## Scope fence
- clutch/runner.py
- tests/unit/test_ticket_write_consumers_runner.py
- tests/unit/test_verdict_menu_parity.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_reject_reason_paths.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_ticket_write_consumers_runner.py` proves that confirm, reject and admission replay repair each change ticket bytes only inside the commit_edit callback, and that refusal precedence is preserved.
2. `./dev.py test tests/unit/test_verdict_menu_parity.py tests/unit/test_verdict_extension.py tests/unit/test_reject_reason_paths.py` preserves verdict, refusal and reason forwarding through the migrated API.

## Verification
```
./dev.py test tests/unit/test_ticket_write_consumers_runner.py tests/unit/test_verdict_menu_parity.py tests/unit/test_verdict_extension.py tests/unit/test_reject_reason_paths.py tests/unit/test_commit_lock.py
```

## Definition of rejected
A runner state writer still changes bytes before it takes shared ownership; verdict_locked wraps intake inside the lock; recursive lock acquisition is introduced; or unrelated user changes are staged.

## Time budget
- expected: 30m
- stuck: 60m