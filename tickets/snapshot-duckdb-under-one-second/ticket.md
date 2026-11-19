---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- docs/journal-sql-refactor-plan.md#Target design
- docs/how-clutch-works.md#2.1 Verbs
- clutch/observe.py::snapshot
- clutch/observe.py::row_menu
- clutch/status.py::verdict_refusal
- clutch/drain.py::awaiting_operator
- clutch/drain.py::parked_blob
- clutch/journal.py::Journal
- tests/unit/test_menu_admission.py::fake_snapshot_inputs
- tests/integration/test_menu_verb_parity.py
- pyproject.toml

## Goal / Why
Restore interactive ticket refresh. The actual extension command, clutch view snapshot, took 27.252 s end to end. The attached CPU profile shows 31.49 s instrumented, 4,809 last_states calls and 1,572 reject_queue calls. Fix the snapshot now by bulk-loading the journal once into an in-memory DuckDB per invocation and producing its journal-derived facts in batches. Deliver the complete current snapshot in under one second on an incident-sized checkout.

## Boundary contract
### Journal query ownership
- disposition: extend
- owner: clutch/journal.py, the query owner designated by the journal SQL plan
- consumers: clutch/observe.py snapshot and the CLI process serving the extension
- observable change: one transient in-memory connection loads journal segments once in append order per snapshot invocation. Use set-oriented queries for journal facts shared by rows and actions. Keep nonjournal sources current.
- compatibility: preserve on-disk files, journal writers, ordering and the snapshot reader's handling of empty state, incomplete tail and malformed JSON lines. No database persisted or lock acquired by a snapshot.
- acceptance: a new invocation sees a newly appended complete event and filesystem ticket edit, and growing row count does not multiply full-history reads or queries
- tests: unit query semantics and incident-scale integration/regression fixture
- post-merge source of truth: clutch/journal.py; JSONL segments remain authoritative

### Snapshot and admission
- disposition: reuse
- owner: clutch/observe.py::snapshot, composing clutch/status.py admissions and clutch/drain.py hold policy
- consumers: clutch view snapshot and the extension
- observable change: restore the response time of the existing complete JSON snapshot. Compute facts once and feed existing policy decisions. Preserve verb and menu agreement and lock handling.
- compatibility: unchanged keys, meanings, order, holds, verdict history, actions, and run eligibility including split dependencies; existing CLI callers keep their contracts
- acceptance: match semantic snapshot results on the same fixture and time the complete CLI process including startup and JSON emission
- tests: integration parity and timed CLI regression
- post-merge source of truth: clutch/observe.py for presentation, status and drain for decisions

## Scope in / Scope out
Add duckdb to the runtime dependency set, its exact set pin in tests/unit/test_scaffold.py and regenerate the lock; the measured repeated journal scans earn this dependency. Replace the event-list input of menu/verb admissions with shared admission facts (latest state, settled dependencies, interruption and reject membership). Build them once per snapshot through the journal query owner, and supply the equivalent facts to the same admission functions from CLI and runner callers. Migrate their direct unit tests and the independent verb_inputs in tests/integration/test_menu_verb_parity.py. Preserve the callable contracts and semantics of last_states, reject_queue, parked_blob and awaiting_operator for existing non-snapshot users. Factor decisions that act on facts once in their current owner, so snapshot does not create a second admission policy. Confine this port to the snapshot and the code it needs to share journal facts with the current policy owners. Batch the latest states, parked blobs and operator/reject holds as well as the journal facts consumed by the remaining snapshot fields; keep SQL results in memory. No per-row replay, second raw read, materialization of whole history for Python to replay, persistent cache, stale results, smaller UI, refresh interval change or application-wide journal migration. Update the current snapshot and journal description in docs/how-clutch-works.md. Adapt fixtures which inject the old snapshot journal/menu inputs to the new seam, preserving their assertions, including the existing fixtures in tests/integration/test_watch.py and tests/regress_review_menu_committed_unlocked.py which import observe as watch. The forced edit to the hot watch test file adds no new test or helper. Exercise floored Python changes in unit tests with an injected in-memory connection, fake filesystem/checkout and synthetic events. Leave release-wide rollout to the existing roadmap. Build a reproducible synthetic checkout in tests, with complete valid event envelopes, real ticket files and at least the observed row/history cardinality, with setup outside the timed interval.

## Scope fence
- clutch/journal.py
- clutch/observe.py
- clutch/status.py
- clutch/drain.py
- clutch/__main__.py
- clutch/runner.py
- tests/unit/test_scaffold.py
- tests/unit/test_paved_roads.py
- tests/integration/test_menu_verb_parity.py
- pyproject.toml
- uv.lock
- docs/how-clutch-works.md
- tests/unit/test_snapshot_duckdb.py
- tests/integration/test_snapshot_duckdb.py
- tests/snapshot_scale_fixture.py
- tests/regress_snapshot_latency.py
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py
- tests/integration/test_watch.py
- tests/regress_review_menu_committed_unlocked.py
- tests/integration/test_stale_running.py
- tests/regress_engine_flag_only_drain_serve.py
- tests/regress_snapshot_verdict_menu_parity.py

## Acceptance criteria
1. On a disposable real git checkout populated with at least 37,763 journal events, 694 displayed ticket rows including merged and active tickets, and 791 box rows, `tests/regress_snapshot_latency.py` times three fresh clutch view snapshot processes with a monotonic clock from launch through final stdout/exit. Median is strictly below 1.000 s. Verify successful exit, parseable complete JSON and expected row/box counts and concrete active-ticket values on each run. Report samples, cardinalities and environment on stderr. Run only on a prepared local host with the project venv. Classify setup, import, subprocess and JSON failures as error. A valid slow snapshot is defect; setup time is excluded.
2. `tests/unit/test_snapshot_duckdb.py` demonstrates one load per invocation and queries bounded independently of the number of stems; exercise the in-memory path on empty history, sequential transitions, reject arrival/release and content holds, including events with colliding timestamps distinguished by append order. A full-history Python scan inside any per-row action fails the check.
3. `tests/integration/test_snapshot_duckdb.py` verifies snapshot sections, ordering, menu outcomes, holds and verdict history for representative transitions, draft/confirmed/reordered tickets, split dependencies and empty, multi-segment and incomplete/malformed input. Prove a second invocation sees the edit and appended confirmation without a state cache, journal write or lock. Preserve the menu/verb parity suite.
4. Review `tickets/snapshot-duckdb-under-one-second/run.md` for a raw end-to-end timing against a read-only incident-sized copy or the real checkout using the implemented build. Record actual event, ticket and box counts, three unprofiled timings and median below 1.000 s. An isolated SQL or snapshot-function microbenchmark cannot satisfy this check.

## Verification
```
./dev.py test tests/unit/test_snapshot_duckdb.py tests/integration/test_snapshot_duckdb.py tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py tests/integration/test_menu_verb_parity.py
```

## Definition of rejected
Reject if the normal extension command misses its latency budget, skips any rows or decisions, returns stale priority or state, replays history per ticket, or bypasses existing admission semantics.

## Time budget
- expected: 55m
- stuck: 110m
- reason: the SQL load, admission composition and command timing must ship together to deliver and measure the requested end-to-end repair.

## Regression
```
python tests/regress_snapshot_latency.py
```
- carries: tests/regress_snapshot_latency.py
- carries: tests/snapshot_scale_fixture.py
