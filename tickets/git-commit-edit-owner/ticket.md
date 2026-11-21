---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Runs before
- runner-ticket-writes-commit-edit
- author-ticket-writes-commit-edit
- rework-ticket-writes-commit-edit

## Context
- clutch/lockfile.py::CommitLock
- clutch/tickets.py::intake
- tests/unit/test_commit_lock.py
- tests/integration/test_tickets.py
- tickets/serve-verdicts-wait-for-runs/ticket.md

## Goal / Why
Add the one shared owner for engine ticket-file edits and their commits, and put intake under the same lock order. The serve-verdicts-wait-for-runs ticket was rejected on November 21 because runner, Author and Rework stamp/write ticket files before they take the commit lock, so confirmation still waits behind unrelated runs (183 seconds observed). This ticket is the first part of the split ticket-writes-atomic-commit: it adds Git.commit_edit and the intake lock order. Sibling tickets move each writer onto it. The original ticket was too large for one attempt: attempt 2 stopped incomplete after editing six engine modules and about 17 test files.

## Boundary contract
### Atomic engine ticket edit and commit
- disposition: extend
- owner: clutch/git.py::Git and clutch/lockfile.py::CommitLock
- consumers: tickets.intake now; runner, Author, triage decision records and daemon.apply_rework migrate in sibling tickets
- observable change: add async Git.commit_edit(dir, message, *, only, edit) -> str. only is a nonempty sequence of exact paths. edit is an async no-argument callback for file reads/writes and read-only Git validation. The helper takes Git.main_write first and the existing commit lock second, awaits edit, then calls _commit directly while both locks are held. Both locks are released on success, exception and cancellation. intake takes main_write and then commit.lock around its existing commit-lock body.
- compatibility: Git.commit, merge_squash, add and restore are unchanged. CommitLock stays non-reentrant. Intake commit messages, exact-path staging and refusal behavior are unchanged.
- acceptance: the edit runs before an exact-path _commit while both locks are held; a competing commit_edit or intake is excluded; exceptions and cancellation release both locks
- tests: tests/unit/test_git_commit_edit.py and tests/unit/test_intake_lock_order.py
- post-merge source of truth: clutch/git.py::Git.commit_edit and existing commit.lock

## Scope in / Scope out
Scope in:
- Implement Git.commit_edit using the existing process, filesystem and lock seams. Add no new lockfile, reentrant lock, transaction journal, worker pool or generic mutation framework. Keep the lock order main_write before commit.lock. Never call Git.commit from inside the helper, because Git.commit takes the non-reentrant lock again. In the helper's docstring, state that the callback must not call a lock-taking Git writer, invoke a model or run checks.
- In clutch/tickets.py::intake, wrap the existing entire `async with git._commit_lock` body in `async with git.main_write()`. Do not nest the new helper inside intake. Merge squash already takes main_write and then commit.lock, and stays unchanged.
- The hand-built Git stand-ins in tests/unit/test_git_commit.py (around lines 82 and 124), tests/unit/test_intake_plan.py (FakeGit, around line 27) and tests/unit/test_menu_admission.py (around line 262) define _commit_lock but not main_write. Give each one a fake main_write async context manager and keep its assertions unchanged.
- Unit tests use in-memory fake locks and fake process exec, not real fcntl. Add an event-controlled test of intake lock order in tests/unit/test_intake_lock_order.py.
Scope out:
- Do not migrate any runner, Author, triage or Rework writer; the sibling tickets do that. Do not change scheduler parallelism, merge code, Serve's run exclusion or lock timeouts. The narrative documentation update belongs to the sibling ticket-write-serialization-proof.

## Scope fence
- clutch/git.py
- clutch/tickets.py
- tests/unit/test_git_commit_edit.py
- tests/unit/test_intake_lock_order.py
- tests/unit/test_git_commit.py
- tests/unit/test_intake_plan.py
- tests/unit/test_menu_admission.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_git_commit_edit.py` proves that the edit runs before an exact-path _commit while main_write and commit.lock are held, that competing tasks are excluded, that lock order is fixed, and that exceptions and cancellation release both locks without making CommitLock reentrant.
2. `./dev.py test tests/unit/test_intake_lock_order.py` proves that intake takes main_write before commit.lock and holds both across its status, read, validation, stamp and _commit steps.
3. `./dev.py test tests/unit/test_git_commit.py tests/unit/test_intake_plan.py tests/unit/test_menu_admission.py tests/unit/test_commit_lock.py tests/integration/test_tickets.py` passes with the existing assertions unchanged.

## Verification
```
./dev.py test tests/unit/test_git_commit_edit.py tests/unit/test_intake_lock_order.py tests/unit/test_git_commit.py tests/unit/test_intake_plan.py tests/unit/test_menu_admission.py tests/unit/test_commit_lock.py tests/integration/test_tickets.py
```

## Definition of rejected
A new lockfile, Serve-only lock or reentrant lock is added; the helper calls Git.commit or takes either lock recursively; the lock order differs from main_write before commit.lock; or a lock stays held after an exception or cancellation.

## Time budget
- expected: 30m
- stuck: 60m