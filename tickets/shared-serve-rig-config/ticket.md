---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
none

## Context
- tests/integration/test_cli.py::CONFIG
- tests/integration/test_stages.py::CONFIG
- tests/integration/test_providers.py::CONFIG
- tests/harness/shakeout/bench.py::_CONFIG
- tests/integration/serve_rig.py::admission_config
- tests/integration/serve_rig.py::notify_command
- tests/integration/test_serve_parallel_admission.py::parallel_rig
- tests/integration/test_restart_timers.py::repository

## Goal / Why
Serve and drain integration tests each carry their own copy of the test `config.yaml` text. When an engine change needs a config route or field (for example a review route for identity-based approval), each copy breaks separately and tickets miss some. After this ticket one new module, `tests/config_fixture.py`, owns the minimal test config text and the YAML edit helper that serve rigs use, so a future config requirement edits one place.

The module exposes `build_config(*, state_dir, providers, routing, inventory) -> str`, whose no-argument result is the text of the `CONFIG` literal in `tests/integration/test_cli.py` today, with keyword overrides for the providers, routing entries, state directory and safety inventory, plus `amend_config(root, **sections)`, which loads `root/config.yaml`, sets each given top-level key (a `None` value removes it) and writes it back. The four config literals (`test_cli`, `test_stages`, `test_providers`, `bench`) are rebuilt through `build_config` with byte-identical text, so every caller's resulting config is unchanged. Production code does not change.

## Boundary contract
### Test config builder
- disposition: create
- owner: tests/config_fixture.py
- consumers: tests/integration/test_cli.py, tests/integration/test_stages.py, tests/integration/test_providers.py, tests/harness/shakeout/bench.py, tests/integration/serve_rig.py, tests/integration/test_serve_parallel_admission.py, and every test module that imports `CONFIG` from the first three
- observable change: one module builds the minimal valid `config.yaml` text and edits its top-level sections; callers pass keyword overrides instead of holding a literal; each former literal's text is byte-identical
- compatibility: the names `CONFIG` in `tests/integration/test_cli.py`, `tests/integration/test_stages.py` and `tests/integration/test_providers.py` and `_CONFIG` in `tests/harness/shakeout/bench.py` stay, now assigned from `build_config(...)`, so every importer (`from tests.integration.test_cli import CONFIG`, and the same from `test_stages` and `test_providers`) works with no edit
- acceptance: `build_config()` loads through `load_config`; each override appears in the loaded `Config`; the rebuilt literals equal their former text
- tests: tests/unit/test_config_fixture.py and tests/integration/test_config_fixture_adoption.py
- post-merge source of truth: tests/config_fixture.py
- closest existing: the `CONFIG` literals in `tests/integration/test_cli.py::CONFIG`, `tests/integration/test_stages.py::CONFIG`, `tests/integration/test_providers.py::CONFIG` and `tests/harness/shakeout/bench.py::_CONFIG`, and the yaml load/dump in `tests/integration/serve_rig.py::admission_config` and `tests/integration/serve_rig.py::notify_command` and `tests/integration/test_serve_parallel_admission.py::parallel_rig`; none is importable by the others without making a test module depend on another test module's literal, and none takes overrides
- earning reason: consolidation of evidenced duplicates (four config literals and three YAML rewriters that already drifted per file)

### Production config schema
- disposition: reuse
- owner: clutch/config.py
- consumers: `load_config` in every migrated test
- observable change: none; the builder emits text the existing loader already accepts
- compatibility: no production file changes
- acceptance: `git diff --stat` shows only paths under `tests/` and `tickets/`
- tests: tests/unit/test_config_fixture.py loads the built text with `load_config`
- post-merge source of truth: clutch/config.py

## Scope in / Scope out
In:
- Create `tests/config_fixture.py` with `build_config` and `amend_config` as described in Goal. The default text is the `tests/integration/test_cli.py` `CONFIG` text; overrides cover the provider entries (name, auth, per-tier models, concurrency, `est_cost_per_call_usd`), the routing entries including a `model:` on a candidate, `state_dir`, and `engine_plane_safety_inventory`. Callers that append sections (`CONFIG + "worktree_root: ...\n"`) keep doing so by string concatenation.
- Rebuild `CONFIG` in `tests/integration/test_cli.py`, `tests/integration/test_stages.py` and `tests/integration/test_providers.py`, and `_CONFIG` in `tests/harness/shakeout/bench.py`, as `build_config(...)` calls whose text is byte-identical to the literal each replaces. The `test_providers` text keeps `state_dir: state`, both providers, the four routes and `engine_plane_safety_inventory: []`, because `.replace(...)` calls in that file and in `tests/integration/test_daemon_composition.py` match its exact lines.
- `tests/integration/test_cli.py`, `tests/integration/test_stages.py` and `tests/integration/serve_rig.py` are hot files; they are fenced only because the migrated literal or rewriter lives in them. Edit only the config literal or rewriter and the import it needs.
- Rewrite `admission_config` and `notify_command` in `tests/integration/serve_rig.py`, and `parallel_rig` in `tests/integration/test_serve_parallel_admission.py`, to call `amend_config` instead of their own `yaml.safe_load`/`safe_dump`. Drop the `yaml` import from a file that no longer uses it.
- New tests: `tests/unit/test_config_fixture.py` (builder and `amend_config` behavior on `tmp_path`) and `tests/integration/test_config_fixture_adoption.py` (the migrated files hold no config literal).

Out:
- Production code, `config.yaml` at the repo root and the config schema do not change.
- `tests/integration/test_daemon_composition.py` is not edited: its config comes from the `test_providers` `CONFIG` and `CoreRig.put_config` only writes the text it is handed, so it holds no literal. `tests/integration/test_restart_timers.py` is not edited for the same reason.
- The retro-section text append in `tests/integration/serve_rig.py` stays a string concatenation on the built text.
- Other test files that hold their own config text (for example `tests/integration/test_ladder.py`, `tests/integration/test_policy.py`, `tests/integration/test_driver.py`, `tests/integration/test_config.py` and the `tests/regress_*.py` reproducers) are out; they test config parsing or their own shapes and are not part of the serve rig chain.
- No file under `tests/integration/test_serve_admission.py`, `tests/integration/test_host_loop.py`, `tests/harness/host_loop.py` or `tests/integration/test_serve_dispatch.py` is touched; they call `admission_config` with the same signature.

## Scope fence
- tests/config_fixture.py
- tests/unit/test_config_fixture.py
- tests/integration/test_config_fixture_adoption.py
- tests/integration/test_cli.py
- tests/integration/test_stages.py
- tests/integration/test_providers.py
- tests/harness/shakeout/bench.py
- tests/integration/serve_rig.py
- tests/integration/test_serve_parallel_admission.py

## Acceptance criteria
1. `build_config()` with no arguments equals the pre-change `tests/integration/test_cli.py` text (`schema_version: 1`, `state_dir: .clutch/state`, one `claude` provider, one `implement` route, `engine_plane_safety_inventory: [config.yaml]`), and loads through `load_config` with `config.providers` naming `claude`: `./dev.py test tests/unit/test_config_fixture.py`. Overriding a provider name, `state_dir` and the inventory shows in the loaded `Config`, not the default values.
2. `amend_config(root, review=..., notify=None)` sets `review` and removes `notify` in `root/config.yaml` and leaves every other key as it was, and a second call keeps the first call's keys: `./dev.py test tests/unit/test_config_fixture.py`.
3. `CONFIG` in `tests/integration/test_cli.py`, `tests/integration/test_stages.py` and `tests/integration/test_providers.py`, and `_CONFIG` in `tests/harness/shakeout/bench.py`, each equal the text of the literal they replaced (for `test_providers`, the `textwrap.dedent` result with its trailing newline): the implementer compares `git show HEAD:<file>` text to the new value before finishing, and `./dev.py test tests/integration/test_providers.py tests/integration/test_cli.py tests/integration/test_stages.py` passes, where the `.replace("x-med", ...)` and `.replace("limits: {concurrency: 1}", ...)` tests in `test_providers.py` would fail on a changed line.
4. No migrated file holds a config literal: a test reads the files through a `Path(__file__)` anchor and asserts that none of `tests/integration/test_cli.py`, `tests/integration/test_stages.py`, `tests/integration/test_providers.py`, `tests/harness/shakeout/bench.py`, `tests/integration/serve_rig.py` or `tests/integration/test_serve_parallel_admission.py` contains a line matching `^\s*providers:`, and that each of the first four imports `build_config` while the last two import `amend_config` and none calls `yaml.safe_dump`: `./dev.py test tests/integration/test_config_fixture_adoption.py`.
5. Every importer of the retained names still passes, including the serve and daemon rigs that build their config from them: `./dev.py test tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_merge_overlap.py tests/integration/test_serve_notify.py tests/integration/test_daemon_pause.py tests/integration/test_release.py tests/integration/test_merge.py`.
6. Production code is unchanged: `git diff --name-only main` lists only paths under `tests/` and `tickets/`, checked by review.

## Verification
```
./dev.py test tests/unit/test_config_fixture.py tests/integration/test_config_fixture_adoption.py tests/integration/test_cli.py tests/integration/test_stages.py tests/integration/test_providers.py tests/integration/test_serve_parallel_admission.py tests/integration/test_serve_merge_overlap.py tests/integration/test_serve_notify.py tests/integration/test_daemon_pause.py tests/integration/test_release.py tests/integration/test_merge.py
```

## Definition of rejected
- Any file outside the fence changes, or any `clutch/` production file changes.
- A migrated config text differs from the literal it replaces, or a test's expected value is edited to make a migration pass.
- A migrated file still holds a `providers:` config literal, or `build_config` has a second copy of the default text (a compat shim or dual path).
- A new test is added to `tests/integration/test_cli.py`, `tests/integration/test_stages.py` or `tests/integration/serve_rig.py`.

## Time budget
- expected: 25m
- stuck: 50m
