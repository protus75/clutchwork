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
- clutch/author.py::author
- clutch/author.py::commit_record
- clutch/author.py::failure_declined
- clutch/triage.py::_record
- tests/integration/test_triage.py
- tests/integration/test_requisition.py

## Goal / Why
Move Author's final ticket publication, its failure compensation and its decision-record commits onto Git.commit_edit. Then Author and triage no longer write ticket or record files before they take the commit lock. This is part of the split ticket-writes-atomic-commit, which serializes all engine ticket writes so Serve can stop waiting for run lifetimes.

## Boundary contract
### Atomic engine ticket edit and commit
- disposition: reuse
- owner: clutch/git.py::Git.commit_edit
- consumers: Author's final publication commit() closure and failure compensation, and author.commit_record
- observable change: Author's final read/validate/write and commit run inside one commit_edit callback. Compensation restores pre-publication bytes only when the current bytes still equal this publication's output.
- compatibility: commit messages, effect keys, exact reviewed-byte checks and the existing compensation assertions are unchanged. review_candidate, the review_ticket/review_with_identity arguments and the returned provenance are untouched.
- acceptance: Author writes no ticket bytes before it holds main_write and commit.lock, and compensation keeps another writer's later bytes
- tests: tests/unit/test_ticket_write_consumers_author.py
- post-merge source of truth: clutch/git.py::Git.commit_edit
### Decision record commit
- disposition: extend
- owner: clutch/author.py::commit_record
- consumers: author.failure_declined and clutch/triage.py::_record
- observable change: commit_record receives the rendered record bytes and writes the record inside the commit_edit callback, instead of its callers writing the record first
- compatibility: the effect key and commit message are unchanged. Triage's existing-record recommit passes the bytes already on disk.
- acceptance: no decision record is written outside commit_edit
- tests: tests/unit/test_ticket_write_consumers_author.py and tests/integration/test_triage.py
- post-merge source of truth: clutch/author.py::commit_record

## Scope in / Scope out
Scope in:
- Prepare model output and private evidence before entering commit_edit. Hold no lock across Author or requisition model calls. Read-only preparation does not replace the protected final read, validate and write.
- Change author.commit_record to take the record bytes. Update author.failure_declined and clutch/triage.py::_record (the write around lines 73-74 and the existing-record recommit around line 243). Change nothing else in triage.py.
- In the compensation callback, check that the current bytes equal this publication's output, then restore the prior bytes or remove an owned new file. Never call add, restore or commit inside the callback. Ignore only NothingToCommit.
- Update the commit-failure interception in tests/integration/test_author.py to go through the protected path, and keep its compensation assertions. Give the Git stand-ins in tests/unit/test_author_roadmap_row.py and tests/unit/test_author_stem_claimed.py (the SimpleNamespace git around line 56) a commit_edit fake that awaits the callback before it records the commit. Keep their assertions. Add no getattr fallback in production code.
- Add tests to tests/unit/test_ticket_write_consumers_author.py, including a non-reentrant fake lock that raises on recursive acquire. Exercise success, partial publication and compensation.
- In the run record, list each Author and decision-record write site and name the owner that covers it.
Scope out:
- Do not touch runner, daemon.apply_rework, triage decision logic, review provenance or Serve's run exclusion.

## Scope fence
- clutch/author.py
- clutch/triage.py
- tests/unit/test_ticket_write_consumers_author.py
- tests/integration/test_author.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_author_stem_claimed.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_ticket_write_consumers_author.py` proves the following: Author publication, compensation and decision records change bytes only inside commit_edit; compensation keeps a later legitimate edit; no callback takes a writer lock again.
2. `./dev.py test tests/integration/test_author.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_stem_claimed.py tests/integration/test_triage.py tests/integration/test_requisition.py` preserves publication, decision-record, recovery and publication-failure behavior.

## Verification
```
./dev.py test tests/unit/test_ticket_write_consumers_author.py tests/integration/test_author.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_stem_claimed.py tests/integration/test_triage.py tests/integration/test_requisition.py
```

## Definition of rejected
A lock spans a model call; an Author or decision-record write happens before the lock is held; compensation overwrites another completed edit; or triage logic changes beyond the commit_record caller update.

## Time budget
- expected: 30m
- stuck: 60m