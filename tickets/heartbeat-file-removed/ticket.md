---
state: draft
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- clutch/heartbeat.py
- clutch/daemon.py::HeartbeatCycle
- clutch/serve.py::Serve.maintenance
- docs/engine-state-db-plan.md#3. Command access
- docs/engine-state-db-plan.md#7. Migration
- tests/unit/test_serve_idle_poll.py

## On-demand
- docs/how-clutch-works.md
- tests/integration/test_heartbeat.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_serve_notify.py
- tests/integration/serve_rig.py
- tests/harness/daemon_soak.py
- tests/integration/test_daemon_soak_runner.py

## Goal / Why
`clutch/heartbeat.py` writes an empty file `state_dir/heartbeat` on every healthy serve loop (`HeartbeatCycle.cycle`, built in `Serve.__init__`, called from `Serve.maintenance`). Nothing in `clutch/`, `vscode-clutchwork/` or any test outside the heartbeat tests reads it: only tests assert its mtime. Liveness for `view status` and the extension already comes from the kernel-held writer lock (`clutch.lock`). The file is dead code and its docs describe a signal nobody uses.

After this ticket the file, `Heartbeat` and `HeartbeatCycle` are gone, no document says serve writes a heartbeat, and `docs/engine-state-db-plan.md` says the future endpoint answers a `ping` request that replaces a liveness file (owner request, 2026-11-22). No ping code is written here.

`HeartbeatCycle` does nothing beyond the file. Its `cycle()` evaluates four health probes (`Serve.healthy(0..4)`) only to decide whether to write the file, and `Serve.maintenance` ignores the returned bool. Nothing else reads those probes, so the class is removed whole.

## Boundary contract
### Serve heartbeat file
- disposition: replace
- owner: clutch/serve.py
- consumers: none; grep of `clutch/`, `vscode-clutchwork/` and `tests/` finds only the writer and tests that assert the file's mtime or count writes to it
- observable change: `serve` no longer creates or touches `state_dir/heartbeat`; `clutch.heartbeat` and `clutch.daemon.HeartbeatCycle` no longer exist; `Serve.maintenance` no longer calls a heartbeat cycle
- compatibility: no reader exists, so no migration; an existing `heartbeat` file left in a state dir is ignored. Liveness stays the kernel-held writer lock `clutch.lock`, which `view status` and the extension already use. Serve start, stop, loop-death handling and every other maintenance step are preserved.
- acceptance: a unit test runs `Serve.maintenance` against a real directory and finds no `heartbeat` file; `clutch.heartbeat` is not importable
- tests: new `tests/unit/test_serve_no_heartbeat_file.py`; heartbeat-only tests deleted; tests that used the file as a "serve looped" signal moved to another observable
- post-merge source of truth: `clutch/serve.py` and the writer lock `clutch.lock`

### Future liveness ping (plan text only)
- disposition: extend
- owner: docs/engine-state-db-plan.md
- consumers: the authors of the planned `state-verdict-ticket-service` and `state-service-handoff` tickets
- observable change: the plan's endpoint section and migration table state that the endpoint answers `ping`, that `clutch engine ping` calls it with a short timeout, and that the extension indicator uses the verb
- compatibility: documentation only; no shipped behavior, verb or code changes
- acceptance: reviewer reads the named plan sections
- tests: none; a plan document gets no standing text pin
- post-merge source of truth: docs/engine-state-db-plan.md

## Scope in / Scope out
Scope in:
- Delete `clutch/heartbeat.py`. In `clutch/daemon.py` delete `HeartbeatCycle` and the `Heartbeat` import. In `clutch/serve.py` delete the `HeartbeatCycle` and `Heartbeat` imports, the `self.heartbeat = HeartbeatCycle(...)` construction in `Serve.__init__`, and `self.heartbeat.cycle()` in `Serve.maintenance`. Keep `Serve.healthy`, `health_tasks` and `Responsiveness`: the planned ping reuses them.
- Remove the `"clutch/heartbeat.py" = 32` row from `test-gate.toml` (the file no longer exists).
- Docs: in `docs/how-clutch-works.md` drop "heartbeat (`state_dir/heartbeat` mtime)" from the maintenance sentence (section 6 area, around lines 550-551) and delete the `heartbeat` row of the state_dir table (around line 792). In `clutch/docs/host-contract.md` drop "and heartbeat" from the two state_dir ownership sentences (around lines 142 and 459), leaving the list grammatical. Edit only those sentences.
- Plan edit, documentation only, in `docs/engine-state-db-plan.md`: in section 3 "Command access", add that the service endpoint answers a `ping` request and that a new verb `clutch engine ping` calls it with a short timeout, where no answer means the engine is hung or dead and the verb exits non-zero; that this replaces any liveness file; and that the VS Code extension's engine-running indicator uses that verb instead of a file or the writer lock. In section 7 add the same to the Fence summary of row 1 `state-verdict-ticket-service` (endpoint, `ping` handler, `clutch engine ping` verb with its help and doc rows) and the extension indicator switch to the verb to row 5 `state-service-handoff` (when the writer lock retires). Write no verb, handler or extension change.
- Tests: delete `tests/integration/test_heartbeat.py`. In `tests/integration/test_serve_lifecycle.py` delete `test_serve_heartbeat_requires_responsive_components` and replace the heartbeat-file waits in `test_serve_consumers_use_existing_writers` with `rig.owner.ready.is_set()` or a maintenance-cycle count. In `tests/integration/serve_rig.py` change `activated_graph` to wait on `rig.owner.ready.is_set()`. In `tests/integration/test_serve_notify.py` replace the three heartbeat-file waits and the `write_fs` wrapper with a wrapper that counts `rig.owner.maintenance` calls. In `tests/harness/daemon_soak.py` remove `_FS.heartbeats`, the `write` override that fills it, and the heartbeat conditions in `recurring` and the final `need`; in `tests/integration/test_daemon_soak_runner.py` remove the `heartbeats` field param and assertions. In `tests/unit/test_callerless_code_removed.py` remove the `heartbeat` import and its `(heartbeat, "is_fresh")` row. In `tests/integration/test_serve_verdict_orphan_sweep.py` remove the stale `owner.heartbeat = SimpleNamespace(...)` line.
- New test file `tests/unit/test_serve_no_heartbeat_file.py`, modeled on the `owner` fixture of `tests/unit/test_serve_idle_poll.py` (copy what it needs; do not edit that file): it runs `Serve.maintenance` with `LocalFileSystem` under `tmp_path` and asserts the directory holds no `heartbeat` entry.
- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.

Scope out: `Serve.healthy`, `health_tasks`, `Responsiveness` and its tests; `tests/regress_reconcile_confirming_draft.py` (carried by a settled bug ticket; its stub line is harmless); merged-history text that mentions heartbeat (roadmap rows, `tickets/`); the extension and `view status` (they never read the file); any ping code, verb or endpoint; any other tests of the hot test files beyond the forced `serve_rig.py` edit above.

## Scope fence
- clutch/heartbeat.py
- clutch/daemon.py
- clutch/serve.py
- test-gate.toml
- docs/how-clutch-works.md
- clutch/docs/host-contract.md
- docs/engine-state-db-plan.md
- tests/unit/test_serve_no_heartbeat_file.py
- tests/unit/test_callerless_code_removed.py
- tests/integration/test_heartbeat.py
- tests/integration/test_serve_lifecycle.py
- tests/integration/test_serve_notify.py
- tests/integration/serve_rig.py
- tests/integration/test_serve_verdict_orphan_sweep.py
- tests/integration/test_daemon_soak_runner.py
- tests/harness/daemon_soak.py

## Acceptance criteria
1. `Serve.maintenance` run against a real `tmp_path` state dir leaves no `heartbeat` entry there, not a zero-byte file: `./dev.py test tests/unit/test_serve_no_heartbeat_file.py`.
2. `clutch.heartbeat` is not importable and `clutch.daemon` has no `HeartbeatCycle`, asserted in the same new test: `./dev.py test tests/unit/test_serve_no_heartbeat_file.py`.
3. No file under `clutch/` or `tests/` (excluding `tests/regress_reconcile_confirming_draft.py`, `tests/regress_control_fold_cached.py` and `tests/unit/test_control_fold_cached.py`, whose `heartbeat` is an unrelated signal name) mentions `heartbeat`: `grep -ril heartbeat clutch tests`.
4. The serve and soak tests that used the file as a "serve looped" signal still pass: `./dev.py test tests/integration/test_serve_lifecycle.py tests/integration/test_serve_notify.py tests/integration/test_daemon_soak_runner.py tests/integration/test_serve_verdict_orphan_sweep.py tests/unit/test_callerless_code_removed.py`.
5. `docs/how-clutch-works.md` and `clutch/docs/host-contract.md` no longer describe a heartbeat file: `grep -in heartbeat docs/how-clutch-works.md clutch/docs/host-contract.md` prints nothing.
6. `docs/engine-state-db-plan.md` section 3 says the endpoint answers `ping`, `clutch engine ping` calls it with a short timeout and exits non-zero on no answer, and the extension indicator uses the verb; section 7 rows 1 and 5 carry the same; reviewer reads those sections (one-time check, no standing test).
7. The whole suite is green with the coverage floor row removed: `./dev.py test`.

## Verification
```
./dev.py test
```

## Definition of rejected
Any ping verb, endpoint, handler or extension change is added; `Serve.healthy`, `health_tasks` or `Responsiveness` is removed; a compat stub for `Heartbeat` or `HeartbeatCycle` remains; the plan edit changes any plan decision other than adding the ping; a deleted heartbeat test is replaced by one that asserts the file exists.

## Time budget
- expected: 25m
- stuck: 50m
