---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/config.py::Scheduler
- clutch/config.py::Limits
- clutch/config.py::Route
- clutch/doctor.py
- clutch/providers.py::candidates
- docs/how-clutch-works.md#11. Config

## Goal / Why
Roadmap row 42, parallel plan ticket 3. After this ticket `config.yaml` accepts an experimental `scheduler.parallel` block with `enabled` (default false), `max_runs` (default 2) and `shared_paths` (default empty), validated fail-closed. `clutch host doctor` adds a `parallel` row that reports FAIL when `enabled` is true and `max_runs` is greater than `limits.concurrency` of the provider serving the implement route. Nothing reads the block yet: dispatch stays single-flight, so `enabled: false` changes no behavior. The model, the doctor warning and the config table come first so the later dispatch tickets (`serve-parallel-dispatch`) have one config owner to read. A `max_runs` above the provider's slots gains nothing, because the runs wait on each other's model calls, and the operator should hear that before turning the switch on.

## Boundary contract
### Scheduler config model
- disposition: extend
- owner: clutch/config.py
- consumers: `load_config` and every reader of `config.scheduler`; the later `serve-parallel-dispatch` ticket
- observable change: `scheduler.parallel` is accepted with keys `enabled`, `max_runs` and `shared_paths`; an unknown key under it, a non-positive `max_runs`, or a `shared_paths` entry that is not repo-relative is refused with a config error that names the key
- compatibility: a config with no `parallel` key loads exactly as before and yields `enabled=False`, `max_runs=2`, `shared_paths=[]`; `scheduler.max_unmerged` is unchanged
- acceptance: valid and invalid blocks are checked through `load_config`
- tests: tests/unit/test_parallel_config.py
- post-merge source of truth: clutch/config.py

### Doctor parallel check
- disposition: extend
- owner: clutch/doctor.py
- consumers: `clutch host doctor` and `doctor.render`
- observable change: when `scheduler.parallel.enabled` is true and `max_runs` exceeds the `limits.concurrency` of the provider of the first candidate of the implement route at `routing_default_tier`, the results gain one row `parallel` with `passed=False` whose detail names `max_runs`, the provider and its concurrency, and the fix (lower `max_runs` or raise `limits.concurrency`). No row is added in any other case, including a config that fails to load and a missing implement route
- compatibility: the existing rows, their order and their text are unchanged; the row is absent whenever `enabled` is false, so every existing doctor test and output stays valid
- acceptance: the row appears only in the mismatch case
- tests: tests/unit/test_parallel_config.py
- post-merge source of truth: clutch/doctor.py

### Host contract config inventory
- disposition: extend
- owner: clutch/docs/host-contract.md
- consumers: tests/integration/test_host_contract.py::test_host_contract_schema_coverage
- observable change: the `config-fields` block gains a `Parallel` row, and the `Scheduler` and `Config` defaults include the new `parallel` default
- compatibility: existing rows are unchanged apart from the two defaults that must equal the dumped model defaults
- acceptance: the schema coverage test passes against the new model
- tests: tests/integration/test_host_contract.py
- post-merge source of truth: clutch/docs/host-contract.md

## Scope in / Scope out
In:
- Add a `Parallel` model nested under `Scheduler` in `clutch/config.py`, built from the existing `StrictModel`, `Count` and the repo-relative path rule already used there (`is_repo_relative`). `Scheduler.parallel` defaults to `Parallel()`.
- Add the `parallel` row to `doctor.check` in `clutch/doctor.py` after the `core` row, only in the mismatch case described above. Resolve the provider from `config.routing` and `config.providers` directly; do not change `clutch/providers.py`.
- Update the config table row for `scheduler`, `drain` in `docs/how-clutch-works.md` (section 11) to name `scheduler.parallel` as experimental and serve-only, with the three keys and defaults, and update the `host doctor` row in the verb table (section 2) to mention the parallel check. Edit only those two rows.
- Update the `host doctor` row in `clutch/docs/host-running.md` and the `does=` text of the doctor command in `clutch/__main__.py` (the string beginning `Check the venv, config load, git`) to mention the parallel check. Nothing else in `__main__.py` changes.
- In the `config-fields` block of `clutch/docs/host-contract.md`, add a `Parallel` row (`required: []`, `defaults: {enabled: false, max_runs: 2, shared_paths: []}`), change the `Scheduler` defaults to `{max_unmerged: 2, parallel: {enabled: false, max_runs: 2, shared_paths: []}}`, and change the `scheduler` entry in the `Config` defaults to match. Edit nothing else in that file.
- New tests in the new file tests/unit/test_parallel_config.py. They build a config under `tmp_path`, call `load_config` for the model cases, and call `doctor.check` with a fake exec returning git version output, as the existing doctor tests do, for the row cases. They add nothing to existing test files.

Out: any reader of `parallel` in the scheduler, daemon, drain or serve (a later ticket); the overlap check and chain order; `clutch/providers.py`; `config.yaml` of this repo; the extension; existing test files. This ticket does not change `scheduler.max_unmerged`.

## Scope fence
- clutch/config.py
- clutch/doctor.py
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- tests/unit/test_parallel_config.py

## Acceptance criteria
1. A config with no `scheduler.parallel` key loads with `scheduler.parallel.enabled is False`, `max_runs == 2` and `shared_paths == []`, not an error and not `None`; checked by `./dev.py test tests/unit/test_parallel_config.py`.
2. A config with `scheduler: {parallel: {enabled: true, max_runs: 3, shared_paths: [docs/how-clutch-works.md]}}` loads with those values; checked by `./dev.py test tests/unit/test_parallel_config.py`.
3. `max_runs: 0`, an unknown key such as `parallel: {bogus: 1}`, and a `shared_paths` entry of `/abs/path` each raise `ConfigError` rather than loading; checked by `./dev.py test tests/unit/test_parallel_config.py`.
4. With `enabled: true`, `max_runs: 3` and an implement-route provider whose `limits.concurrency` is 1, `doctor.check` returns a result named `parallel` with `passed` False whose detail contains `max_runs` and the provider name, and `doctor.render` starts with `doctor: failed`; checked by `./dev.py test tests/unit/test_parallel_config.py`.
5. With `enabled: true`, `max_runs: 2` and `limits.concurrency: 2`, and separately with `enabled: false` and `max_runs: 5`, `doctor.check` returns no row named `parallel`, not a passing one; checked by `./dev.py test tests/unit/test_parallel_config.py`.
6. The existing doctor tests still pass unchanged, so the row order and text of a default config are untouched; checked by `./dev.py test tests/integration/test_doctor.py tests/unit/test_main_host_group.py tests/unit/test_main_help.py`.
7. `scheduler.parallel`, its three keys and the doctor check appear in the docs rows named in Scope in; checked by review of the diff of `docs/how-clutch-works.md` and `clutch/docs/host-running.md` (no standing text test is added).
8. The `config-fields` inventory matches the models: the set of rows equals every `StrictModel` subclass including `Parallel`, and the `Scheduler` and `Config` defaults equal the dumped model defaults, not the old `{max_unmerged: 2}`; checked by `./dev.py test tests/integration/test_host_contract.py`.

## Verification
```
./dev.py test tests/unit/test_parallel_config.py tests/integration/test_doctor.py tests/integration/test_config.py tests/integration/test_host_contract.py tests/unit/test_main_host_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py
```

## Definition of rejected
The branch is thrown away if any code outside `config.py` and `doctor.py` reads `scheduler.parallel`, if a config without the key behaves differently from before, if the doctor row appears while `enabled` is false, or if a test is added to an existing test file.

## Time budget
- expected: 15m
- stuck: 30m
