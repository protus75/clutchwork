---
state: draft
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- exec-seam-owns-reap

## Context
- clutch/seams.py::GroupExec
- clutch/providers.py::CliAdapter.invoke
- clutch/evidence/schema.py::Rusage
- docs/evidence-trail-plan.md#Target design

## Goal / Why
Merged row 29 (`evidence-envelope`) left its rusage piece unbuilt: `clutch/providers.py::CliAdapter.invoke` writes `"rusage": None` into every `end.json`. `exec-seam-owns-reap` makes the exec seam report each child's own user CPU seconds, system CPU seconds and peak RSS in KB through `on_rusage`. After this ticket `CliAdapter.invoke` records them in `end.json` as `rusage: {user_s, sys_s, max_rss_kb}`. Resource use cannot be rebuilt after the call ends; the evidence plan keeps it to tell resource exhaustion from model failure.

## Scope in / Scope out
In:
- `CliAdapter.invoke` passes `on_rusage` only when `capture is not None`, stores what the seam reports, and writes it as `rusage` in `end.json`. When the seam never calls it (a fake exec, or a spawn error), `rusage` stays `None`.
- Fixed-signature exec fakes reached by a capture-on call (they answer `argv[0] == "git"` and have no `**kwargs`) each gain an `on_rusage=None` keyword on their `run`, and a fake that delegates to a real exec passes it through: `tests/integration/test_providers.py` (two fakes, lines 78 and 430), `tests/integration/test_daemon_composition.py` (line 79), `tests/harness/daemon_soak.py` (line 132), `tests/harness/reliability_battery.py` (line 86) and `tests/harness/shakeout/providers.py` (line 23). That keyword and its pass-through are the only edit in each file; `test_daemon_composition.py` is forced, so the hot-file rule allows it.

Out:
- `clutch/seams.py` and `clutch/docs/host-contract.md`: `exec-seam-owns-reap` owns them.
- No schema change. `Rusage` and `End.rusage` already exist.
- No change to `Parsed`, the journal or normalizers. Fakes that accept `**kwargs` (`tests/unit/test_evidence_envelope.py`, `tests/integration/test_drain.py`, `tests/integration/test_watchdog_activation.py`) are not edited and keep working.
- No new config knob.

Seam for tests: `tests/unit/test_evidence_rusage_record.py` drives `CliAdapter.invoke` with a fake exec that calls `on_rusage`, with no process.

## Scope fence
- clutch/providers.py
- tests/unit/test_evidence_rusage_record.py
- tests/integration/test_providers.py
- tests/integration/test_daemon_composition.py
- tests/harness/daemon_soak.py
- tests/harness/reliability_battery.py
- tests/harness/shakeout/providers.py

## Acceptance criteria
1. `tests/unit/test_evidence_rusage_record.py`: with a fake exec that calls `on_rusage` with user 1.5, sys 0.25 and max RSS 20480, the `end.json` written by `CliAdapter.invoke` has `rusage == {"user_s": 1.5, "sys_s": 0.25, "max_rss_kb": 20480}`, not `None`.
2. `tests/unit/test_evidence_rusage_record.py`: with a fake exec that never calls `on_rusage`, `end.json` has `rusage` equal to `None` and the call still succeeds.
3. `tests/unit/test_evidence_rusage_record.py`: when the fake exec calls `on_rusage` and then raises `TimeoutError`, `end.json` has `exit.status == "timeout"` and a non-`None` `rusage`.
4. `tests/unit/test_evidence_rusage_record.py`: with `capture=None`, the fake exec's `run` receives no `on_rusage` keyword, not `on_rusage=None`.
5. `./dev.py test tests/integration/test_providers.py tests/integration/test_daemon_composition.py tests/integration/test_reliability_battery.py tests/integration/test_shakeout.py tests/integration/test_daemon_soak.py` exits 0, so a capture-on call through each edited fake completes with no `TypeError`.

## Verification
```
./dev.py test tests/unit/test_evidence_rusage_record.py tests/unit/test_evidence_envelope.py tests/integration/test_evidence_envelope.py
./dev.py test tests/integration/test_providers.py tests/integration/test_daemon_composition.py tests/integration/test_reliability_battery.py tests/integration/test_shakeout.py tests/integration/test_daemon_soak.py
```

## Definition of rejected
The branch is thrown away if any of these hold:
- `CliAdapter.invoke` still writes `None` when the seam supplied figures.
- `CliAdapter.invoke` passes `on_rusage` on a call with no capture.
- Fakes that accept `**kwargs` and are left unedited stop working.
- A second capture path or a compat shim is added.

## Time budget
- expected: 25m
- stuck: 50m
