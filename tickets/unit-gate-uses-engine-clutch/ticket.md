---
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Runs before
- cli-group-coverage

## Context
- config.yaml
- tests/integration/test_host_contract.py
- clutch/stages.py::run_host_command

## On-demand
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_mergequeue.py
- tests/integration/test_stages.py

## Goal / Why
The `unit` mechanical check in `config.yaml` runs the gate through the ticket worktree's own source (`uv run python -m clutch covgate -- ...`). Check reads that argv from main's config, so a branch that renames or removes the `covgate` verb (cli-group-coverage) fails its own Check with argparse exit 2 on every attempt. Any ticket that edits `clutch/covgate.py` also weakens the gate that judges it. After this ticket the unit argv starts with the installed engine's `clutch covgate --` and runs pytest through `uv run python -m pytest` inside it, so main's gate code judges the branch's tests. `clutch` is the console script beside the engine's interpreter: it imports the engine's code through its install, never the worktree's, unlike `python -m clutch` run in the worktree.

The command must resolve on every launch path. A drain or serve started under `uv run` or by the self-upgrade re-exec (`uv run --project <engine>`) has the engine's venv first on `PATH`. The extension's play button runs `.venv/bin/clutch engine drain --detach` with the editor's environment, whose `PATH` lacks that venv, and `--detach` passes it on unchanged, so a bare `clutch` would fail every Check with `executable not found: 'clutch'`. So the shared host-command runner, `clutch/stages.py::run_host_command` (used by Check, its base rerun, Verification, autofix and the merge queue's host checks), puts the directory of the engine's own interpreter, `Path(sys.executable).parent`, first on each command's `PATH`. Under `uv run` that directory is already first, so those launches see no change. This is an orchestration cause: it keeps breaking runs while it sits, so it is P0 and runs before cli-group-coverage.

## Scope in / Scope out
Scope in:
- `config.yaml`: change the `unit` argv prefix from `[uv, run, python, -m, clutch, covgate, --, python, -m, pytest, ...]` to `[clutch, covgate, --, uv, run, python, -m, pytest, ...]`. Every later argument stays byte-identical.
- `clutch/docs/host-contract.md`: change only the example `unit` argv line (the `argv: [uv, run, python, -m, clutch, covgate, --, ...]` line) to the same new prefix.
- `tests/integration/test_host_contract.py`: change only the pinned prefix assertion in `test_python_host_setup_loads` (the `unit.argv[:7] == [...]` line) to `unit.argv[:8] == ["clutch", "covgate", "--", "uv", "run", "python", "-m", "pytest"]`. Nothing else in the file changes; no test reads the repo's operator-owned `config.yaml`, whose argv criterion 1 checks once.
- `clutch/stages.py::run_host_command`: the env passed to `ctx.exec_.run` is `child_env(ctx.env, ctx.config)` with `str(Path(sys.executable).parent)` placed first on its `PATH`, joined with `os.pathsep`; when that env has no `PATH` or an empty one, `PATH` is the directory alone, never with an empty entry. Add the `os` and `sys` imports it needs. Nothing else in `stages.py` changes.
- `tests/unit/test_stages_host_path.py` (new): calls `stages.run_host_command` with a fake ctx (fake exec that records its keyword arguments, fake clock, spool and redactor, and a config whose one provider has `auth: FAKE_KEY` and that carries the other field `clutch/redact.py::secret_names` reads, `release.pypi_token`) and covers the prepend; it starts no process and reads no repo file.
- Two hot test files are fenced only because the prepend forces one existing `PATH` expectation in each; nothing else in them changes and no test is added to either:
  - `tests/integration/test_mergequeue.py`: in `test_host_check_environment_timeout_and_redaction`, the assertion `kw["env"]["PATH"] == ENV["PATH"]` becomes `kw["env"]["PATH"] == f"{Path(sys.executable).parent}{os.pathsep}{ENV['PATH']}"`, plus the `import os` and `import sys` it needs.
  - `tests/integration/test_stages.py`: in `test_verification_children_never_inherit_a_provider_key`, the substring `"PATH=/usr/bin:/bin"` checked in the spool of the fixture ticket's `env` Verification command becomes `f"PATH={Path(sys.executable).parent}{os.pathsep}/usr/bin:/bin"`, plus the `import os` and `import sys` it needs. Its `FAKE_KEY` and secret checks stay as they are.
- `docs/how-clutch-works.md`: in section 5.4, after the sentence that says all use one shared command runner, add one sentence: the runner puts the directory of the engine's own Python interpreter first on each command's `PATH`, so a check argv naming `clutch` runs the installed engine, not the worktree's code. No other part changes.

Scope out: the `integration`, `lint` and `format` checks; `clutch/covgate.py`; the `covmap` coverage_map argv; `clutch/providers.py::child_env`, which provider CLIs and git also use; the bug regression command's env in `clutch/stages.py::_gather_bug`; `cli-group-coverage`'s own rename of the verb to `coverage gate` (that ticket updates this argv again).

Simpler approaches rejected: a bare `clutch` with no `PATH` change fails on the play-button launch; `python -m clutch.covgate` adds a second front-end beside the CLI verb and still lets the branch's gate judge the branch; prepending in `child_env` would also change every provider CLI's and git's `PATH`.

## Scope fence
- config.yaml
- clutch/docs/host-contract.md
- tests/integration/test_host_contract.py
- clutch/stages.py
- tests/unit/test_stages_host_path.py
- tests/integration/test_mergequeue.py
- tests/integration/test_stages.py
- docs/how-clutch-works.md

## Acceptance criteria
1. The repo `config.yaml` `unit` argv is `[clutch, covgate, --, uv, run, python, -m, pytest]` followed by exactly the arguments that followed `pytest` at HEAD, not the old `uv, run, python, -m, clutch, covgate` prefix and not a changed tail; checked by `uv run python -c "import sys, yaml; u = next(c for c in yaml.safe_load(open('config.yaml'))['review']['mechanical'] if c['code'] == 'unit')['argv']; sys.exit(0 if u == ['clutch', 'covgate', '--', 'uv', 'run', 'python', '-m', 'pytest', 'tests/unit', '-p', 'clutch.testguard', '-p', 'clutch.testreport', '--clutch-results', '.clutch/results/unit.json', '--cov=clutch', '--cov-branch', '--cov-context=test', '--cov-report=json:coverage.json', '-n', 'auto'] else 1)"`.
2. The `argv:` line of the unit check in the `python-host` block of `clutch/docs/host-contract.md` has the same prefix; `test_python_host_setup_loads` fails if that doc block keeps `-m, clutch, covgate`; checked by `./dev.py test tests/integration/test_host_contract.py`.
3. The `-p clutch.testguard -p clutch.testreport`, `--clutch-results`, `--cov-context=test` and `--cov-report=json:` assertions in that test still pass unchanged; checked by `./dev.py test tests/integration/test_host_contract.py`.
4. `tests/unit/test_stages_host_path.py` runs `stages.run_host_command` with a ctx env of `{"PATH": "/usr/bin", "FAKE_KEY": "x"}` and a config naming `FAKE_KEY` as a provider auth, and asserts the recorded `PATH` is `str(Path(sys.executable).parent) + os.pathsep + "/usr/bin"`, not `/usr/bin` unchanged, and that `FAKE_KEY` is absent; with no `PATH` in the ctx env it asserts the recorded `PATH` is exactly `str(Path(sys.executable).parent)`, with no trailing separator; checked by `./dev.py test tests/unit/test_stages_host_path.py`.
5. The merge queue's host-check environment test and the Verification child-env test pass with only their `PATH` expectations changed to the prepended value, and the other host-command tests pass unchanged; checked by `./dev.py test tests/integration/test_mergequeue.py tests/integration/test_stages.py tests/integration/test_host_mechanical.py tests/integration/test_bug_gate.py tests/integration/test_fixture_host.py`.

## Verification
```
./dev.py test tests/integration/test_host_contract.py tests/unit/test_stages_host_path.py tests/integration/test_mergequeue.py tests/integration/test_stages.py tests/integration/test_host_mechanical.py tests/integration/test_bug_gate.py tests/integration/test_fixture_host.py
uv run python -c "import sys, yaml; u = next(c for c in yaml.safe_load(open('config.yaml'))['review']['mechanical'] if c['code'] == 'unit')['argv']; sys.exit(0 if u == ['clutch', 'covgate', '--', 'uv', 'run', 'python', '-m', 'pytest', 'tests/unit', '-p', 'clutch.testguard', '-p', 'clutch.testreport', '--clutch-results', '.clutch/results/unit.json', '--cov=clutch', '--cov-branch', '--cov-context=test', '--cov-report=json:coverage.json', '-n', 'auto'] else 1)"
```

## Definition of rejected
The unit argv still invokes `python -m clutch covgate` from the worktree; any later unit argument changes; `clutch/covgate.py` or another check is edited; the `PATH` prepend lives anywhere but `run_host_command` (for example in `child_env`); a test other than the two named `PATH` expectations is loosened; or a new test is added to `tests/integration/test_mergequeue.py` or `tests/integration/test_stages.py`.

## Time budget
- expected: 20m
- stuck: 40m
