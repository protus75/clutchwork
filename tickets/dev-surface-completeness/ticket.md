---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- dev.py
- clutch/testguard.py::pytest_configure
- config.yaml
- tests/integration/test_dev.py::test_test_passes_leading_options_to_pytest
- tests/regress_dev_test_args.py
- docs/how-clutch-works.md#2.2

## Goal / Why
Check's `unit` gate runs `tests/unit` with `-p clutch.testguard` (`config.yaml`, `review.mechanical` code `unit`). That plugin blocks process and network IO in every test phase and, in `clutch/testguard.py::pytest_configure`, reads the unit time budget from `test-gate.toml` (`[unit] budget_seconds = 60`). `./dev.py test` never loads it: `dev.py::main` runs `uv run pytest -q [args]`, and nothing else loads the plugin, because `pyproject.toml` `addopts` is only `-n auto` and the repo has no `conftest.py`. Every ticket's `## Verification`, and every Implement run, checks its work with `./dev.py test tests/unit/...`. So a unit test that spawns a process or opens a socket, or a unit suite over budget, passes there and fails only later, at Check. `docs/how-clutch-works.md` section 2.2 already says unit tests "run under `clutch.testguard`" and that `./dev.py test tests/unit` runs that suite, but the code does not do this (roadmap section 3.5 and the section 4.1 row for line 79).

The roadmap row's other half, removing the `dev.py` launcher twins of engine verbs, is already done. `dev-py-dev-tasks-only` merged it in `7296a7f0`, so `dev.py` keeps only `test`, `publish`, `vscode` and `vscode-package`, as `CLAUDE.md` section B requires.

After this change, `./dev.py test` loads `clutch.testguard`, and with it `test-gate.toml`'s budget, for every run that targets `tests/unit`, and for no run that includes integration tests. Integration tests spawn processes, so the guard would fail them.

## Scope in / Scope out
- In: `dev.py::main`, the full-suite run. `./dev.py` with no arguments, and `./dev.py test` with no arguments, each make exactly two `run` calls, in this order:
  1. `["uv", "run", "pytest", "-q", "-p", "clutch.testguard", "tests/unit"]`
  2. `["uv", "run", "pytest", "-q", "tests/integration"]`

  `run` already exits on a non-zero return code, so a unit failure exits non-zero before the integration run starts. The integration run never loads `clutch.testguard`, because its tests spawn processes. This mirrors Check, which gates the two suites as separate sessions, `-p clutch.testguard` only on `unit`. `tests/unit` and `tests/integration` are the only directories under `tests/` that hold `test_*.py` files, so the two runs cover what `uv run pytest -q` collects today.
- In: `dev.py::main`, `./dev.py test <args>` with at least one argument. A "test path argument" is an argument equal to `tests` or starting with `tests/`.
  - At least one test path argument, and every one of them equal to `tests/unit` or starting with `tests/unit/`: one `run` call, `["uv", "run", "pytest", "-q", "-p", "clutch.testguard", *args]`, with the arguments unchanged and in order. This covers node IDs such as `tests/unit/test_graph.py::test_x` too.
  - Anything else: no test path argument (`-k foo`, `--durations=25`), a path outside `tests/unit` (`tests/integration`, `tests`), or a mix of unit and other paths. It runs `["uv", "run", "pytest", "-q", *args]`, exactly as today.
  - The decision is made only on the argument text. It does not read the filesystem and does not parse pytest options.
- In: `dev.py`, the module docstring's `./dev.py` and `./dev.py test [args]` lines say that the unit suite runs under `clutch.testguard`. No other docstring line, subcommand, `help=` string or import changes, beyond what the two branches above need.
- In: new `tests/unit/test_dev_testguard.py`, which imports `dev` and monkeypatches `dev.subprocess.run` with a recorder, as `tests/integration/test_dev.py` does. It spawns nothing. The tests are listed in `## Acceptance criteria`.
- In: `docs/how-clutch-works.md` section 2.2, only its subcommand table.
  - The `(none)` row names the two runs, `uv run pytest -q -p clutch.testguard tests/unit` and then `uv run pytest -q tests/integration`, and says a unit failure stops before the integration run.
  - The `test [args]` row says that with no args it does the same as `(none)`. With args, it runs pytest with those args, adding `-p clutch.testguard` when every test path they name is under `tests/unit`.
  - The prose above the table (unit tests "run under `clutch.testguard`"; "Run one suite with `./dev.py test tests/unit` or `./dev.py test tests/integration`") becomes true and stays as written. Section 12's `clutch.testguard` bullet and the rest of the file do not change.
- Out: `tests/integration/test_dev.py` and `tests/regress_dev_test_args.py`. They pin the unguarded argv for arguments that name no test path (`--durations=25 -k foo`, `-k foo`), and this change keeps that argv, so both pass unedited.
- Out: `clutch/testguard.py`, `test-gate.toml`, `pyproject.toml` (including `addopts`), `config.yaml`, and any `conftest.py`. The plugin and its budget are already correct; only the launcher fails to load them.
- Out: the `uv run pytest` form itself. Switching it to `uv run python -m pytest` is not this ticket's change.
- Out: `README.md`. Its `./dev.py test [args]  # run the test suite` row stays true.
- Out: `CLAUDE.md`, `AGENTS.md`, and `docs/roadmap.md`. A person updates the roadmap rows per its section 9.

## Scope fence
- dev.py
- tests/unit/test_dev_testguard.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/unit/test_dev_testguard.py::test_suite_runs_unit_guarded_then_integration` is parametrized over argv `["dev.py"]` and `["dev.py", "test"]`. With every faked call returning code 0, it asserts that the recorded calls are exactly two, `(["uv", "run", "pytest", "-q", "-p", "clutch.testguard", "tests/unit"], cwd=dev.ROOT, check=False)` then `(["uv", "run", "pytest", "-q", "tests/integration"], cwd=dev.ROOT, check=False)`. It rules out three wrong results: the single unguarded `["uv", "run", "pytest", "-q"]` call made today; one guarded run over the whole `tests` tree, which would fail every integration test that spawns a process; and an integration run that also loads `clutch.testguard`.
2. `tests/unit/test_dev_testguard.py::test_unit_failure_stops_before_integration`. With argv `["dev.py", "test"]` and the first faked call returning code 1, `dev.main()` raises `SystemExit` with a non-`None`, non-zero code, and exactly one call is recorded: the guarded `tests/unit` run. It rules out exit 0 after a unit failure, and an integration run that still starts after one.
3. `tests/unit/test_dev_testguard.py::test_unit_paths_load_testguard` is parametrized over these argument lists: `["tests/unit"]`, `["tests/unit/test_graph.py::test_x", "-k", "foo"]`, and `["-k", "foo", "tests/unit/test_a.py", "tests/unit/test_b.py"]`. For each, `["dev.py", "test", *args]` makes exactly one call, `["uv", "run", "pytest", "-q", "-p", "clutch.testguard", *args]`. It rules out today's argv without `-p clutch.testguard`, the arguments being dropped or reordered, and a node ID or a leading option defeating the guard.
4. `tests/unit/test_dev_testguard.py::test_other_paths_run_unguarded` is parametrized over these argument lists: `["tests/integration"]`, `["tests"]`, `["tests/unit/test_a.py", "tests/integration/test_b.py"]`, `["-k", "foo"]`, and `["--durations=25"]`. For each, `["dev.py", "test", *args]` makes exactly one call, `["uv", "run", "pytest", "-q", *args]`. It rules out `clutch.testguard` loaded for a run that collects integration tests, and any change to the argv for arguments that name no test path.
5. `./dev.py test tests/integration/test_dev.py` exits 0, and `uv run python tests/regress_dev_test_args.py` prints `{"regression_result": "pass"}`. Both are unedited, so leading options still reach pytest unchanged and the surviving subcommands still reject unknown options.
6. The `docs/how-clutch-works.md` check in `## Verification` exits 0. In section 2.2, the table row starting `| (none) |` contains `clutch.testguard tests/unit` and `tests/integration`, and the row for `test [args]` contains `clutch.testguard`. It rules out the old `uv run pytest -q` row left in place, and a section that names the guard only in prose.
7. `./dev.py test` exits 0, so the whole unit suite passes under `clutch.testguard` within `test-gate.toml`'s budget, and the integration suite passes unguarded.

## Verification
```
./dev.py test tests/unit/test_dev_testguard.py
./dev.py test tests/integration/test_dev.py
uv run python tests/regress_dev_test_args.py
uv run python -c "import pathlib; s = pathlib.Path('docs/how-clutch-works.md').read_text().split('### 2.2 ')[1].split('\n### ')[0]; rows = s.splitlines(); none = [r for r in rows if r.startswith('| (none) |')]; test = [r for r in rows if r.startswith('| ') and 'test [args]' in r]; assert len(none) == 1 and 'clutch.testguard tests/unit' in none[0] and 'tests/integration' in none[0]; assert len(test) == 1 and 'clutch.testguard' in test[0]"
./dev.py test
```

## Definition of rejected
- Any pytest session that collects `tests/integration` loads `clutch.testguard`.
- The argv for `./dev.py test` with arguments that name no test path differs from `["uv", "run", "pytest", "-q", *args]`.
- `tests/integration/test_dev.py` or `tests/regress_dev_test_args.py` is edited.
- `clutch/testguard.py`, `test-gate.toml`, `pyproject.toml` or `config.yaml` is edited, or a `conftest.py` is added.
- A `dev.py` subcommand, flag, environment variable or config knob is added, for example to turn the guard on or off.

## Time budget
- expected: 25m
- stuck: 60m
