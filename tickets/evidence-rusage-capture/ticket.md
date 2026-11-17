---
state: draft
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/seams.py::GroupExec
- clutch/seams.py::SubprocessExec
- clutch/providers.py::CliAdapter.invoke
- clutch/evidence/schema.py::Rusage
- docs/evidence-trail-plan.md#Target design

## Goal / Why
Merged row 29 (`evidence-envelope`) left its rusage piece unbuilt. `clutch/providers.py::CliAdapter.invoke` writes `"rusage": None` into every `end.json`, and the exec seam in `clutch/seams.py` reports nothing about the child's resource use. After this ticket the exec seam reports the child's user CPU seconds, system CPU seconds and peak RSS in KB. `CliAdapter.invoke` records them in `end.json` as `rusage: {user_s, sys_s, max_rss_kb}`. Resource use cannot be rebuilt after the call ends. The evidence plan keeps it to tell resource exhaustion from model failure.

## Scope in / Scope out
In:
- `clutch/seams.py` gains a pure helper `rusage_figures(ru)` that turns an `os.wait4` resource struct (fields `ru_utime`, `ru_stime`, `ru_maxrss`) into a `clutch.evidence.schema.Rusage` with `user_s`, `sys_s` and `max_rss_kb`, applying the platform unit conversion (`ru_maxrss` is KB on Linux, bytes on macOS). It does no I/O, so a unit test runs it with a fake struct.
- `GroupExec.run` and `SubprocessExec.run` in `clutch/seams.py` gain an optional keyword `on_rusage: Callable[[Rusage], None] | None = None`. `SubprocessExec.run` calls it once, after the child is reaped, with `rusage_figures` of that child's own struct. The figures must be per child, not a `RUSAGE_CHILDREN` delta, because concurrent calls share the process. One option is `os.wait4` on the pid on a worker thread in place of the asyncio wait; the mechanism is the implementer's choice.
- A call that is killed or times out still reports rusage when the child was reaped.
- `CliAdapter.invoke` passes `on_rusage` only when evidence capture is on, the same condition under which it passes `on_stdout_line`. It stores the result and writes it as `rusage` in `end.json`. When the seam never calls it (a fake exec, or a spawn error), `rusage` stays `None`.
- Fixed-signature fakes reached by a capture-on call (they answer `argv[0] == "git"` and have no `**kwargs`) each gain an `on_rusage=None` keyword on their `run`: `tests/integration/test_providers.py` (two fakes, lines 78 and 430), `tests/integration/test_daemon_composition.py` (line 79), `tests/harness/daemon_soak.py` (line 132), `tests/harness/reliability_battery.py` (line 86) and `tests/harness/shakeout/providers.py` (line 23). That one keyword is the only edit in each file; `test_daemon_composition.py` is forced, so the hot-file rule allows it.
- Update the exec-seam paragraph in `clutch/docs/host-contract.md` that describes `on_stdout_line` so it also names `on_rusage`. Change nothing else in that document.

Out:
- No schema change. `Rusage` and `End.rusage` already exist.
- No change to `Parsed`, the journal or normalizers. Fakes that accept `**kwargs` (`tests/unit/test_evidence_envelope.py`, `tests/integration/test_drain.py`, `tests/integration/test_watchdog_activation.py`) are not edited and keep working.
- No new config knob.

Seam for tests: `rusage_figures` is the in-fence seam for the new `clutch/seams.py` lines, so `tests/unit/test_seams_rusage.py` runs them with a fake struct and no process. `tests/unit/test_evidence_rusage_record.py` drives `CliAdapter.invoke` with a fake exec that calls `on_rusage`. Real-process checks live under `tests/integration/`.

## Scope fence
- clutch/seams.py
- clutch/providers.py
- clutch/docs/host-contract.md
- tests/unit/test_seams_rusage.py
- tests/unit/test_evidence_rusage_record.py
- tests/integration/test_evidence_rusage_exec.py
- tests/integration/test_providers.py
- tests/integration/test_daemon_composition.py
- tests/harness/daemon_soak.py
- tests/harness/reliability_battery.py
- tests/harness/shakeout/providers.py

## Acceptance criteria
1. `tests/unit/test_seams_rusage.py`: `rusage_figures` on a fake struct with `ru_utime` 1.5, `ru_stime` 0.25 and `ru_maxrss` 20480 returns `user_s == 1.5`, `sys_s == 0.25` and `max_rss_kb == 20480` on Linux, not zeros and not bytes-scaled values.
2. `tests/unit/test_evidence_rusage_record.py`: with a fake exec that calls `on_rusage` with user 1.5, sys 0.25 and max RSS 20480, the `end.json` written by `CliAdapter.invoke` has `rusage == {"user_s": 1.5, "sys_s": 0.25, "max_rss_kb": 20480}`, not `None`.
3. `tests/unit/test_evidence_rusage_record.py`: with a fake exec that never calls `on_rusage`, `end.json` has `rusage` equal to `None` and the call still succeeds.
4. `tests/unit/test_evidence_rusage_record.py`: when the fake exec calls `on_rusage` and then raises `TimeoutError`, `end.json` has `exit.status == "timeout"` and a non-`None` `rusage`.
5. `tests/integration/test_evidence_rusage_exec.py`: `SubprocessExec().run` on a real Python child that burns CPU for about 0.2s calls `on_rusage` exactly once with `user_s + sys_s > 0` and `max_rss_kb > 0`, not zeros.
6. `tests/integration/test_evidence_rusage_exec.py`: two children run concurrently through one `SubprocessExec`, one allocating about 200 MB and one allocating almost nothing. The first reports a `max_rss_kb` at least 100000 above the second, so the figures are per child and not a shared `RUSAGE_CHILDREN` delta.
7. `tests/integration/test_evidence_rusage_exec.py`: `SubprocessExec().run` with no `on_rusage` still returns `(rc, out, err)` unchanged, and `on_stdout_line` delivery still includes the EOF tail.
8. `tests/integration/test_providers.py tests/integration/test_daemon_composition.py`: a capture-on call through each edited fake completes with no `TypeError`, checked by `./dev.py test tests/integration/test_providers.py tests/integration/test_daemon_composition.py` exiting 0.
9. `clutch/docs/host-contract.md` names `on_rusage` in the exec-seam paragraph, checked by `rg -n on_rusage clutch/docs/host-contract.md` printing at least one line.

## Verification
```
./dev.py test tests/unit/test_seams_rusage.py tests/unit/test_evidence_rusage_record.py tests/integration/test_evidence_rusage_exec.py tests/unit/test_evidence_envelope.py tests/integration/test_evidence_envelope.py tests/integration/test_providers.py tests/integration/test_daemon_composition.py tests/integration/test_host_contract.py
```

## Definition of rejected
The branch is thrown away if any of these hold:
- Rusage comes from a `RUSAGE_CHILDREN` delta that concurrent calls share.
- `CliAdapter.invoke` still writes `None` when the seam supplied figures.
- Fakes that accept `**kwargs` and are left unedited stop working.
- A second capture path or a compat shim is added.

## Time budget
- expected: 30m
- stuck: 60m
