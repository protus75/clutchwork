---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/stats.py
- clutch/driver.py::unwrap_fence
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- docs/boundary-contract-plan.md#Outcome comparison
- tests/unit/test_stats.py
- tests/unit/test_main_view_group.py

## On-demand
- clutch/__main__.py

## Goal / Why
Roadmap row 233 replaces merged row 208 (`boundary-contract-outcome-compare`), whose `docs/boundary-contract-plan.md#Outcome comparison` marked every quantity "Not measurable" because the ticket worktree had no state directory and `clutch view stats` could not split journal history before vs after a cutoff or separate duplicate-owner review findings.

After this ticket:
1. `clutch/stats.py` exposes `parse_split`, `DUPLICATE_OWNER_PATTERN`, and `project_split(events, *, now, split)` to split journal events up to `now` into `before` (`ts < split`) and `after` (`split <= ts <= now`), separating settled tickets, premise failures by stage, rework actions, review snags mean, first-pass yield, and duplicate-owner/undeclared-boundary review findings.
2. `clutch view stats` accepts `--split <ISO-8601>` to print that before/after comparison (with `--json`, `--tree`, or text output) while keeping existing `--window` behavior unchanged when `--split` is omitted.
3. CLI help in `clutch/__main__.py` and the `view stats` rows in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` document `--split`.
4. `docs/boundary-contract-plan.md#Outcome comparison` records the verified before/after counts measured from this repository's journal at row 153 (`adf7d00b`, `2026-11-20T05:08:40+00:00`) instead of "Not measurable".

## Boundary contract

### Stats split projection
- disposition: extend
- owner: clutch/stats.py
- consumers: clutch/__main__.py, tests/unit/test_stats_boundary_outcomes.py
- observable change: add `parse_split(value: str) -> datetime`, `DUPLICATE_OWNER_PATTERN`, and `project_split(events, *, now, split) -> dict` returning `{"split": split_dt.isoformat(), "before": <period>, "after": <period>}` where each period has `settled` (`merged`, `already_satisfied`, `rejected`), `premise_failed` (`implement`, `requisition`, `review`, `total`), `rework` (`update`, `split`, `escalate`), `review_snags_mean`, `first_pass_yield`, and `duplicate_owner_findings`; existing `project_stats`, `collect_stats`, `render_stats`, `stats_tree`, and `window_start` contracts and top-level keys stay unchanged
- compatibility: additive; existing callers (`clutch/__main__.py`, `clutch/mcp.py`, `clutch/calibration.py`, and existing stats/help tests) keep their exact inputs and outputs
- acceptance: criteria 1, 2, and 3
- tests: tests/unit/test_stats_boundary_outcomes.py
- post-merge source of truth: clutch/stats.py

### Review reply fence unwrapper
- disposition: reuse
- owner: clutch/driver.py::unwrap_fence
- consumers: clutch/stats.py
- observable change: none; `project_split` reuses `unwrap_fence` to unwrap JSON code fences from review `effect_completion` reply text instead of writing a second parser
- compatibility: unchanged
- acceptance: criterion 2
- tests: tests/unit/test_stats_boundary_outcomes.py
- post-merge source of truth: clutch/driver.py

### CLI view stats --split option
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators, clutch/docs/host-running.md, docs/how-clutch-works.md, tests/unit/test_stats_boundary_outcomes.py, tests/unit/test_main_help.py, tests/unit/test_main_view_group.py
- observable change: `clutch view stats` adds optional `--split <ISO-8601>` (default `None`); when provided, `handle_stats` validates it via `parse_split` (exiting 2 via `_fail` on invalid or timezone-naive input), computes `project_split(events, now=now, split=split)` without reading git check invoices, and renders with `--json`, `--tree`, or `render_stats`; when omitted, existing `--window` / `_stats` path is unchanged; CLI help and examples in `clutch/__main__.py` and verb tables in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` describe `--split`
- compatibility: additive; default `view stats` behavior without `--split`, `--window` default (`7d`), and existing flags stay unchanged
- acceptance: criteria 3 and 4
- tests: tests/unit/test_stats_boundary_outcomes.py, tests/unit/test_main_help.py, tests/unit/test_main_view_group.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out

### Scope in
1. **`clutch/stats.py`**:
   - Import `unwrap_fence` from `clutch.driver`.
   - Define `DUPLICATE_OWNER_PATTERN` as a compiled case-insensitive regex matching boundary-contract review finding language:
     `r"\b(?:duplicate|second|parallel|competing)\s+(?:owner|parser|registry|codec|factory|implementation)\b|\bduplicate[- ]owner\b|\bundeclared\s+(?:boundar(?:y|ies)|public|exported|api|symbol)\b|\bcanonical\s+owner\b"`.
   - Add `parse_split(value: str) -> datetime`: parses an ISO-8601 timestamp with `datetime.fromisoformat(value)`; raises `ValueError(f"bad split {value} -- use an ISO-8601 timestamp with timezone")` if parsing fails or `tzinfo is None`.
   - Add `project_split(events, *, now, split) -> dict`:
     - Accepts `split` as a `datetime` (if `str`, parses via `parse_split`; if timezone-naive `datetime`, raises `ValueError`).
     - Filters `events` to `ts <= now`, then partitions into `before` (`ts < split`) and `after` (`split <= ts <= now`).
     - For each period (`before` using `all_events = before_events` and `now = split`; `after` using `all_events = valid_events` and `now = now`), computes:
       - `settled`: `{"merged": int, "already_satisfied": int, "rejected": int}` from the latest `STATE_TRANSITION` to `CLOSED` per ticket within that period.
       - `premise_failed`: `{"implement": int, "requisition": int, "review": int, "total": int}` from `STATE_TRANSITION` events with `to == "premise_failed"` within that period (`total` counts all `premise_failed` transitions in the period, including any other stage).
       - `rework`: `{"update": int, "split": int, "escalate": int}` from `SIGNAL` events with `signal == "rework_order"` within that period (missing actions are `0`).
       - `review_snags_mean`: `round(snags / len(stems), 3)` when `stems` is non-empty else `0.0`, where `stems` are tickets settled in the period and `snags` counts `STATE_TRANSITION` events with `to == "gate_failed"` and `stage == "review"` for those stems in `all_events`.
       - `first_pass_yield`: `round(sum(n == 1 for n in merged_attempts) / len(merged_attempts), 3)` when `merged_attempts` is non-empty else `None`, where `merged_attempts` is the count of `to == "running"` transitions in `all_events` for each ticket whose latest settled state in the period is `"merged"`.
       - `duplicate_owner_findings`: count of findings in `EFFECT_COMPLETION` events within that period whose `key` matches `llm/<stem>/<run_seq>/review/<attempt>/<call_seq>` (6 slash-separated parts, `parts[0] == "llm"`, `parts[3] == "review"`), whose `body["result"]["text"]` parses via `json.loads(unwrap_fence(text))` to a dict with `verdict == "snag"`, and whose `findings` list items have `code` in `{"scope", "acceptance"}` with `DUPLICATE_OWNER_PATTERN.search(f"{finding.get('message', '')} {finding.get('paved_road', '')}")` matching. Non-JSON or malformed review replies are skipped without raising.
     - Returns `{"split": split_dt.isoformat(), "before": before_summary, "after": after_summary}`.
   - Keep `project_stats`, `collect_stats`, `render_stats`, `stats_tree`, and `window_start` unchanged so all existing callers and `test_help.py` top-level `stat.*` keys stay intact.
2. **`clutch/__main__.py`**:
   - Add `stats.add_argument("--split", default=None, help="Split journal metrics before and after an ISO-8601 timestamp with timezone.")` to the `view stats` parser.
   - Update `view stats` `_command` `does`, `exits`, and `examples` (adding a `--split` example that parses cleanly under `test_main_help.py`, e.g. `clutch view stats --split 2026-11-20T05:08:40+00:00 --json`).
   - In `handle_stats`: when `args.split is not None`, validate via `parse_split(args.split)` (returning `_fail(args.verb, str(exc))` on `ValueError`), compute `result = project_split(events, now=now, split=split)`, and print via `--tree`, `--json`, or `render_stats`; when `args.split is None`, keep the existing `window_start` + `_stats` flow unchanged.
3. **`clutch/docs/host-running.md` and `docs/how-clutch-works.md`**:
   - Update the `view stats` row in `clutch/docs/host-running.md` and the `view stats` row in `docs/how-clutch-works.md#2.1 Verbs` to document `[--split ISO]` and its before/after comparison of premise failures, rework, and duplicate-owner findings.
4. **`docs/boundary-contract-plan.md#Outcome comparison`**:
   - Replace the "Not measurable" placeholder table and prose with the verified counts measured from this repository's journal (`.clutch/state/journal/`, 25 files, 60,701 events spanning `2026-10-05T07:10:12+00:00` to `2026-11-25T16:09:59+00:00`), split at row 153 (`adf7d00b`, `2026-11-20T05:08:40+00:00`) via `clutch view stats --split 2026-11-20T05:08:40+00:00 --json`:
     - **Settled tickets**: Before: 807 (`merged`: 736, `already_satisfied`: 5, `rejected`: 66); After: 279 (`merged`: 201, `already_satisfied`: 1, `rejected`: 77).
     - **Premise failures (`premise_failed`)**: Before: 651 total (`implement`: 568, `requisition`: 83, `review`: 0; 0.885 per merged ticket); After: 117 total (`implement`: 90, `requisition`: 26, `review`: 1; 0.582 per merged ticket).
     - **Rework (`rework_order` signals)**: Before: 24 total (`update`: 17, `split`: 4, `escalate`: 3; 0.033 per merged ticket); After: 80 total (`update`: 53, `split`: 3, `escalate`: 24; 0.398 per merged ticket).
     - **Review snags mean**: Before: 0.165; After: 0.204.
     - **First-pass yield**: Before: 0.662 (66.2%); After: 0.493 (49.3%).
     - **Duplicate-owner findings**: Before: 0 (0.000 per merged ticket); After: 1 (`training-export-ticket`, `scope` finding at `2026-11-20T06:20:22Z`; 0.005 per merged ticket).
   - State clearly that `duplicate_owner_findings` is counted from `scope` and `acceptance` review snag findings matching `DUPLICATE_OWNER_PATTERN` (because row 153 added no dedicated finding code), and that raw before/after windows do not by themselves establish causation (rework and review-snag rates also reflect later pipeline changes).
5. **`tests/unit/test_stats_boundary_outcomes.py`**:
   - New unit test file (in-memory fakes and `tmp_path` only; no repo reads, no processes, no network) covering `parse_split`, `project_split`, `DUPLICATE_OWNER_PATTERN`, and `view stats --split` CLI parsing, dispatch, and refusal.

### Scope out
- Do not change `project_stats` top-level keys, `clutch/help.py`, `clutch/mcp.py`, or `vscode-clutchwork/`.
- Do not add a new review finding code to the review prompt spec.
- Do not edit existing hot test files (`tests/integration/test_cli.py`, `tests/integration/test_stages.py`, etc.) or add a standing test pinning `docs/boundary-contract-plan.md` prose.

## Scope fence
- clutch/stats.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- docs/boundary-contract-plan.md
- tests/unit/test_stats_boundary_outcomes.py

## Acceptance criteria
1. `parse_split` accepts a timezone-aware ISO-8601 timestamp and raises `ValueError` on a malformed string or a timezone-naive timestamp (not silently treating naive timestamps as UTC), verified by `./dev.py test tests/unit/test_stats_boundary_outcomes.py`.
2. `project_split(events, now=now, split=split)` partitions events strictly at `ts < split` (`before`) vs `split <= ts <= now` (`after`), excludes events with `ts > now`, separates `settled`, `premise_failed` (by `implement`, `requisition`, `review`, `total`), `rework` (`update`, `split`, `escalate`), `review_snags_mean`, `first_pass_yield`, and `duplicate_owner_findings` (counting fenced or plain JSON `scope`/`acceptance` review snag findings matching `DUPLICATE_OWNER_PATTERN` while ignoring `logic` findings, `approve` verdicts, non-review completions, and malformed JSON instead of crashing or overcounting), verified by `./dev.py test tests/unit/test_stats_boundary_outcomes.py`.
3. `clutch view stats --split <ISO>` prints JSON (`--json`), tree JSON (`--tree`), or text (`render_stats`) from `project_split` without calling `_stats`, exits 2 on a bad or naive `--split` timestamp (not 0 or an unhandled traceback), and leaves `clutch view stats` without `--split` calling the existing `--window` path unchanged, verified by `./dev.py test tests/unit/test_stats_boundary_outcomes.py tests/unit/test_main_view_group.py tests/unit/test_main_help.py tests/unit/test_help.py`.
4. `clutch/docs/host-running.md` and `docs/how-clutch-works.md` document `--split` on the `view stats` row, and `clutch/__main__.py` help/examples for `view stats` pass `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/integration/test_help.py`.
5. `docs/boundary-contract-plan.md#Outcome comparison` records the verified before/after counts and per-merged-ticket rates from Scope in (with no remaining "Not measurable" table entries) and explains the `DUPLICATE_OWNER_PATTERN` text-classifier caveat, verified by review of `docs/boundary-contract-plan.md#Outcome comparison`.

## Verification
```
./dev.py test tests/unit/test_stats_boundary_outcomes.py tests/unit/test_stats.py tests/unit/test_stats_usage.py tests/unit/test_main_view_group.py tests/unit/test_main_help.py tests/unit/test_help.py tests/unit/test_host_running.py tests/integration/test_stats.py tests/integration/test_help.py
```

## Definition of rejected
- Any existing `clutch view stats` flag or `project_stats` top-level key changes or breaks existing callers.
- `clutch/stats.py` introduces a second JSON-fence unwrapper instead of reusing `clutch/driver.py::unwrap_fence`.
- `tests/unit/test_stats_boundary_outcomes.py` reads real `.clutch/state/` files or repo files, or fails to cover the added lines in `clutch/stats.py` against `test-gate.toml`.
- `docs/boundary-contract-plan.md#Outcome comparison` leaves "Not measurable" cells or alters the verified counts from Scope in.

## Time budget
- expected: 10m
- stuck: 20m
