---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/config.py::Release
- clutch/release.py
- config.yaml
- pyproject.toml
- .gitignore
- dev.py::build_ui_bundle
- clutch/mcp.py::ClutchMCPServer.dispatch
- clutch/docs/host-contract.md#Complete field inventory
- clutch/docs/host-running.md
- tests/unit/test_release_publish.py
- tests/integration/conftest.py
- tests/integration/test_mcp_app_dashboard.py

## On-demand
- clutch/__main__.py
- docs/how-clutch-works.md

## Goal / Why
`clutch mcp serve` serves the MCP App dashboard resource `ui://clutch/dashboard.html` from `clutch/ui/dashboard.html` inside the installed `clutchwork` package (`clutch/mcp.py::DEFAULT_DASHBOARD_HTML`). Because `clutch/ui/dashboard.html` is gitignored and `clutch release publish` runs `uv build` without first building the UI bundle (`config.yaml` `release.packages` runs only after publish for the VSIX), published `clutchwork` wheels and sdists omit `clutch/ui/dashboard.html`, causing `resources/read` to return `dashboard_unavailable` on PyPI and `uvx` installs.

When this ticket is done:
- Host configs can declare `release.pre_build` commands that `clutch release publish` (and therefore `clutch release ship`) runs with sanitized `child_env` before `uv build`, failing closed on any command error.
- This repo's `config.yaml` declares `["uv", "run", "python", "dev.py", "ui-bundle"]` under `release.pre_build`, so `uv_build` packages `clutch/ui/dashboard.html` into both the wheel and sdist while keeping `clutch/ui/dashboard.html` gitignored.
- Unit and real-I/O integration tests verify `release.pre_build` execution/failure handling and verify that a real `uv build` after `dev.build_ui_bundle` packages `clutch/ui/dashboard.html` into the `clutchwork` wheel and sdist and serves it through `ClutchMCPServer.dispatch("resources/read", ...)`.

## Boundary contract

### Host release configuration (Release.pre_build)
- disposition: extend
- owner: clutch/config.py
- consumers: `clutch/release.py::publish`, `clutch/docs/host-contract.md`, host `config.yaml` files
- observable change: `Release` accepts optional `pre_build: list[Argv] = []`, validating each entry as a non-empty list of strings under `StrictModel` (refusing explicit `null` or empty argv).
- compatibility: additive optional field with default `[]`; existing `config.yaml` files without `release.pre_build` remain valid with unchanged behavior.
- acceptance: `config.Release()` defaults `pre_build` to `[]`, valid argv lists parse, and `null` or `[]` entries raise `ValidationError` / `ConfigError`.
- tests: `tests/unit/test_release_pre_build.py`, `tests/unit/test_release_publish.py`, `tests/integration/test_host_contract.py`
- post-merge source of truth: clutch/config.py

### Release build pipeline (release.publish)
- disposition: extend
- owner: clutch/release.py
- consumers: `clutch release publish`, `clutch release ship`
- observable change: after verifying `publishable`, `uv version --short`, and the `HEAD` tag, and before invoking `uv build`, `publish()` runs each argv in `config.release.pre_build` via `exec_.run(argv, cwd=repo, env=child, timeout=BUILD_TIMEOUT_S)`. Any non-zero exit code, `TimeoutError`, or `ExecutableNotFound` raises `Refusal` and prevents `uv build` and `uv publish` from running.
- compatibility: hosts with `release.pre_build: []` execute the exact same `uv` commands in the same order as before.
- acceptance: `pre_build` commands run in order before `uv build` with sanitized `child_env` (no provider keys, no `pypi_token`, no `UV_PUBLISH_TOKEN`), and any failure raises `Refusal` before `uv build` or `uv publish`.
- tests: `tests/unit/test_release_pre_build.py`, `tests/unit/test_release_publish.py`, `tests/integration/test_mcp_dashboard_wheel.py`
- post-merge source of truth: clutch/release.py

## Scope in / Scope out

Scope in:
- `clutch/config.py`: add `pre_build: list[Argv] = []` to `Release`.
- `clutch/release.py`: in `publish()`, run each command in `config.release.pre_build` after tag verification and before `uv build`, using `cwd=repo`, `env=child` (from `child_env(env, config)`), and `timeout=BUILD_TIMEOUT_S`; raise `Refusal` with a paved road on non-zero return code, `TimeoutError`, or `ExecutableNotFound`.
- `config.yaml`: add `pre_build: [[uv, run, python, dev.py, ui-bundle]]` under `release` while preserving `publish: true` and `packages`.
- `clutch/__main__.py`: update `release publish` help text (`does` and `exits`) to note that configured `release.pre_build` commands run before `uv build` and refuse on failure.
- `clutch/docs/host-contract.md`: add `pre_build: []` to `Config.defaults.release` and `Release.defaults` in the `config-fields` YAML block, and document `release.pre_build` alongside `release.publish` / `release.pypi_token`.
- `clutch/docs/host-running.md`: update the `release publish` verb row to note `release.pre_build` runs before building.
- `docs/how-clutch-works.md`: update the `release publish` row in section 2.1 to note `release.pre_build` commands run before building into `state_dir/dist`.
- `tests/unit/test_release_publish.py`: add `pre_build=[]` to the `setup()` fake `Release` namespace and include `"pre_build": []` in the `config.Release().model_dump()` assertion.
- `tests/unit/test_release_pre_build.py`: new unit test module covering `Release.pre_build` validation, execution order before `uv build` / `uv publish`, secret stripping in `child_env`, and `Refusal` on non-zero rc, `TimeoutError`, and `ExecutableNotFound`.
- `tests/integration/conftest.py`: add `"test_mcp_dashboard_wheel.py"` to `REAL_IO_TESTS`.
- `tests/integration/test_mcp_dashboard_wheel.py`: new real-I/O integration test that checks `config.yaml` declares `["uv", "run", "python", "dev.py", "ui-bundle"]` in `release.pre_build`, runs `dev.build_ui_bundle` to produce `clutch/ui/dashboard.html`, builds wheel and sdist into `tmp_path / "dist"` with `uv build --clear -o <tmp_path/dist>` from the repo root (restoring `clutch/ui/dashboard.html` to its prior state in `finally` — deleting it if absent before the test, or restoring its original bytes if present), verifies `clutch/ui/dashboard.html` is present and non-empty in both the `.whl` and `.tar.gz`, extracts it from the `.whl` into `tmp_path`, and verifies `ClutchMCPServer(ui_html_path=extracted).dispatch("resources/read", {"uri": "ui://clutch/dashboard.html"})` returns `text/html;profile=mcp-app` HTML.

Scope out:
- Do not commit `clutch/ui/dashboard.html` to git or modify `.gitignore` or `pyproject.toml`.
- Do not modify `dev.py`, `clutch/mcp.py`, or `release.packages` behavior (`run_packages`).
- Do not add tests to any of the seven shared integration test files (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `test_cli.py`, `test_watch.py`, `serve_rig.py`).

## Scope fence
- clutch/config.py
- clutch/release.py
- clutch/__main__.py
- config.yaml
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_release_publish.py
- tests/unit/test_release_pre_build.py
- tests/integration/conftest.py
- tests/integration/test_mcp_dashboard_wheel.py

## Acceptance criteria
1. `config.Release()` defaults `pre_build` to `[]`, accepts non-empty `list[list[str]]`, and rejects `None` or an empty inner list `[]` (ruling out silent acceptance of invalid `pre_build` entries), verified by `./dev.py test tests/unit/test_release_pre_build.py`.
2. `clutch/release.py::publish` runs every `config.release.pre_build` command in order after tag verification and before `uv build` and `uv publish`, passing `child_env` with provider secrets and `pypi_token` stripped (ruling out running `pre_build` after `uv build`, skipping it, or leaking `UV_PUBLISH_TOKEN` / provider keys into it), verified by `./dev.py test tests/unit/test_release_pre_build.py`.
3. When any `config.release.pre_build` command exits non-zero, raises `TimeoutError`, or raises `ExecutableNotFound`, `clutch/release.py::publish` raises `Refusal` and invokes neither `uv build` nor `uv publish` (ruling out building or publishing a wheel missing pre-built assets), verified by `./dev.py test tests/unit/test_release_pre_build.py`.
4. Existing release publish and CLI help tests pass with the new `Release.pre_build` field and updated `release publish` help text, verified by `./dev.py test tests/unit/test_release_publish.py tests/unit/test_main_help.py tests/unit/test_main_release_group.py`.
5. `clutch/docs/host-contract.md` `config-fields` matches `clutch/config.py` including `Release.pre_build` (ruling out contract drift), verified by `./dev.py test tests/integration/test_host_contract.py`.
6. `config.yaml` declares `["uv", "run", "python", "dev.py", "ui-bundle"]` in `release.pre_build` (while keeping `release.packages` intact), and running `dev.build_ui_bundle` followed by `uv build --clear -o <tmp_path/dist>` produces both a `.whl` and `.tar.gz` containing non-empty `clutch/ui/dashboard.html` that `ClutchMCPServer.dispatch("resources/read", {"uri": "ui://clutch/dashboard.html"})` serves with `mimeType == "text/html;profile=mcp-app"` rather than raising `dashboard_unavailable`, while restoring `clutch/ui/dashboard.html` afterward, verified by `./dev.py test tests/integration/test_mcp_dashboard_wheel.py tests/integration/test_dev_vscode_package_kept.py`.

## Verification
```
./dev.py test tests/unit/test_release_pre_build.py tests/unit/test_release_publish.py tests/unit/test_main_help.py tests/unit/test_main_release_group.py tests/integration/test_host_contract.py tests/integration/test_mcp_dashboard_wheel.py tests/integration/test_dev_vscode_package_kept.py
```

## Definition of rejected
- Committing generated `clutch/ui/dashboard.html` to git or removing it from `.gitignore`.
- Hardcoding `dev.py ui-bundle` or `clutch/ui/dashboard.html` in engine-plane `clutch/release.py` instead of driving pre-build commands from `config.release.pre_build`.
- Passing `pypi_token`, `UV_PUBLISH_TOKEN`, or provider auth env vars to `release.pre_build` commands.
- Leaving `clutch/ui/dashboard.html` created or modified on disk after `tests/integration/test_mcp_dashboard_wheel.py` finishes, or writing build outputs to `/tmp` or the repo's `dist/`.
- Adding new tests to any of the seven do-not-grow integration test files.

## Time budget
- expected: 15m
- stuck: 30m
