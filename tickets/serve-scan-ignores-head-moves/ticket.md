---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- tests/unit/test_serve_idle_poll.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/serve_rig.py
- clutch/daemon.py
- tickets/serve-scan-ignores-head-moves/evidence/serve-scan-head-trigger.txt

## On-demand
- clutch/serve.py

## Goal / Why
`Serve.scan` takes the exclusive admission section (`mutations()`, which waits for every running implementation and, while it waits, refuses new runs) whenever its intake snapshot changes, and the snapshot includes the sha of `main`. The sha changes on every commit to main: the engine's own run-record, checks, harvest, diagnosis, review and merge commits, the roadmap driver's link, strike and refile commits, and an operator's ticket-plane commits. So the scan takes the exclusive section far more often than a ticket file really changed, and each time a ready second ticket waits for the running one to end. With `scheduler.parallel` `max_runs` 2, serve runs one implementation at a time for much of the time. The evidence file has the mechanism.

The sha is in the snapshot only so that a ticket intake refused for repo state outside `tickets/` is retried after main moves (ticket `serve-polls-block-parallel-runs`). A refused ticket stays an uncommitted file under `tickets/`, which the snapshot already reads as `pending`. With no pending uncommitted ticket file there is nothing to retry, and a move of main cannot change what intake does.

After this ticket the snapshot includes the sha of main only while at least one pending uncommitted ticket file exists. A commit to main made while no ticket file is pending does not change the snapshot and does not take the exclusive section, so it neither waits for a running implementation nor blocks admission.

## Boundary contract
### Serve intake snapshot
- disposition: extend
- owner: clutch/serve.py (`intake_snapshot`)
- consumers: `Serve.scan` and, through it, ticket intake and the watcher's publication
- observable change: the snapshot tuple's `head` element is the sha of main when `pending` is non-empty and `None` otherwise; nothing else in the tuple changes
- compatibility: a ticket file change, a new or removed ticket, a change to `git status` of `tickets/` and a change of a pending stem's journal state still change the snapshot exactly as today; with a pending uncommitted ticket file a move of main still triggers a rescan, so a refused ticket is retried after a merge
- acceptance: criteria 1 to 4
- tests: tests/unit/test_serve_scan_head.py and tests/integration/test_serve_scan_head.py
- post-merge source of truth: clutch/serve.py `intake_snapshot`

## Scope in / Scope out
Scope in:
- `clutch/serve.py` `intake_snapshot`: compute `pending` before `head`, and set the `head` element to `await c.git.rev_parse(c.repo, "main")` only when `pending` is non-empty, else `None`. The existing `except OSError, GitError: return None` stays and still means "unknown is work". Nothing else in the function changes; no other file in `clutch/` changes.
- New tests, each file starting with a `clutch:meta` header created by `uv run clutch meta refresh <file>` with only the `purpose` line edited by hand: `tests/unit/test_serve_scan_head.py`, `tests/integration/test_serve_scan_head.py`, and the reproducer `tests/regress_serve_scan_head.py` that `## Regression` names. Import `tests/integration/serve_rig.py` and change nothing in it.
- `tests/unit/test_serve_idle_poll.py`: only if an existing case there builds a snapshot that depends on the sha of main while no ticket file is pending; the implementer names such a case in the run record and changes only its expectation. Nothing else there changes.

Scope out: the exclusive section in `scan` and the publication gate in `watch` (they keep waiting for running implementations; removing that needs every writer that stamps a ticket file and then commits under one lock, which is separate); verdict settlement; the merge queue; `clutch/daemon.py`; `config.yaml`; docs (no document describes the snapshot's inputs).

## Scope fence
- clutch/serve.py
- tests/unit/test_serve_idle_poll.py
- tests/unit/test_serve_scan_head.py
- tests/integration/test_serve_scan_head.py
- tests/regress_serve_scan_head.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_serve_scan_head.py` shows `intake_snapshot` returns equal tuples before and after the sha of main changes when `git status` of `tickets/` shows no pending uncommitted ticket file, not different tuples (a stand-in `rev_parse` returning `a` then `b`).
2. The same file shows the tuples differ when the sha of main changes while one pending uncommitted ticket file exists (the refused-ticket retry), and that a changed ticket file content, a new ticket directory and a changed `git status` of `tickets/` each still change the tuple with no pending file.
3. `./dev.py test tests/integration/test_serve_scan_head.py` runs serve through `tests/integration/serve_rig.py` with `max_runs` 2 and one implementation blocked on a release event. Commits that touch only a run record (`tickets/<stem>/run.md`) and a roadmap file (`docs/roadmap.md`) are made on main while it is blocked, the fake clock is advanced past `SERVE_POLL_S` at least three times, and `admission.exclusive_pending` is never true and a second ready ticket with a disjoint fence is admitted and starts while the first is still held. The old behavior leaves the second ticket waiting until the first ends.
4. The same test shows a refused ticket is still retried: with a pending uncommitted ticket file that intake refuses for a path under `clutch/`, a commit that adds that path moves main and the next scan intakes the ticket.
5. `uv run python tests/regress_serve_scan_head.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch and `{"regression_result": "defect"}` with a non-zero exit on the merge base, as `## Regression` states.
6. `./dev.py test tests/unit/test_serve_idle_poll.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py tests/unit/test_admission_parallel_run_set.py` passes, with only a case named in Scope in changed.
7. `uv run clutch meta check tests/unit/test_serve_scan_head.py tests/integration/test_serve_scan_head.py tests/regress_serve_scan_head.py` exits 0 (only the files this ticket creates).

## Verification
```
./dev.py test tests/unit/test_serve_scan_head.py tests/integration/test_serve_scan_head.py tests/unit/test_serve_idle_poll.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_admission.py tests/unit/test_admission_parallel_run_set.py
```

## Definition of rejected
The snapshot ignoring a ticket file, directory or `git status` change; a refused ticket no longer retried after main moves; any change to `scan`'s exclusive section, to `watch`, to the merge queue or to `clutch/daemon.py`; the regression reproducer passing on the merge base; a test or fixture added to `tests/integration/serve_rig.py` or another hot test file.

## Time budget
- expected: 20m
- stuck: 40m
- reason: one conditional in one function, one test per layer and one reproducer

## Regression
```
uv run python tests/regress_serve_scan_head.py
```
- carries: tests/regress_serve_scan_head.py
