---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- clutch/observe.py::step_session
- clutch/observe.py::_open_calls
- clutch/observe.py::snapshot
- clutch/llmeffect.py
- tests/unit/test_observe_step_session.py

## Goal / Why
Restore `observe.snapshot` latency after `extension-step-copy-session-id` reintroduced an $O(\text{steps} \times \text{calls})$ full-directory disk scan in `step_session`. On a checkout with 4,406 evidence call directories (`tickets/snapshot-step-session-perf/evidence/snapshot-perf-evidence.txt`), `observe.snapshot` takes 15.9s with 13.2s (129,594 `open`/`read_text` calls) spent re-reading every `evidence/calls/*/start.json` for each of 28 recent steps. Filtering evidence call directories by the canonical URL-encoded key prefix (`llm/<stem>/<run_seq>/<surface>/<attempt>/`) and listing `evidence/calls` at most once per `snapshot()` eliminates unrelated `start.json` reads and keeps snapshot reads bounded regardless of evidence store size.

## Boundary contract
### Snapshot step session lookup
- disposition: reuse
- owner: clutch/observe.py
- consumers: `clutch view snapshot`, `clutch_open_dashboard`, `clutch_snapshot`, `clutch_app_snapshot`, and the VS Code extension
- observable change: restore single-pass bounded disk I/O in `step_session` and `snapshot` so unrelated evidence call `start.json` files are never opened while keeping identical `session` and `contextValue` output on matching steps
- compatibility: `step_session(evidence, stem, surface, attempt, run_seq)` preserves its public signature, return shape (`{"provider": ..., "id": ...}` or `None`), tie-breaking by `(wall_start, directory.name)`, and error tolerance for unreadable/malformed JSON
- acceptance: `step_session` and `snapshot` attach the exact same session metadata for matching calls while opening zero `start.json` files belonging to other stems, runs, surfaces, or attempts
- tests: unit tests in `tests/unit/test_observe_step_session_perf.py` and existing `tests/unit/test_observe_step_session.py`, plus the carried regression reproducer `tests/regress_snapshot_step_session_perf.py`
- post-merge source of truth: clutch/observe.py

## Scope in / Scope out
In scope:
- Update `step_session` in `clutch/observe.py` so it filters candidate call directories by the URL-encoded key prefix `quote(f"llm/{stem}/{run_seq}/{surface}/{attempt}/", safe="")` (matching the canonical key layout `llm/<stem>/<run_seq>/<surface>/<attempt>/<call_seq>` in `clutch/llmeffect.py`) before reading any `start.json` file.
- Update `_open_calls` and `step_session` in `clutch/observe.py` to accept an optional pre-listed sequence/index of `evidence/calls` entries, and list `(state / "evidence" / "calls")` at most once inside `snapshot()`, passing those entries into both `_open_calls` and `step_session` so `snapshot()` never scans `evidence/calls` per step or per running ticket.
- Add unit tests in `tests/unit/test_observe_step_session_perf.py` (new file) covering prefix filtering, exact session attachment, tie-breaking, unreadable `start.json` tolerance, bounded `start.json` read counts that do not scale with unrelated evidence calls, and a spy asserting `evidence/calls` is listed at most once per `snapshot()` with multiple running tickets and multiple recent steps.
- Add regression reproducer `tests/regress_snapshot_step_session_perf.py` speaking the `regression_result` JSON protocol.

Out of scope:
- Changing evidence call directory naming or `EvidenceStore` layout in `clutch/evidence/`.
- Changing `stats.collect_stats`, MCP dashboard UI, or journal caching.
- Editing existing tests in `tests/unit/test_observe_step_session.py` (keep it passing unchanged).

## Scope fence
- clutch/observe.py
- tests/unit/test_observe_step_session_perf.py
- tests/regress_snapshot_step_session_perf.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_observe_step_session_perf.py` passes and proves that with 100 unrelated evidence call directories, 2 running tickets, and 5 recent steps, `observe.snapshot` opens zero `start.json` files for unrelated calls (ruling out an $O(\text{steps} \times \text{calls})$ full-directory scan) while attaching the exact latest `session` and `contextValue` for each matching step.
2. `./dev.py test tests/unit/test_observe_step_session_perf.py` spies on directory listing of `evidence / "calls"` (`Path.glob`, `Path.iterdir`, and `os.scandir` on that directory) and proves `observe.snapshot` lists `evidence/calls` at most once across 2 running tickets and 5 recent steps (ruling out per-step or per-running-ticket directory scans).
3. `./dev.py test tests/unit/test_observe_step_session_perf.py` proves `step_session(evidence, stem, surface, attempt, run_seq)` called directly opens only `start.json` files whose directory name matches `llm/<stem>/<run_seq>/<surface>/<attempt>/`, not unrelated call directories, and returns `None` rather than raising when a matching `start.json` is malformed or lacks native IDs.
4. `./dev.py test tests/unit/test_observe_step_session.py` passes unchanged, confirming existing session attachment and `clutchCopySession` menu behavior are preserved (not dropped or altered).
5. `uv run python tests/regress_snapshot_step_session_perf.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `{"regression_result": "defect"}` with non-zero exit on merge base.

## Verification
```
./dev.py test tests/unit/test_observe_step_session_perf.py tests/unit/test_observe_step_session.py
```

## Definition of rejected
- Any implementation that still opens `start.json` for unrelated evidence call directories during `step_session` or `observe.snapshot`.
- Any change that alters `step_session`'s signature in a backwards-incompatible way or drops `session` / `contextValue` on valid steps.
- Any edit to files outside `## Scope fence`.

## Time budget
- expected: 10m
- stuck: 20m

## Regression
```
uv run python tests/regress_snapshot_step_session_perf.py
```
- carries: tests/regress_snapshot_step_session_perf.py
