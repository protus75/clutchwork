---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- projection-helpers-single-owner

## Context
- clutch/enginelog.py
- clutch/driver.py::Driver.from_config
- clutch/tickets.py::ticket_path
- tests/integration/test_projection_helpers_source.py

## On-demand
- clutch/stages.py
- clutch/observe.py
- clutch/runner.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/triage.py
- clutch/retro.py
- clutch/events.py
- clutch/__main__.py
- tests/integration/test_daemon_composition.py
- tests/unit/test_drain_driver_overlap.py
- tests/unit/test_driver_hooks.py

## Goal / Why
Roadmap row 146, the part of row 125 that `projection-helpers-single-owner` left out. Three facts each get one owner, and a source scan keeps them there.

1. `Driver.from_config` builds its `EngineLog` through `enginelog.engine_log`, passing the same `Redactor` object it gives the `Spool`. Today it calls `EngineLog(...)` directly. Afterwards `driver.log` and `driver.spool` hold one shared redactor.
2. The `engine.log` file name has one owner in `clutch/enginelog.py`: a name constant and `engine_log_path(state)`. The reads in `clutch/observe.py` (two `read_lines` sites), the watch glob in `clutch/observe.py`, the read in `clutch/events.py::poll`, the display path in `clutch/stages.py`, and `engine_log` itself use it. No other module spells `engine.log`.
3. Paths to the per-ticket files `run.md`, `review.md`, `checks.json`, `diagnosis.json`, `rework.md` and `attempts/<n>/harvest.json` have one owner in `clutch/tickets.py`, next to `ticket_path`. Today about 30 sites in `stages.py`, `merge.py`, `mergequeue.py`, `runner.py`, `triage.py`, `retro.py` and `__main__.py` rebuild them with f-strings or `/` chains.

Why: a change to where a ticket file or the log lives then happens in one place, and the scan fails when a copy returns.

## Boundary contract
### Engine log construction
- disposition: extend
- owner: clutch/enginelog.py (`engine_log`)
- consumers: `Driver.from_config`; existing callers in drain, runner, serve, triage
- observable change: `engine_log` takes the `Redactor` from its caller. `Driver.from_config` passes the redactor it gave the Spool. Other callers pass `Redactor.from_config(config, env)`. Log lines are scrubbed exactly as before.
- compatibility: log line format, rotation and path unchanged. No dual signature. Every caller is updated in the same change.
- acceptance: `driver.log` and `driver.spool` share one redactor object. A configured secret never reaches `engine.log`.
- tests: new unit test; existing `tests/integration/test_driver.py` secret test; updated `tests/unit/test_projection_helpers_single_owner.py`
- post-merge source of truth: clutch/enginelog.py

### Engine log path
- disposition: extend
- owner: clutch/enginelog.py (new `ENGINE_LOG_FILE` and `engine_log_path`)
- consumers: `clutch/observe.py`, `clutch/events.py`, `clutch/stages.py`, `engine_log`
- observable change: none visible. The same path is read, watched and displayed.
- compatibility: the watch glob string stays byte-identical, so the extension watcher is unchanged.
- acceptance: no `engine.log` literal outside `clutch/enginelog.py`.
- tests: new unit test; source scan
- post-merge source of truth: clutch/enginelog.py
- (rule for `create`: the name and function are added to the existing owner module, so no new owner is created.)

### Ticket artifact paths
- disposition: extend
- owner: clutch/tickets.py (beside `ticket_path`)
- consumers: stages, merge, mergequeue, runner, triage, retro, `__main__`
- observable change: none. Every path produced is byte-identical to today's.
- compatibility: `ticket_path` is unchanged. Spec files read from `specs_dir` (for example `rework.md`, `review.md`) are not ticket artifacts and stay as they are.
- acceptance: the source scan finds no literal artifact file name used as a ticket path outside `clutch/tickets.py`.
- tests: new unit test for the returned strings; source scan
- post-merge source of truth: clutch/tickets.py

## Scope in / Scope out
Scope in:
- `clutch/enginelog.py`: add `ENGINE_LOG_FILE`, `engine_log_path(state)`, and give `engine_log` a redactor argument.
- Update every `engine_log` caller to the new signature: `clutch/drain.py`, `clutch/runner.py`, `clutch/serve.py`, `clutch/triage.py`. `Driver.from_config` in `clutch/driver.py` calls `engine_log` with its shared redactor and drops the direct `EngineLog(` call and any import left unused.
- Replace the `engine.log` literals in `clutch/observe.py` (both reads and the watch glob), `clutch/events.py` and `clutch/stages.py` with the owner.
- `clutch/tickets.py`: add name constants for the six artifacts and one path helper that returns the repo-relative string for a ticket artifact, plus one for an attempt's `harvest.json`. Replace the rebuilt paths in `stages.py`, `merge.py`, `mergequeue.py`, `runner.py`, `triage.py`, `retro.py`, `__main__.py` and the `observe.py` surface-to-file map.
- `tests/integration/test_projection_helpers_source.py`: extend the scan so `EngineLog(` is allowed only in `enginelog.py::engine_log` (drop the `Driver.from_config` allowance), `engine.log` is allowed only in `enginelog.py`, and the artifact names are allowed only in `tickets.py`. Add rejecting and permitting cases to its table.
- `tests/unit/test_projection_helpers_single_owner.py`: `test_engine_log_uses_config_env_and_clock` changes to pass `Redactor.from_config(config, env)` to `engine_log(config, redactor, clock)`. It keeps its log path and its `[REDACTED:KEY]` assertions. This is the only edit in that file.
- `tests/integration/test_daemon_composition.py`: change the expected `redactor` trace entries only if the change alters the count or order of `Redactor.from_config` calls. This is the one expectation that may change.
- Fake configs in tests that replace `engine_log` through `install_log` or `lambda *args: log` and then run a real caller: callers now call `Redactor.from_config(config, env)` themselves, which reads `config.providers` and `config.release`. In each fixture below, give the fake config `providers=[]` and `release=SimpleNamespace(pypi_token='')`. Every event and behavior assertion stays as it is; no other edit is allowed in these files.
  - `tests/unit/test_phase_events.py`: the `config = SimpleNamespace(state_dir=Path('/state'))` used with `runner.prepare_pipeline` and the one used with `drain._Drain._run_retro`.
  - `tests/unit/test_verdict_extension.py`: the `config=SimpleNamespace(state_dir=PurePath('state'))` used with `drain.settle_admissions(checkout)`.
  - `tests/unit/test_drain_driver_overlap.py`: the `rig` fixture's `config=SimpleNamespace(state_dir=tmp_path)` (line 22), which reaches `drain._Drain._run_driver`.
  - `tests/unit/test_driver_hooks.py`: `test_drain_runs_driver_between_tickets`'s `config=SimpleNamespace(state_dir=tmp_path)` (line 58), which reaches `drain._Drain._run_driver`.
- New `tests/unit/test_projection_leftovers.py`.

Scope out: the `KNOWN_ARTIFACTS` mapping, the `evidence/` and `reference/` directories, `prior.diff`, the roadmap row (the driver strikes it), and any behavior change. If a site cannot use the owner without changing behavior, leave it and name it in the run record. If another test outside the fence fails only because its fake config lacks `providers` or `release`, stop and name it in the run record rather than editing it.

## Scope fence
- clutch/enginelog.py
- clutch/driver.py
- clutch/tickets.py
- clutch/observe.py
- clutch/events.py
- clutch/stages.py
- clutch/merge.py
- clutch/mergequeue.py
- clutch/runner.py
- clutch/triage.py
- clutch/retro.py
- clutch/drain.py
- clutch/serve.py
- clutch/__main__.py
- tests/integration/test_projection_helpers_source.py
- tests/integration/test_daemon_composition.py
- tests/unit/test_projection_helpers_single_owner.py
- tests/unit/test_projection_leftovers.py
- tests/unit/test_phase_events.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_drain_driver_overlap.py
- tests/unit/test_driver_hooks.py

## Acceptance criteria
1. `Driver.from_config(...)` returns a driver whose `log` and `spool` use the same `Redactor` object, checked with `assert driver.log._redactor is driver.spool._redactor`, not two equal-valued objects. Check: `./dev.py test tests/unit/test_projection_leftovers.py`.
2. An event carrying a configured secret value written through `engine_log(config, redactor, clock)` leaves `[redacted]`-style scrubbed text in the file, never the secret. Check: `./dev.py test tests/integration/test_driver.py`.
3. `engine_log_path(Path('s'))` returns `Path('s/engine.log')`, and the watch glob built in `observe.py` equals `{journal/*.jsonl,queue.json,engine.log,box/*.json}` byte for byte. Check: `./dev.py test tests/unit/test_projection_leftovers.py`.
4. The ticket artifact helpers return `tickets/<stem>/run.md`, `review.md`, `checks.json`, `diagnosis.json`, `rework.md` and `tickets/<stem>/attempts/<n>/harvest.json` as strings, identical to the old f-strings, not `Path` objects. Check: `./dev.py test tests/unit/test_projection_leftovers.py`.
5. The source scan fails on an `EngineLog(` call in `driver.py::Driver.from_config`, on an `engine.log` literal outside `enginelog.py`, and on an artifact file name used as a ticket path outside `tickets.py`. It passes on the real tree, and `specs_dir / "rework.md"` is not flagged. Check: `./dev.py test tests/integration/test_projection_helpers_source.py`.
6. The composition trace pin matches the real sequence, and the provider, preflight and driver ordering assertions still hold. Check: `./dev.py test tests/integration/test_daemon_composition.py`.
7. `test_engine_log_uses_config_env_and_clock` passes with the new `engine_log(config, redactor, clock)` signature and still asserts `[REDACTED:KEY]` in the log, not the raw secret. Check: `./dev.py test tests/unit/test_projection_helpers_single_owner.py`.
8. The drain driver tests that replace `engine_log` still pass with their fake configs carrying `providers=[]` and `release`. Check: `./dev.py test tests/unit/test_drain_driver_overlap.py tests/unit/test_driver_hooks.py tests/unit/test_phase_events.py tests/unit/test_verdict_extension.py`.
9. No behavior regression across drain, runner, merge, triage and retro. Check: `./dev.py test tests/integration tests/unit`.

## Verification
```
./dev.py test tests/unit/test_projection_leftovers.py tests/unit/test_projection_helpers_single_owner.py tests/integration/test_projection_helpers_source.py tests/integration/test_daemon_composition.py tests/integration/test_driver.py tests/unit/test_phase_events.py tests/unit/test_verdict_extension.py tests/unit/test_drain_driver_overlap.py tests/unit/test_driver_hooks.py
./dev.py test tests/integration tests/unit
```

## Definition of rejected
A behavior change in a produced path, log line or glob; a compat shim or second `engine_log` signature; a new owner module; a scan that flags spec-file reads under `specs_dir`; or an edit to a file outside the fence.

## Time budget
- expected: 30m
- stuck: 60m