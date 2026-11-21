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
- requisition-review-input-reuse

## Context
- clutch/git.py::Git
- clutch/lockfile.py::CommitLock
- clutch/daemon.py::apply_rework
- tests/integration/test_rework.py

## Goal / Why
Move daemon.apply_rework publication and compensation onto Git.commit_edit, so Rework no longer writes ticket files before it takes the commit lock and its compensation never undoes another writer's later edit. This is part of the split ticket-writes-atomic-commit, which serializes all engine ticket writes so Serve can stop waiting for run lifetimes.

## Boundary contract
### Atomic engine ticket edit and commit
- disposition: reuse
- owner: clutch/git.py::Git.commit_edit
- consumers: publish() and restore_publication() in daemon.apply_rework
- observable change: publication writes and commits inside one commit_edit callback. Compensation replaces the existing add/restore/commit sequence with one commit_edit call. Its callback restores the pre-publication bytes, or removes an owned new file, only when the current bytes still equal this publication's output.
- compatibility: commit messages, effect keys, the partial-publication and refusal behavior, and the review identity wrapper are unchanged
- acceptance: Rework changes no bytes before it holds main_write and commit.lock, and compensation keeps another writer's later bytes
- tests: tests/unit/test_ticket_write_consumers_rework.py
- post-merge source of truth: clutch/git.py::Git.commit_edit

## Scope in / Scope out
Scope in:
- Callbacks use only filesystem reads/writes/removes and read-only _run/rev_parse. Never call add, restore or commit inside a callback. Ignore only NothingToCommit when restoration leaves no Git delta.
- Add test_callback_never_reenters_writer_lock to tests/unit/test_ticket_write_consumers_rework.py. It uses a non-reentrant fake lock that raises on recursive acquire, and exercises success, partial publication and compensation.
- In tests/unit/test_supervise_idle_point.py (around line 215), replace the ctx.git.commit stub on the Rework publication path with a commit_edit stub that awaits the callback, so the test fails if publication is refused. Keep its assertions.
- tests/unit/test_key_scope.py::test_apply_rework_scoped_publication (around line 118) runs the real daemon.apply_rework with a SimpleNamespace git that supplies only _run, rev_parse and commit. Give that stand-in a commit_edit fake that awaits the edit callback and returns "sha", and change its `git.commit.await_count == 2` assertion to the commit_edit await count (2). Keep its key and scope assertions unchanged. Add no getattr fallback in production code.
- Update the Rework commit-failure hooks in tests/integration/test_ladder.py, tests/integration/test_drain.py and tests/integration/test_daemon_composition.py to intercept commit_edit or _commit as appropriate. Keep their partial-publication and refusal assertions. In the two hot files, change only the existing failure hooks this forces; add no test, fixture or helper there.
- In the run record, list each Rework write site and name the owner that covers it.
Scope out:
- Do not touch runner, Author, triage, review_candidate provenance or Serve's run exclusion. tests/integration/test_rework.py calls the real Git.commit and stays unchanged.

## Scope fence
- clutch/daemon.py
- tests/unit/test_ticket_write_consumers_rework.py
- tests/unit/test_supervise_idle_point.py
- tests/unit/test_key_scope.py
- tests/integration/test_ladder.py
- tests/integration/test_drain.py
- tests/integration/test_daemon_composition.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_ticket_write_consumers_rework.py` proves the following: Rework publication and compensation change bytes only inside commit_edit; compensation keeps a later legitimate edit; no callback takes a writer lock again.
2. `./dev.py test tests/unit/test_supervise_idle_point.py tests/unit/test_key_scope.py tests/integration/test_ladder.py tests/integration/test_drain.py tests/integration/test_daemon_composition.py tests/integration/test_rework.py` preserves the partial-publication, refusal, key-scope and recovery behavior.

## Verification
```
./dev.py test tests/unit/test_ticket_write_consumers_rework.py tests/unit/test_supervise_idle_point.py tests/unit/test_key_scope.py tests/integration/test_ladder.py tests/integration/test_drain.py tests/integration/test_daemon_composition.py tests/integration/test_rework.py
```

## Definition of rejected
Rework writes bytes before it holds the lock; compensation overwrites another completed edit; a callback calls a lock-taking Git writer; or a new test, fixture or helper is added to a hot test file.

## Time budget
- expected: 30m
- stuck: 60m