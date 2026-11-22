---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- clutch/runner.py::pipeline
- clutch/runner.py::prepare_pipeline
- clutch/__main__.py::_preflighted_llm
- clutch/__main__.py::build_daemon_core
- clutch/providers.py::ProviderSession
- clutch/providers.py::ProviderLLM.preflight
- clutch/serve.py::Serve.run_retro
- docs/how-clutch-works.md#8.1 Providers
- tests/unit/test_phase_events.py
- tests/regress_phase_step_kinds.py

## Goal / Why
Provider preflight runs once per lock-held engine session, not once per ticket. Today it runs on every ticket dispatch under `engine drain`, `engine run` and `engine serve`. Triage, retro and the idle supervise pass run it again on top of that. Evidence: one drain session logged 9 preflights, and serve logged two within seconds because two tickets dispatched in parallel. Each preflight runs `--version` and `pnpm view` per CLI and sends a live probe call to every routed model. That costs 10-20 s per dispatch, and each extra probe is another chance for a flaky failure to stop the engine (serve stopped on one at 02:30:39 in the evidence). The documented contract in `docs/how-clutch-works.md` section 8.1 already says preflight runs at the start of `engine run`/`engine drain`/`engine serve`. This restores that contract.

Causes:
- Drain and run: `runner.pipeline`'s `PreparedDispatch.__call__` sets `self.callback = None` in its `finally`, so `prepare()` never finds a prepared callback and preflights again for the next ticket.
- Serve: `build_daemon_core`'s `dispatch` calls `prepare_pipeline` on every dispatch. Serve's `run_retro` and its idle `make_ctx` do the same, and triage goes through `_preflighted_llm`.

This deliberately replaces the clause in frozen `CLUTCH_PLAN.md` 19 (scheduler activation) that asks for "no stale preflight result reused across daemon admissions". Rebinding the config snapshot per admission stays. Re-probing an unchanged provider set per admission goes.

## Boundary contract
### Provider preflight per session
- disposition: extend
- owner: clutch/providers.py
- consumers: `runner.prepare_pipeline` (drain, run, serve dispatch, serve retro, serve idle supervise) and `__main__._preflighted_llm` (triage in drain and serve, and the other verbs that call it)
- observable change: `ProviderSession` remembers a successful preflight together with the snapshot's `providers` and `routing`. A later preflight on the same session whose snapshot has equal `providers` and `routing` probes nothing (no `--version`, `pnpm view`, or probe call), returns no problems, and writes no `phase_start`/`phase_end` preflight events. Concurrent callers on one session share one probe run instead of each probing. A config reload that changes `providers` or `routing` probes again. A failed or raising preflight is not remembered, so the next caller probes again.
- compatibility: a new lock-held session still preflights every routed (provider, model) pair before admitting work, including auth-excluded providers (CLUTCH_PLAN 19 provider-cooldown-failover release road). Refusal text and paved road are unchanged. Per-admission snapshot binding (`bind`, Driver, StageContext per snapshot) is unchanged. Eval's direct `llm.preflight()` on its own fresh session is unchanged.
- acceptance: two dispatches on one session with an unchanged snapshot run the probe commands once, and a changed `routing` runs them again
- tests: `tests/unit/test_preflight_once_per_session.py`, `tests/regress_preflight_once_per_session.py`
- post-merge source of truth: clutch/providers.py

## Scope in / Scope out
Scope in:
- Hold the remembered preflight on `ProviderSession`, which already has exactly one instance per lock-held session (`build_control`) and already marks the startup pass (`preflight_passed`). Use an `asyncio.Lock` (or a shared task) so concurrent callers do not each probe.
- Make `runner.prepare_pipeline` and `__main__._preflighted_llm` skip the probe, and `prepare_pipeline` skip its `phase_start`/`phase_end` preflight events, when the session already passed for equal `providers` and `routing`. When `checkout.control.providers` is `None` (test seams), keep probing every time.
- Update the preflight bullet in `docs/how-clutch-works.md` section 8.1: preflight runs once per engine session and again only after a config reload changes `providers` or `routing`.
- Add `tests/unit/test_preflight_once_per_session.py` covering the new lines, and the carried reproducer `tests/regress_preflight_once_per_session.py`. The reproducer calls `runner.prepare_pipeline` twice on one checkout whose `control.providers` is a real `ProviderSession`, with a scripted exec seam and `bind` stubbed. It counts probe exec calls and prints `pass` when the second call adds none, `defect` when it adds some, and `error` on any exception. It uses only APIs that exist on the merge base.
- Adjust `tests/unit/test_phase_events.py` and `tests/unit/test_preflight_parallel.py` only where their fakes lack a session attribute the change reads.

Scope out:
- `PreparedDispatch`'s `callback = None` reset and per-admission `bind`. Rebinding stays per ticket, and only the probe is shared.
- Logging the preflight problem list on failure (separate concern, not filed).
- The `provider` probe verb, which always probes by design.
- Any edit to `tests/integration/test_daemon_composition.py`. Its config-edit case changes a provider model, so it still probes twice.
- The frozen plan document.

## Scope fence
- clutch/providers.py
- clutch/runner.py
- clutch/__main__.py
- docs/how-clutch-works.md
- tests/unit/test_preflight_once_per_session.py
- tests/unit/test_phase_events.py
- tests/unit/test_preflight_parallel.py
- tests/regress_preflight_once_per_session.py

## Acceptance criteria
1. Two `runner.prepare_pipeline` calls on one session with an equal snapshot run the `--version`, `pnpm view` and probe commands once in total, not twice. Checked by `tests/unit/test_preflight_once_per_session.py`.
2. A second call whose snapshot changes `routing` runs the probes again, not zero times. Checked by `tests/unit/test_preflight_once_per_session.py`.
3. After a first preflight returns problems, the next call probes again instead of returning the remembered failure or an empty list. Checked by `tests/unit/test_preflight_once_per_session.py`.
4. Two concurrent `prepare_pipeline` calls on one fresh session run the probes once, not twice. Checked by `tests/unit/test_preflight_once_per_session.py`.
5. A skipped preflight writes no `phase_start`/`phase_end` preflight events, so the engine log holds exactly one pair, not two. Checked by `tests/unit/test_preflight_once_per_session.py`.
6. The reproducer prints `{"regression_result": "pass"}` on the branch: `uv run python tests/regress_preflight_once_per_session.py`.
7. The full suite passes: `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_preflight_once_per_session.py tests/unit/test_phase_events.py tests/unit/test_preflight_parallel.py
uv run python tests/regress_preflight_once_per_session.py
./dev.py test
```

## Definition of rejected
- A new session admits work without probing every routed pair.
- A failed preflight is reused instead of re-probed.
- Per-admission snapshot binding is cached or removed.
- `tests/integration/test_daemon_composition.py` is edited.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_preflight_once_per_session.py
```
- carries: tests/regress_preflight_once_per_session.py
