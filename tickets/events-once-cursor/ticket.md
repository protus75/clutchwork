---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/events.py
- clutch/runner.py::Refusal
- docs/antigravity-plan.md#1. Event cursor and reactive wakeup
- tests/unit/test_view_events.py
- tests/unit/test_main_view_events.py
- tests/unit/test_host_running.py
- tests/unit/test_readme.py
- tests/unit/test_main_help.py
- tests/integration/test_ask_view_events.py

## On-demand
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- README.md

## Goal / Why
Roadmap row 218 (`events-once-cursor`, `docs/antigravity-plan.md` §1). Supervising agents that wake on completed tool calls, subagent messages, or timers rather than line-by-line stdout hooks cannot use an unbounded `clutch view events` stream without either blocking forever or missing events between turns. After this ticket, `clutch/events.py` provides an opaque JSON/base64 state cursor and `wait_once(...)` returning `(next_cursor, lines, timed_out)`, and `clutch view events` gains `--once`, `--cursor CURSOR`, and `--timeout SECONDS` printing structured JSON `{"cursor": ..., "events": [...], "timed_out": bool}` while bare `clutch view events` keeps its streaming line behavior.

## Boundary contract

### Event cursor and `wait_once` API
- disposition: extend
- owner: clutch/events.py
- consumers: `clutch/__main__.py::handle_events` (and future `clutch_wait_event` in `mcp-read-server`)
- observable change: adds `encode_cursor(seen) -> str`, `decode_cursor(token: str) -> tuple[int, set[str], set[tuple[str, str]], dict[str, bool]]`, and `wait_once(state, *, cursor=None, timeout=300.0, sleep=time.sleep, clock=time.monotonic, interval=POLL_SECONDS) -> tuple[str, list[str], bool]`. The cursor is an opaque urlsafe-base64-encoded UTF-8 JSON object (`{"v": 1, "offset": <int>, "reject": [<str>, ...], "engine": [[<str>, <str>], ...], "gates": {<str>: <bool>, ...}}`) capturing the 4-tuple state computed by `changes()`. `decode_cursor` validates the envelope, types (rejecting booleans for `offset`, negative `offset`, non-boolean `gates` values, non-2-string `engine` pairs, and malformed base64/JSON), and raises `ValueError` on any invalid token. `wait_once` validates finite `timeout >= 0` and finite `interval > 0` (raising `ValueError` otherwise). When `cursor is None`, `wait_once` establishes a silent baseline via `poll(state, None)` and waits up to `timeout` seconds (clamping each `sleep` call to `min(interval, remaining)` against a `clock() + timeout` deadline and polling once after the final sleep) until `poll` produces at least one line, returning `(encode_cursor(seen), lines, False)` or `(encode_cursor(seen), [], True)` on timeout. When `cursor` is provided, `wait_once` decodes it and immediately runs `poll(state, seen)` before sleeping: if lines already arrived since `cursor`, it returns `(encode_cursor(seen), lines, False)` immediately with zero sleeps; otherwise it waits up to `timeout` seconds as above (including returning immediately with `timed_out=True` when `timeout == 0` and no lines arrived). If the journal was truncated (`len(events) < offset`), `changes()` re-baselines silently and `wait_once` advances the returned cursor to the new baseline.
- compatibility: additive; `POLL_SECONDS`, `EVENTS`, `changes`, `poll`, and `stream` retain their signatures, return shapes, and behavior unchanged.
- acceptance: acceptance criteria 1, 2, 3, and 4
- tests: tests/unit/test_events_once_cursor.py
- post-merge source of truth: clutch/events.py

### `clutch view events --once` CLI and verb docs
- disposition: extend
- owner: clutch/__main__.py (parser and `handle_events`), clutch/docs/host-running.md, docs/how-clutch-works.md, README.md
- consumers: operators and supervising agents invoking `clutch view events`; `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, `tests/integration/test_ask_view_events.py`
- observable change: adds `--once` (`action="store_true"`), `--cursor` (`default=None`), and `--timeout` (`type=float, default=None`) to the `view events` subparser in `clutch/__main__.py`, updates `_command` `summary`, `does`, `exits`, and `examples` (adding `"clutch view events --once --timeout 300"`), and extends `handle_events`: passing `--cursor` or `--timeout` without `--once` raises `runner.Refusal` (exit 2); with `--once`, it calls `events.wait_once(config.state_dir, cursor=args.cursor, timeout=300.0 if args.timeout is None else args.timeout, sleep=time.sleep, clock=time.monotonic)`, maps `ValueError` from an invalid `--cursor` or invalid `--timeout` to `runner.Refusal` (exit 2), prints a single JSON line `{"cursor": ..., "events": [...], "timed_out": bool}` on stdout, and exits 0 (returning 0 cleanly on `KeyboardInterrupt`); without `--once`, it calls `events.stream(...)` as before. Updates the `view events` row in `clutch/docs/host-running.md` and `docs/how-clutch-works.md` section 2.1 (keeping column 1 as `` `view events` ``) and adds a `--once` example line in `README.md` under `# Observing` (keeping the existing `uv run clutch view events` line).
- compatibility: bare `clutch view events` preserves line-by-line streaming behavior unchanged; `tests/unit/test_main_view_events.py` previously asserted `view events --once` exits 2 and is updated in this ticket to assert default flags `(once=False, cursor=None, timeout=None)` and exit 2 on an unrecognized flag.
- acceptance: acceptance criteria 5, 6, and 7
- tests: tests/unit/test_main_view_events_once.py, tests/unit/test_main_view_events.py, tests/unit/test_main_help.py, tests/unit/test_host_running.py, tests/unit/test_readme.py, tests/integration/test_ask_view_events.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/events.py`: add `encode_cursor`, `decode_cursor`, and `wait_once(state, *, cursor=None, timeout=300.0, sleep=time.sleep, clock=time.monotonic, interval=POLL_SECONDS)` with strict input validation (`timeout >= 0`, `interval > 0`, finite values, strict cursor schema check).
- `clutch/__main__.py`: update the `view events` `_command` help (`summary`, `does`, `exits`, `examples`), add `--once`, `--cursor`, and `--timeout` options on that subparser, and update `handle_events` to refuse `--cursor`/`--timeout` without `--once`, call `events.wait_once` on `--once`, translate `ValueError` into `runner.Refusal` (exit 2), print `json.dumps({"cursor": ..., "events": [...], "timed_out": bool})`, and preserve `events.stream` when `--once` is omitted. Nothing else in `clutch/__main__.py` changes.
- `clutch/docs/host-running.md`: update the `What it does` cell of the `| \`view events\` | Yes | ... |` row to document `--once`, `--cursor`, and `--timeout`; keep column 1 exact.
- `docs/how-clutch-works.md`: update the `What it does` cell of the `| \`view events\` | no | ... |` row in section 2.1 to document `--once`, `--cursor`, and `--timeout` and the JSON output; keep column 1 exact so `tests/integration/test_ask_view_events.py` remains satisfied.
- `README.md`: add `uv run clutch view events --once --timeout 300  # wait once for changes as JSON` under `# Observing` while keeping the existing `uv run clutch view events` line intact.
- `tests/unit/test_main_view_events.py`: replace the old `["view", "events", "--once"]` `SystemExit(2)` check (lines 20-22) with checking `parser.parse_args(["view", "events"])` defaults `(once, cursor, timeout) == (False, None, None)` and `["view", "events", "--unknown"]` raising `SystemExit(2)` (keeping the `pytest` import used).
- New unit test files `tests/unit/test_events_once_cursor.py` and `tests/unit/test_main_view_events_once.py`, using `tmp_path`/fake seams only.

Scope out:
- Editing `clutch/specs/ask/*.md` (`ask-specs-mcp-supervision` updates supervising prompts later).
- Adding `clutch/mcp.py` or MCP tools (`mcp-read-server` consumes `events.wait_once` later).
- Changing `events.changes`, `events.poll`, `events.stream`, `events.EVENTS`, `clutch/observe.py`, `clutch/status.py`, `clutch/help.py`, or `vscode-clutchwork/`.
- Adding new tests to `tests/unit/test_view_events.py`, `tests/unit/test_main_view_group.py`, `tests/unit/test_main_help.py`, or any of the seven hot test files.

Merge note with confirmed unmerged `roadmap-align-pypi-versions`: that ticket edits only the `roadmap author` row in `docs/how-clutch-works.md` §2.1, while this ticket edits only the `view events` row in §2.1, so either merge order preserves both edits.

## Scope fence
- clutch/events.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_main_view_events.py
- tests/unit/test_events_once_cursor.py
- tests/unit/test_main_view_events_once.py

## Acceptance criteria
1. `tests/unit/test_events_once_cursor.py`: `encode_cursor` and `decode_cursor` round-trip a 4-tuple containing non-empty journal offset, Reject-queue stems, engine-lifecycle `(kind, ts)` tuples, and gate pass/fail map back to equal values (not a dropped field or stringified key), and `decode_cursor` raises `ValueError` on empty string, invalid base64, invalid JSON, wrong version, boolean or negative `offset`, non-bool `gates` value, and malformed `engine` pair (never silently accepting corrupt cursors). Verified by `./dev.py test tests/unit/test_events_once_cursor.py`.
2. `tests/unit/test_events_once_cursor.py`: `wait_once(tmp_path, cursor=None, timeout=12.0, sleep=fake_sleep, clock=fake_clock, interval=5.0)` establishes a silent baseline over pre-existing journal/log history (does not replay old history), sleeps `5.0`, `5.0`, and clamped `2.0` when nothing arrives, returns `(next_cursor, [], True)` where `decode_cursor(next_cursor)[0]` equals the baseline count; when an actionable event is appended during a fake `sleep`, `wait_once` returns `(next_cursor, [expected_line], False)` on that poll without sleeping further. Verified by `./dev.py test tests/unit/test_events_once_cursor.py`.
3. `tests/unit/test_events_once_cursor.py`: calling `wait_once` with a previously returned `cursor` after an actionable event was already appended between turns returns `(next_cursor, [expected_line], False)` with zero `sleep` calls (`timed_out is False`, not missing pre-existing post-cursor events); calling with `timeout=0.0` and no new events returns `(next_cursor, [], True)` with zero `sleep` calls; truncating the journal below the cursor offset re-baselines silently and returns the updated cursor rather than raising or replaying. Verified by `./dev.py test tests/unit/test_events_once_cursor.py`.
4. `tests/unit/test_events_once_cursor.py`: `wait_once` raises `ValueError` for `timeout=-1.0`, `timeout=float("nan")`, `timeout=float("inf")`, and `interval=0.0` before sleeping. Verified by `./dev.py test tests/unit/test_events_once_cursor.py`.
5. `tests/unit/test_main_view_events_once.py`: `_parser().parse_args(["view", "events", "--once", "--cursor", "tok", "--timeout", "15"])` sets `(once, cursor, timeout) == (True, "tok", 15.0)`; `main(["view", "events", "--once"], ...)` calls `events.wait_once` with `cursor=None, timeout=300.0`, prints single-line JSON `{"cursor": ..., "events": [...], "timed_out": false}` to stdout with empty stderr and exit 0; `main(["view", "events", "--cursor", "tok"], ...)` and `main(["view", "events", "--timeout", "10"], ...)` without `--once` exit 2 with `"clutch view: "` refusal on stderr; invalid `--cursor` or negative `--timeout` with `--once` exits 2 with `"clutch view: "` refusal on stderr (never an uncaught traceback); `KeyboardInterrupt` inside `wait_once` returns 0 with empty stderr. Verified by `./dev.py test tests/unit/test_main_view_events_once.py`.
6. `tests/unit/test_main_view_events.py` passes with updated default-option and unknown-flag checks alongside existing streaming interrupt behavior; `./dev.py test tests/unit/test_main_view_events.py tests/unit/test_view_events.py tests/unit/test_events_gate_repeat.py tests/unit/test_events_upgrade_pending.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_main_view_group.py` exits 0.
7. `clutch/docs/host-running.md`, `docs/how-clutch-works.md` section 2.1, and `README.md` document `--once`, `--cursor`, and `--timeout` on `view events` while preserving `| \`view events\` |` row prefixes and `uv run clutch view events`, verified by `./dev.py test tests/integration/test_ask_view_events.py tests/unit/test_host_running.py tests/unit/test_readme.py`.

## Verification
```
./dev.py test tests/unit/test_events_once_cursor.py tests/unit/test_main_view_events_once.py tests/unit/test_main_view_events.py tests/unit/test_view_events.py tests/unit/test_events_gate_repeat.py tests/unit/test_events_upgrade_pending.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_main_view_group.py tests/integration/test_ask_view_events.py
```

## Definition of rejected
- `wait_once` calls real `time.sleep` or `time.monotonic` when `sleep`/`clock` seams are passed, or replays pre-baseline history when `cursor=None`.
- Passing a valid `cursor` misses events appended between calls, or `--cursor`/`--timeout` without `--once` succeeds instead of refusing with exit 2.
- Bare `clutch view events` stops streaming or breaks `tests/unit/test_view_events.py` / `tests/integration/test_ask_view_events.py`.
- Any file outside `## Scope fence` is modified, or `clutch/events.py` drops below the 90% unit coverage threshold.

## Time budget
- expected: 10m
- stuck: 20m