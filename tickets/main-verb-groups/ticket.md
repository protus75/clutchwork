---
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
none

## Context
- docs/roadmap.md#2.3
- clutch/__main__.py
- clutch/runner.py::Refusal
- clutch/lockfile.py

## Goal / Why
Roadmap row 20 (`main-verb-groups`), the `__main__.py` half. Today `clutch/__main__.py` writes the same plumbing over and over. The writer-lock acquire/try/release is written once per lock-holding verb (retro, roadmap, release, publish, dismiss, triage, and the control verbs pause/resume/kill/stop in `_control`), seven `Lockfile(` calls in all. The `_require_engine` + `control.read_active` + `ValueError -> Refusal` sequence is written more than once. `observe.Context(...)` is built twice. `lambda: load_config(...)` is repeated. Several verbs print an ad-hoc `clutch <verb>: <message>` line with `print(..., file=sys.stderr); return 2` next to the shared exception handler at the end of `main`. After this change each of these has one definition in `clutch/__main__.py`, and the verb handlers sit in named groups: utilities, projections, authoring, control, lock holders. A lock, engine-submit, context or error-print change then needs one edit, and the next verb cannot copy a fifth variant. Behavior, output text and exit codes stay exactly as they are.

## Scope in / Scope out
Scope in, all inside `clutch/__main__.py`:
- One async context manager (for example `_locked(checkout, verb)`) owns `Lockfile(...)` construction, `acquire()` and `release()`. Every lock-holding verb handler uses it, including `_control`. `_retro` and `_control` keep their `LockHeld` fallbacks, which catch the exception from entering the wrapper. The wrapper resolves `Lockfile` from module globals at call time (no default argument, no captured reference, no early binding), so tests that swap `entry.Lockfile` (tests/unit/test_lock_holder.py) keep working.
- One helper owns the `_require_engine(exc)` check, the `control.read_active` read with its `ValueError -> runner.Refusal("current control identity unavailable", ...)` mapping, and `control.publish_request`. Every site that does this sequence calls it.
- One builder returns the `observe.Context` that `prompt drafts` and `watch`/`snapshot` use.
- One helper returns the `lambda: load_config(path, cwd=repo)` reloader assigned to `checkout.control.load_config`.
- One error printer writes `clutch <verb>: <message>` to stderr. The `except` clauses at the end of `main` and the `clutch <verb>:` prints inside verb handlers (`covgate` twice, `stats`) call it. Where a handler returns 2 after its print, it returns `runner.EXIT_REFUSED` through the printer. The exact message text of each existing print is unchanged. Two prints are deliberate exceptions and stay as they are, because they carry no `clutch <verb>: ` prefix today: the `probe` print `unknown providers: ...; declared providers: ...` and the `issue` warning `issue: config did not load, so no secrets were scrubbed: ...` (which continues and exits 0).
- The verb branches of `main` are split into handler functions grouped under the five group names above, with a dispatch table from verb to handler. Verb names, argparse definitions and the order of admission checks are unchanged.
- Names that other modules or tests import or monkeypatch keep their names, signatures and module-level bindings: `main`, `build_control`, `_status`, `_parser`, `_engine_signals`, `_control`, `_verdict`, `_retro`, `_order`, `_lint`, `_review`, `_new`, `build_serve`, `build_daemon_core`, `build_notifications`, `build_driver`, and the module attributes `Lockfile`, `control`, `load_config`, `SubprocessExec`, `ProviderLLM` and `Redactor`. Handlers such as `_control`, `_verdict` and `_retro` stay callable with a SimpleNamespace checkout as tests/unit/test_lock_holder.py does.
- Unit seam: the error printer and the lock wrapper take their inputs as plain arguments (a verb name, a message, a lock path or checkout), so a `tests/unit/` test runs their new lines with `tmp_path` and `capsys` and no process, repo file or network. The AST-shape and `main(...)` end-to-end checks, which read `clutch/__main__.py` or run a full verb, stay under `tests/integration/`.

Scope out (a separate ticket, because its fence spans the runner, stages, driver, triage, eval and about 30 test files):
- `Checkout` and `StageContext` carrying `log` and `box`.
- `Driver.from_config` taking the journal.
- Any change to `clutch/runner.py`, `clutch/stages.py`, `clutch/driver.py` or `clutch/triage.py`.
- The other duplication-table rows (closed sets, last-transition fold, signal bodies).

No existing test changes are forced: existing tests call `main(...)` and the preserved names listed above, which stay.

## Scope fence
- clutch/__main__.py
- tests/integration/test_main_verb_groups.py
- tests/unit/test_main_verb_groups.py

## Acceptance criteria
1. In `clutch/__main__.py`, `ast` finds exactly one call to `Lockfile(`; the test fails on today's seven. Checked by `./dev.py test tests/integration/test_main_verb_groups.py`.
2. `ast` finds exactly one call to `control.read_active` and exactly one call to `_require_engine`, both inside the engine-submit helper. The test fails on today's three call sites for `_require_engine`.
3. `ast` finds exactly one call to `observe.Context(` and exactly one `load_config(` lambda; the test fails on today's two and six.
4. `ast` finds every `print(..., file=sys.stderr)` call that emits a `clutch <verb>: ` line inside the one error-printer function. The only other `print(..., file=sys.stderr)` calls in `main` and the verb handlers are the `probe` unknown-providers print and the `issue` config warning, whose text is unchanged. The test fails on today's ad-hoc `clutch <verb>:` prints (covgate x2, stats).
5. A test runs `main(["prompt", "box"])` in a `tmp_path` host and asserts stderr is `clutch prompt: box prompt requires ids -- name at least one box id\n` with return value `runner.EXIT_REFUSED`, not an uncaught `Refusal`. The prefix, message and road are copied from the current handler output, not changed.
6. A test in the same file takes the lock with `Lockfile` in a `tmp_path` host, then runs `main(["dismiss", "box-000001"])`. It asserts return value `runner.EXIT_REFUSED` and a stderr line that names the holder verb. This proves the wrapper maps `LockHeld` the way the shared handler did, and still releases the lock afterward, so the lock file the test took is the only one present.
7. `./dev.py test` passes with every pre-existing test unchanged, so output text and exit codes of all verbs are preserved, including tests/unit/test_lock_holder.py, which swaps `entry.Lockfile` and calls `_control`, `_verdict` and `_retro`, and tests/unit/test_probe_verb.py.
8. `tests/unit/test_main_verb_groups.py` runs the error printer under `capsys` and asserts stderr is exactly `clutch <verb>: <message>\n` and the return value is `runner.EXIT_REFUSED`, not `0` or `None`. It also enters the lock wrapper on a `tmp_path` lock path, asserts a second entry raises `LockHeld` while the first is held, and asserts a third entry succeeds after the first exits, not still raising. Checked by `./dev.py test tests/unit/test_main_verb_groups.py`.

## Verification
```
./dev.py test tests/unit/test_main_verb_groups.py
./dev.py test tests/integration/test_main_verb_groups.py
./dev.py test tests/unit/test_lock_holder.py tests/unit/test_probe_verb.py tests/unit/test_menu_admission.py tests/integration/test_cli.py tests/integration/test_drain.py tests/integration/test_status.py tests/integration/test_triage.py tests/integration/test_review_command.py tests/integration/test_control_cli.py
```

## Definition of rejected
The branch changes any verb's stdout, stderr text or exit code (including the unprefixed `probe` and `issue` stderr text), renames or removes any name in the preserved list in Scope in, binds `Lockfile` early in the wrapper, edits any file outside the fence, adds a compat shim or second lock path beside the wrapper, or touches `Checkout`, `StageContext` or `Driver.from_config`.

## Time budget
- expected: 60m
- stuck: 120m
