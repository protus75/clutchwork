---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- docs/antigravity-plan.md#2. Detached daemon lifecycle
- clutch/serve.py::Serve.run
- clutch/seams.py::spawn_detached
- clutch/runner.py::Refusal
- clutch/control.py::write_active
- clutch/lockfile.py::Lockfile.acquire
- tests/unit/test_drain_detach_cli.py
- tests/unit/test_main_engine_group.py
- tests/unit/test_main_help.py
- tests/unit/test_host_running.py
- tests/unit/test_readme.py
- tests/integration/test_help.py

## On-demand
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- README.md

## Goal / Why
Roadmap row 219 (`engine-serve-detach`, `docs/antigravity-plan.md` §2). Supervising agents and MCP tools in Antigravity cannot keep `clutch engine serve` attached to a shell or MCP stdio process, because reloading the editor or closing a conversation terminates child processes (`AGENTS.md`: launchers carry no process policy). Today `clutch engine drain --detach` spawns a detached session writing to `<state_dir>/drain.out`, whereas `clutch engine serve` runs only in the foreground.

After this ticket:
- `clutch engine serve --detach` spawns `[sys.executable, "-m", "clutch", *(["--config", str(args.config)] if args.config else []), "engine", "serve"]` (without `--detach`) in its own detached OS session (`start_new_session=True` via `seams.spawn_detached`), redirecting stdout and stderr in append mode to `<state_dir>/serve.out`.
- Before returning, the launcher waits briefly (`SERVE_STARTUP_TIMEOUT_S = 5.0`s, polling every `SERVE_STARTUP_POLL_S = 0.05`s) to confirm startup (`clutch.lock` held by `pid` for `"serve"` and `control/active.json` updated with a fresh non-null `lifecycle_id` distinct from any pre-spawn `lifecycle_id`) or surface an immediate child exit/refusal from the newly appended tail of `<state_dir>/serve.out` as a `runner.Refusal` (exit 2), then prints `serve: pid <pid>, output <output>` and exits `0`.
- Foreground `clutch engine serve` and `clutch engine drain --detach` keep their existing behavior unchanged.

Rejected simpler approach: spawn `engine serve` and return `0` immediately without checking startup, as `engine drain --detach` does. Because `serve` is a long-lived daemon whose callers (`mcp-control-and-tickets` and operators) need to know it actually took the writer lock and passed startup recovery, a silent background exit on `LockHeld`, stale conduct files, or `serve startup recovery refused` would leave callers believing `serve` started.

## Boundary contract

### Detached child exit probe
- disposition: extend
- owner: clutch/seams.py
- consumers: `clutch/serve.py::wait_detached_startup`
- observable change: adds `child_exit(pid: int) -> int | None` wrapping `os.waitpid(pid, os.WNOHANG)` and returning `os.waitstatus_to_exitcode(status)` when the child exited, or `None` when still running or on `ChildProcessError`
- compatibility: `spawn_detached` signature and behavior are unchanged so all existing `drain --detach` callers and tests remain identical
- acceptance: criterion 1
- tests: tests/unit/test_serve_detach.py
- post-merge source of truth: clutch/seams.py

### Detached serve startup confirmation
- disposition: extend
- owner: clutch/serve.py
- consumers: `clutch/__main__.py::main` (`handle_detach`)
- observable change: adds `SERVE_STARTUP_TIMEOUT_S = 5.0`, `SERVE_STARTUP_POLL_S = 0.05`, `capture_startup_baseline(state_dir, output) -> tuple[int, str | None]`, `startup_confirmed(state_dir, pid, prior_lifecycle) -> bool`, `_read_startup_tail(output, prior_size) -> str`, and `wait_detached_startup(state_dir, pid, output, *, prior_size=0, prior_lifecycle=None, poll_child=child_exit, sleep=time.sleep, clock=time.monotonic, timeout=SERVE_STARTUP_TIMEOUT_S, interval=SERVE_STARTUP_POLL_S) -> bool`. Validates finite `timeout >= 0` and finite `interval > 0` (raising `ValueError` otherwise). Polls `startup_confirmed` and `poll_child` before each sleep (and once after the final clamped sleep): returns `True` immediately once confirmed, raises `runner.Refusal` from newly appended `serve.out` output (preserving `"clutch engine: <msg> -- <road>"`) if the child exits early, and returns `False` if the child stays alive past `timeout`
- compatibility: `Serve` and `serve()` signatures and foreground lifecycle are unchanged
- acceptance: criteria 1 and 2
- tests: tests/unit/test_serve_detach.py
- post-merge source of truth: clutch/serve.py

### `clutch engine serve --detach` CLI and verb docs
- disposition: extend
- owner: clutch/__main__.py (parser and `handle_detach`), clutch/docs/host-running.md, docs/how-clutch-works.md, README.md
- consumers: operators, future `mcp-control-and-tickets`, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, `tests/integration/test_help.py`
- observable change: adds `--detach` (`action="store_true"`) to `engine serve`, updates `serve` `_command` `writes`, `lock`, `exits`, and `examples`, extends `handle_detach` to run both `engine drain --detach` and `engine serve --detach` (calling `serve.capture_startup_baseline` before `spawn` and `serve.wait_detached_startup` after `spawn` for `serve`, printing `serve: pid <pid>, output <output>` and returning `0`), and updates the `engine serve` documentation in `clutch/docs/host-running.md`, `docs/how-clutch-works.md` sections 2.1 and 10.1, and `README.md`
- compatibility: `clutch engine serve` without `--detach` and `clutch engine drain --detach` keep their exact behavior; `| \`engine serve\` |` keeps its column-1 name in `clutch/docs/host-running.md` so `clutch/help.py` (`verb.serve`) continues resolving without editing `clutch/help.py`
- acceptance: criteria 3, 4, and 5
- tests: tests/unit/test_main_serve_detach.py, tests/unit/test_main_engine_group.py, tests/unit/test_drain_detach_cli.py, tests/unit/test_main_help.py, tests/unit/test_host_running.py, tests/unit/test_readme.py, tests/integration/test_help.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/seams.py`: add `child_exit(pid: int) -> int | None`. Nothing else in `clutch/seams.py` changes.
- `clutch/serve.py`: add `SERVE_STARTUP_TIMEOUT_S`, `SERVE_STARTUP_POLL_S`, `capture_startup_baseline`, `startup_confirmed`, `_read_startup_tail`, and `wait_detached_startup` using injectable `poll_child`, `sleep`, and `clock` seams and validating `timeout >= 0` and `interval > 0`. Nothing in `Serve` or `serve()` changes.
- `clutch/__main__.py`: update `_command(engine_sub, "serve", ...)` `writes`, `lock`, `exits`, and `examples` (`["clutch engine serve", "clutch engine serve --detach"]`), add `--detach` on that subparser, generalize `handle_detach` for `args.engine_verb in {"drain", "serve"}` (calling `serve.capture_startup_baseline` and `serve.wait_detached_startup` when `engine_verb == "serve"`), and route `args.verb == "engine" and args.engine_verb in {"drain", "serve"} and args.detach` to `handle_detach()`. Nothing else in `clutch/__main__.py` changes.
- `clutch/docs/host-running.md`: update the `What it does` cell of `| \`engine serve\` | No | ... |` to document `--detach` (own session surviving terminal or editor closing, `<state_dir>/serve.out`, brief startup check / immediate refusal), keeping column 1 exact.
- `docs/how-clutch-works.md`: update the `engine serve` row in section 2.1 to `| \`engine serve [--detach]\` | yes | ... |` documenting `--detach` (`<state_dir>/serve.out` and startup check), and add `| \`serve.out\` | Output appended by \`engine serve --detach\`. |` immediately below `| \`drain.out\` |` in section 10.1.
- `README.md`: add `uv run clutch engine serve --detach  # run the continuous daemon detached` under `# Running`, keeping `uv run clutch engine serve` intact.
- New unit test files `tests/unit/test_serve_detach.py` and `tests/unit/test_main_serve_detach.py` using `tmp_path` and fake seams only (with `uv run clutch meta refresh` + non-empty `# purpose:` headers).
- Engine-written `# clutch:meta` header lines on newly created files under `tests/` updated by Check's meta step.

Scope out:
- `clutch/observe.py` (`extension_fields`, `engineVerbs`), `vscode-clutchwork/`, and `clutch/help.py`.
- `clutch/specs/ask/*.md` (`ask-specs-mcp-supervision`) and `clutch/mcp.py` (`mcp-control-and-tickets`).
- `clutch/drain.py`, `Serve.run` foreground lifecycle, `reexec_argv`, the host contract guide, and adding tests to existing test files or any of the seven hot test files.

Merge note with confirmed unmerged `panel-facts-journal-signal`: that ticket edits only `docs/how-clutch-works.md` section 9.6, while this ticket edits only sections 2.1 and 10.1, so either merge order preserves both edits.

## Scope fence
- clutch/seams.py
- clutch/serve.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_serve_detach.py
- tests/unit/test_main_serve_detach.py

## Acceptance criteria
1. `tests/unit/test_serve_detach.py`: `seams.child_exit` returns `None` on `(0, 0)` or `ChildProcessError` and returns the exit code on an exited status; `serve.capture_startup_baseline` reads existing `serve.out` size and `control/active.json` `lifecycle_id` (returning `(0, None)` when absent); `serve.startup_confirmed` returns `False` when `clutch.lock` is missing, has another `pid`, or has `verb != "serve"`, or when `control/active.json` is `null` or unchanged (`lifecycle_id == prior_lifecycle`), and returns `True` only when `clutch.lock` has `pid` + `"serve"` and `control/active.json` has a fresh non-empty `lifecycle_id`. Verified by `./dev.py test tests/unit/test_serve_detach.py`.
2. `tests/unit/test_serve_detach.py`: `serve.wait_detached_startup` returns `True` with zero `sleep` calls when already confirmed, returns `True` once confirmed during a fake `sleep`, raises `runner.Refusal` preserving `"clutch engine: <msg> -- <road>"` (ignoring bytes before `prior_size`) when `poll_child` returns exit `2`, raises `runner.Refusal` on unexpected exit `0` or exit `1`, returns `False` after a clamped final sleep and post-sleep poll when the child stays alive past `timeout`, and raises `ValueError` for `timeout=-1.0`, `timeout=float("nan")`, `interval=0.0`, or `interval=float("inf")`. Verified by `./dev.py test tests/unit/test_serve_detach.py`.
3. `tests/unit/test_main_serve_detach.py`: `_parser().parse_args(["engine", "serve"])` sets `detach is False` and `_parser().parse_args(["engine", "serve", "--detach"])` sets `detach is True`; `main(["engine", "serve", "--detach"], ...)` calls `spawn` once with `[sys.executable, "-m", "clutch", "engine", "serve"]` (no `--detach`), `cwd=repo`, `env=env`, `output=state_dir / "serve.out"`, prints `serve: pid 4242, output <output>` to stdout, and exits `0`; `main(["--config", str(cfg), "engine", "serve", "--detach"], ...)` forwards `["--config", str(cfg)]` before `"engine", "serve"`; an immediate refusal from `wait_detached_startup` exits `2` with a single-line `"clutch engine: "` message on stderr and empty stdout; invalid config exits `2` without calling `spawn`. Verified by `./dev.py test tests/unit/test_main_serve_detach.py`.
4. Existing engine CLI, drain-detach, help, host-running, README, and extension-fields tests pass unchanged (`./dev.py test tests/unit/test_main_engine_group.py tests/unit/test_drain_detach_cli.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_help.py tests/unit/test_observe_extension_fields.py tests/integration/test_help.py` exits `0`).
5. `clutch/docs/host-running.md` documents `--detach` and `<state_dir>/serve.out` in `| \`engine serve\` |`, `docs/how-clutch-works.md` documents `engine serve [--detach]` in section 2.1 and `serve.out` in section 10.1, `README.md` includes `uv run clutch engine serve --detach`, and both new unit test files pass `uv run clutch meta check tests/unit/test_serve_detach.py tests/unit/test_main_serve_detach.py`.

## Verification
```
./dev.py test tests/unit/test_serve_detach.py tests/unit/test_main_serve_detach.py tests/unit/test_main_engine_group.py tests/unit/test_drain_detach_cli.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_help.py tests/unit/test_observe_extension_fields.py tests/integration/test_help.py
uv run clutch meta check tests/unit/test_serve_detach.py tests/unit/test_main_serve_detach.py
```

## Definition of rejected
- Detached `engine serve` child argv includes `--detach`, or `clutch engine serve` without `--detach` stops running in the foreground.
- `wait_detached_startup` calls real `time.sleep` or `time.monotonic` when `sleep`/`clock` seams are passed, or mistakes another process's `clutch.lock` or a stale `control/active.json` for the new child's startup.
- An immediate child refusal during `serve --detach` returns exit `0` instead of surfacing the refusal with exit `2`.
- `clutch/seams.py`, `clutch/serve.py`, or `clutch/__main__.py` drops below its `test-gate.toml` unit coverage floor, or any file outside `## Scope fence` is modified.

## Time budget
- expected: 15m
- stuck: 30m
