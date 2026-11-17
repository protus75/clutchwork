---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/seams.py::GroupExec
- clutch/seams.py::SubprocessExec
- clutch/seams.py::_kill_and_wait
- clutch/seams.py::_read_pipe
- clutch/evidence/schema.py::Rusage
- tests/waiting.py
- tests/integration/test_host_contract.py::test_host_contract_seam_inventory

## Goal / Why
Roadmap row 123 (`evidence-rusage-capture`) needs each child's own resource use, and only `os.wait4` on that child returns it. `SubprocessExec.run` spawns through `asyncio.create_subprocess_exec`, and asyncio's child watcher reaps the child with `os.waitpid` as soon as it exits, so the seam never sees that child's rusage (`tickets/evidence-envelope/ticket.md` Goal). A second waiter on the same pid races the watcher: on 2026-11-17 (Python 3.14.6, pidfd watcher) a worker-thread `os.wait4` beside an asyncio spawn won 5 of 6 times, and asyncio then logged "exit status already read" and reported returncode 255 instead of the child's 3; the sixth `os.wait4` raised `ChildProcessError`. A `resource.getrusage(RUSAGE_CHILDREN)` delta is wrong too: its `ru_maxrss` is the largest child ever reaped, so the delta is 0 for any child after a larger one, and concurrent children's CPU lands in each other's delta.

After this ticket the seam spawns its child outside asyncio's child watcher and reaps it itself with `os.wait4`, and `run` takes an optional `on_rusage` callback that receives that child's user and system CPU seconds and peak RSS in KB. The return value and every other exec contract stay as they are.

## Scope in / Scope out
In:
- `clutch/seams.py`: `SubprocessExec.run` spawns with `subprocess.Popen` (`start_new_session=True`, the same cwd, env, stdin and pipes) instead of `asyncio.create_subprocess_exec`. It reads stdout and stderr through asyncio pipe readers with `_read_pipe`, waits for exit without blocking the event loop (a pidfd reader or a dedicated thread, the implementer's choice), and reaps with `os.wait4(pid, 0)`. The return code comes from that wait status through `os.waitstatus_to_exitcode`, so a signal-killed child still returns a negative code. After the reap it sets the `Popen` object's `returncode`, so `subprocess` never polls the reaped pid again.
- Timeout and outer cancellation still kill the group through `_kill_and_wait(proc)`, which still calls `kill_group(proc.pid)`, then drain both pipes and reap. The unbounded (`timeout=None`) path still inherits stdio. Keep those two names: `tests/integration/test_host_contract.py::test_host_contract_seam_inventory` pins them in the source.
- A pure helper `rusage_figures(ru) -> Rusage` turns an `os.wait4` resource struct (`ru_utime`, `ru_stime`, `ru_maxrss`, which Linux reports in KB) into `clutch.evidence.schema.Rusage`. It does no I/O, so a unit test runs it on a fake struct. A second pure helper `reap_outcome(status, ru, on_rusage) -> int` holds the rest of the reap logic: it converts the `os.wait4` status with `os.waitstatus_to_exitcode`, calls `on_rusage(rusage_figures(ru))` once when `on_rusage` is set, and returns the exit code; `SubprocessExec.run` calls it after every reap. Only the process calls themselves (`Popen`, the exit wait, `os.wait4`) stay outside these helpers; the integration tests cover them, and the unit check's coverage of `clutch/seams.py` stays at or above its floor in `test-gate.toml`.
- `GroupExec.run` and `SubprocessExec.run` gain `on_rusage: Callable[[Rusage], None] | None = None`. After every reap, including after a timeout or cancellation kill, `SubprocessExec.run` calls it once with `rusage_figures` of that child's struct, before it returns or re-raises.
- `tests/waiting.py::ready_before_returning_spawn` patches the seam's new spawn point instead of `asyncio.create_subprocess_exec`, so it still waits for `ready` after the child starts and before `run`'s timeout window opens, and on failure still kills the group and reaps.
- `clutch/docs/host-contract.md`: in the exec-seam paragraph that describes `on_stdout_line`, add one sentence naming `on_rusage`. Change nothing else in that document.

Out: `clutch/providers.py` and every exec fake (`evidence-rusage-capture` wires the callback); `ProcessExec.run`'s signature; `spawn_detached`; `replace`; any `RUSAGE_CHILDREN` use; any new config knob.

## Scope fence
- clutch/seams.py
- tests/waiting.py
- clutch/docs/host-contract.md
- tests/unit/test_seams_rusage.py
- tests/integration/test_exec_seam_reap.py

## Acceptance criteria
1. `tests/unit/test_seams_rusage.py`: `rusage_figures` on a fake struct with `ru_utime` 1.5, `ru_stime` 0.25 and `ru_maxrss` 20480 returns `Rusage(user_s=1.5, sys_s=0.25, max_rss_kb=20480)`, not zeros and not bytes-scaled values.
2. `tests/unit/test_seams_rusage.py`: `reap_outcome` on a status built with `os.waitstatus_to_exitcode`-compatible values for exit code 3 returns 3, for signal 9 returns -9, calls a recording `on_rusage` exactly once with `rusage_figures` of the fake struct, and with `on_rusage=None` returns the code and calls nothing.
3. `tests/integration/test_exec_seam_reap.py`: twenty concurrent `SubprocessExec().run` calls on a Python child that exits with code 3 each return rc 3, not 255, and `caplog` holds no `asyncio` record containing "exit status already read" or "Unknown child process".
4. `tests/integration/test_exec_seam_reap.py`: `SubprocessExec().run` on a real Python child that burns CPU for about 0.2s calls `on_rusage` exactly once with `user_s + sys_s > 0` and `max_rss_kb > 0`, not zeros.
5. `tests/integration/test_exec_seam_reap.py`: two children run concurrently through one `SubprocessExec`, one allocating about 200 MB and one allocating almost nothing; the first reports a `max_rss_kb` at least 100000 above the second, so the figures are per child and not a shared `RUSAGE_CHILDREN` delta.
6. `tests/integration/test_exec_seam_reap.py`: a child that sleeps past a 0.3s timeout makes `run` raise `TimeoutError`, `on_rusage` was called exactly once before it, and `tests.waiting.group_exited` is true for its pgid.
7. `tests/integration/test_exec_seam_reap.py`: `SubprocessExec().run` with no `on_rusage` returns `(rc, out, err)` unchanged, and `on_stdout_line` delivery still includes the EOF tail.
8. `./dev.py test tests/integration/test_git.py tests/integration/test_providers.py tests/integration/test_host_contract.py` exits 0, so the group-kill, drain, consumer-failure and source-pin contracts hold with the new spawn.
9. `rg -n on_rusage clutch/docs/host-contract.md` prints at least one line.

## Verification
```
./dev.py test tests/unit/test_seams_rusage.py tests/integration/test_exec_seam_reap.py
./dev.py test tests/integration/test_git.py tests/integration/test_providers.py tests/integration/test_host_contract.py
./dev.py test tests/unit
```

## Definition of rejected
- The seam still spawns through an asyncio subprocess API and reads rusage beside asyncio's child watcher.
- Rusage comes from `resource.getrusage(RUSAGE_CHILDREN)`.
- `run`'s return value, group kill, drain on unwind, or consumer-failure behavior changes.
- `tests/waiting.py::ready_before_returning_spawn` no longer intercepts the spawn.

## Time budget
- expected: 40m
- reason: moving the spawn and taking the reap are one change: a moved spawn without the `os.wait4` reap yields no rusage, and a reap beside the asyncio spawn races its watcher (returncode 255).
- stuck: 80m
