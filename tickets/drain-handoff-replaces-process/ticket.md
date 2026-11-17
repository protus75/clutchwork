---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
none

## Context
- clutch/seams.py
- tests/integration/test_drain_upgrade.py

## On-demand
- clutch/drain.py
- clutch/serve.py
- tests/integration/test_serve_upgrade.py
- tests/integration/serve_rig.py
- tests/integration/test_drain.py
- tests/integration/test_daemon_composition.py
- docs/how-clutch-works.md

## Goal / Why
After a self-upgrade handoff, the old engine process is gone and the new one has taken its place, so a long run keeps one engine process however many handoffs happen. Today `clutch/drain.py` awaits `reexec.run(reexec_argv(...), timeout=None)` after the lock is released, and `clutch/serve.py` does the same in its handoff branch. The parent python (about 130 MB RSS, plus its uv wrapper) stays resident for the child's whole life. A ps capture from 2026-11-16 shows three nested handoffs in 30 minutes with 7 live drain-related processes holding about 650 MB. Since driver-loop the drain rarely quiesces, so each engine-plane merge adds another waiting parent. Replacing the process in place keeps the pid, so the caller still receives the final exit code.

## Scope in / Scope out
Scope in:
- Add a new Protocol `ReplaceExec` in `clutch/seams.py` with `async def replace(self, argv, *, cwd, env) -> int`. Do not add the method to `ProcessExec` or `GroupExec`, so their other fakes stay valid.
- `SubprocessExec.replace` raises `ExecutableNotFound` when `argv[0]` does not resolve on `env["PATH"]`, as `run` does. Otherwise it flushes `sys.stdout` and `sys.stderr`, then does `os.chdir(cwd)` then `os.execvpe(argv[0], argv, dict(env))` and never returns. The flush is needed because exec runs no atexit handlers and block-buffered output (such as `drain --detach` writing to `drain.out`) would otherwise be lost. Fakes return the child's exit code instead.
- In `clutch/drain.py`, the handoff calls `reexec.replace(reexec_argv([...]), cwd=..., env=...)` instead of `reexec.run(..., timeout=None)`. The argv, the `--parked` and `--deadline` carrying, and the order journaled, journal closed, lock released, then replace do not change. Change the `reexec` annotation to `ReplaceExec`.
- In `clutch/serve.py`, the handoff branch calls `self.reexec.replace(reexec_argv(self.argv, engine=self.engine), cwd=c.repo, env=c.env)` and returns its code.
- Reword the comment in `SubprocessExec.run` in `clutch/seams.py` that names the drain's self-upgrade handoff child as the one unbounded caller, so it says unbounded (`timeout=None`) callers stream through inherited stdio, without naming the handoff. No behavior change.
- Update the fakes that stand in for the handoff child so they implement `replace` and not `run`: the handoff fakes in `tests/integration/test_drain_upgrade.py`, `tests/integration/test_serve_upgrade.py`, `tests/integration/serve_rig.py` (`UpgradeChild`), and the `Child` and `handoff` fakes in `tests/integration/test_drain.py` and `tests/integration/test_daemon_composition.py`. Change only those fakes and the assertions that read their recorded call. A fake `NoChild` that never expects a handoff stays untouched.
- In `tests/integration/test_drain_upgrade.py`, rename `test_the_unbounded_handoff_spawn_streams_through_inherited_stdio` to a name that describes unbounded `run` callers without naming the handoff; its behavior is unchanged.
- In `docs/how-clutch-works.md`, update the sentence about the drain self-upgrade re-exec to say the process is replaced in place, and reword the serve handoff sentence in section 7.2 (the one saying serve releases the lock and spawns the new serve) to say serve replaces its process in place. Do not touch other sections.
- In `clutch/docs/host-contract.md`, the `async run(...)` bullet's parenthetical stops naming the self-upgrade handoff: `None` is only for unbounded callers, which inherit stdio and return empty out/err.
- Drop `timeout is None` from the `test_serve_upgrade.py` assertion that unpacks `(argv, cwd, env, timeout)`.

Scope out:
- `SubprocessExec.run` behavior and direct `timeout=None` callers in `tests/integration/test_git.py` and `clutch/covmap.py` are unchanged.
- The uv wrapper in `reexec_argv`: whether `uv run` execs python or keeps a wrapper process is not changed here. If wrapper processes still accumulate after this change, file that with `clutch suggest`.
- No new config, flags, or fallback to the old spawn path.

## Scope fence
- clutch/seams.py
- clutch/docs/host-contract.md
- clutch/drain.py
- clutch/serve.py
- docs/how-clutch-works.md
- tests/integration/test_drain_upgrade.py
- tests/integration/test_serve_upgrade.py
- tests/integration/serve_rig.py
- tests/integration/test_drain.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_handoff_replace.py
- tests/unit/test_seam_replace.py

## Acceptance criteria
1. In a drain whose merge changes `clutch/`, the fake `ReplaceExec` receives exactly one `replace` call carrying `reexec_argv` with the `--parked` and `--deadline` arguments, and it happens after the journal is closed and the lock is released; `./dev.py test tests/integration/test_drain_upgrade.py` passes with `run` never called on the handoff seam, not a call to `run(timeout=None)`.
2. In serve's upgrade path the fake receives one `replace` call with `reexec_argv(self.argv, engine=self.engine)`, and `serve()` returns the fake's exit code 7, not 0; `./dev.py test tests/integration/test_serve_upgrade.py` passes.
3. `SubprocessExec.replace` flushes `sys.stdout` and `sys.stderr`, then calls `os.chdir(cwd)` then `os.execvpe(argv[0], argv, env)` with the given values, and raises `ExecutableNotFound` for an unresolvable binary without calling exec; `./dev.py test tests/unit/test_seam_replace.py` passes, with `os.chdir`, `os.execvpe` and the flush monkeypatched, and the test asserts the flush happened before `os.execvpe`, not after.
4. A real process that calls `SubprocessExec().replace` to run a python that exits 7 keeps its pid and its parent sees exit code 7, not a second child pid. Before calling `replace`, that process prints a line without flushing with stdout redirected to a file or pipe, and the captured output contains that line, not an empty capture; `./dev.py test tests/integration/test_handoff_replace.py` passes.
5. After the change, `grep -n "timeout=None" clutch/drain.py clutch/serve.py` prints nothing, so no engine handoff awaits an unbounded child; checked by `./dev.py test tests/integration/test_handoff_replace.py`, which reads both files and asserts that.
6. The handoff fakes in `tests/integration/test_drain.py` and `tests/integration/test_daemon_composition.py` still pass: `./dev.py test tests/integration/test_drain.py tests/integration/test_daemon_composition.py`.
7. The `SubprocessExec.run` comment no longer contains the text `self-upgrade handoff`, and `docs/how-clutch-works.md` no longer says serve releases the lock and spawns the new serve; checked by `./dev.py test tests/integration/test_handoff_replace.py`, which reads both files and asserts the old text is absent.

## Verification
```
./dev.py test tests/unit/test_seam_replace.py tests/integration/test_handoff_replace.py tests/integration/test_drain_upgrade.py tests/integration/test_serve_upgrade.py tests/integration/test_drain.py tests/integration/test_daemon_composition.py
```

## Definition of rejected
The branch keeps any awaited unbounded child spawn in the drain or serve handoff, adds a fallback path that still spawns and waits, or changes the order journaled, journal closed, lock released, then handoff.

## Time budget
- expected: 60m
- stuck: 120m
