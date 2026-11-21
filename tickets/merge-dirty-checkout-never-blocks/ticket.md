---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- clutch/merge.py
- clutch/mergequeue.py
- tests/unit/test_merge_dirty.py
- tests/integration/test_merge.py
- tests/integration/test_mergequeue.py
- tickets/merge-dirty-checkout-never-blocks/evidence/ev5.txt

## Goal / Why
A ticket that passed Implement, Check and Review is sent to the Reject queue (`abandon-human`) when the owner has an uncommitted edit in the main checkout to a file the ticket also changes: the merge gate's `dirty_checkout` finding is a refusal, and the diagnosis stage turns it into a human task. On 2026-11-21 `review-cost-sonnet-instance` was rejected this way for the owner's own uncommitted `config.yaml` edit. The owner edits the main checkout while serve runs; that must never reject or fail a ticket.

After this ticket a `dirty_checkout` finding defers the merge instead of refusing it: the reviewed ticket stays in the merge queue, no refusal, retry, diagnosis, Reject-queue entry or attempt is spent, one `merge_waiting_dirty` signal naming the paths is journaled once per wait, and the squash is admitted on a later merge poll once the overlapping edit is committed or reverted. The owner's uncommitted edit is never overwritten.

## Boundary contract
### Merge admission under a dirty main checkout
- disposition: extend
- owner: clutch/merge.py (`dirty_overlap`) and clutch/mergequeue.py (`_admit`, `process`)
- consumers: the merge queue's admission, `clutch engine serve` and `engine drain`, the diagnosis stage (no longer reached for this finding)
- deferral shape: `_admit` returns `StageResult(outcome="deferred", artifact=None)`; `process()` puts a deferred ticket back in `pending` for the next poll and appends nothing to `results` or `deliveries`, so the serve boundary future stays unresolved until a later poll admits it; inline `merge()` (run and drain) returns the same deferred result and the runner journals no failure and spends no attempt, leaving the ticket reviewed and retried by the next merge call
- once-per-wait: the `merge_waiting_dirty` marker is an in-memory set on `MergeQueue` keyed by stem, cleared when the stem is admitted or its overlap goes away; a serve restart signals again, and a second wait after the first clears signals again
- observable change: an overlapping or staged-outside-branch edit defers admission and journals `merge_waiting_dirty`; it no longer returns a `dirty_checkout` refusal
- compatibility: every other merge refusal, the squash itself, ordering of pending tickets and the main checkout's contents stay as today; a deferred ticket does not block other pending tickets from being admitted
- acceptance: criteria 1 to 4
- tests: tests/unit/test_merge_dirty_defer.py and tests/integration/test_merge_dirty_defer.py
- post-merge source of truth: clutch/mergequeue.py and docs/how-clutch-works.md sections 7.2 and 11

## Scope in / Scope out
Scope in:
- `clutch/mergequeue.py` and `clutch/merge.py`: the two `merge.dirty_overlap` call sites in `_admit` return a deferral (not `refused(...)`) when `dirty_overlap` reports findings. The implementer reads both files and `process`, then makes the deferred ticket stay pending without being picked again in the same `process()` pass (no spin) and be retried on the next poll; it names in the run record the simpler approach rejected. A cheap overlap check before the expensive gates may be added only if it is the smallest way to avoid rerunning them every poll.
- Existing tests that pin the refusal change to the deferral: `tests/unit/test_merge_dirty.py`, the `dirty_checkout` cases in `tests/integration/test_merge.py` (`test_merge_refuses_dirty_overlap_instead_of_raising` and its neighbour at line 130) and `tests/integration/test_mergequeue.py` (lines 120-148); nothing else in those files changes.
- `docs/how-clutch-works.md` lines 307 and 599: say the merge waits and retries; then `uv run clutch meta refresh docs/how-clutch-works.md`, changing nothing else in its header.
- New tests, each starting with a `clutch:meta` header created by `uv run clutch meta refresh <file>` with only `purpose` edited: `tests/unit/test_merge_dirty_defer.py`, `tests/integration/test_merge_dirty_defer.py`, and the reproducer `tests/regress_merge_dirty_defer.py`.

Scope out: the squash and write paths, other refusals, untracked-file handling, `config.yaml`, and any auto-commit or stash of the owner's edit.

## Scope fence
- clutch/merge.py
- clutch/mergequeue.py
- docs/how-clutch-works.md
- tests/unit/test_merge_dirty.py
- tests/integration/test_merge.py
- tests/integration/test_mergequeue.py
- tests/unit/test_merge_dirty_defer.py
- tests/integration/test_merge_dirty_defer.py
- tests/regress_merge_dirty_defer.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_merge_dirty_defer.py` shows a reviewed ticket whose changed file has an uncommitted edit in the main checkout is not merged, is not refused, spends no attempt, is not sent to diagnosis, and has exactly one `merge_waiting_dirty` signal after three polls, and that a second wait after the first clears signals again.
2. `./dev.py test tests/integration/test_merge_dirty_defer.py` shows that after the edit is committed the next poll admits the ticket and main contains both the owner's commit and the ticket's change; the owner's edit is never lost.
3. `./dev.py test tests/integration/test_merge_dirty_defer.py` shows a second pending ticket with no overlap is admitted while the first waits.
4. `./dev.py test tests/unit/test_merge_dirty_defer.py tests/unit/test_merge_dirty.py` passes; `uv run python tests/regress_merge_dirty_defer.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch and `{"regression_result": "defect"}` with a non-zero exit on the merge base.
5. `./dev.py test tests/integration/test_merge.py tests/integration/test_mergequeue.py` passes with only the named cases changed, and `uv run clutch meta check tests/unit/test_merge_dirty_defer.py tests/integration/test_merge_dirty_defer.py tests/regress_merge_dirty_defer.py docs/how-clutch-works.md` exits 0.

## Verification
```
./dev.py test tests/unit/test_merge_dirty_defer.py tests/integration/test_merge_dirty_defer.py tests/unit/test_merge_dirty.py tests/integration/test_merge.py tests/integration/test_mergequeue.py
```

## Definition of rejected
A dirty overlap that still refuses, spends an attempt or reaches the Reject queue; an owner edit overwritten, stashed or auto-committed; a deferred ticket that blocks other tickets or spins within one poll; a regression reproducer passing on the merge base; a test added to another hot test file beyond the named cases.

## Time budget
- expected: 30m
- stuck: 60m

## Regression
```
uv run python tests/regress_merge_dirty_defer.py
```
- carries: tests/regress_merge_dirty_defer.py
