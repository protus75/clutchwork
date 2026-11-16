---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- pyproject.toml
- README.md#Install
- clutch/docs/host-contract.md#Install
- clutch/docs/host-contract.md#Python host test setup
- tests/regress_engine_text_verbs.py
- tests/unit/test_readme.py
- tickets/install-docs-name-clutchwork/evidence/evidence.txt

## Goal / Why
The PyPI distribution is `clutchwork` (`pyproject.toml` `[project] name = "clutchwork"`); the import package and the console script are `clutch`. The host install docs name the wrong distribution in four places:

- `README.md` `## Install`, the code block line `uv add --dev clutch`;
- `clutch/docs/host-contract.md` `## Install`, `` `uv add --dev clutch` `` and the pin `` `clutch==<version>` ``;
- `clutch/docs/host-contract.md` `## Python host test setup`, ``Add dev dependencies `clutch`, `pytest`, ...``.

On PyPI, `clutch` is an unrelated project ("A Python Web Framework for GAE", version 0.1a2). The evidence file shows `uv pip compile` of a requirements file holding `clutch` resolving `clutch==0.1a2` with `mako` and `routes`, while `clutchwork` resolves `clutchwork==0.2.4` with `pydantic` and `pyyaml`. A host that follows the install docs installs a GAE web framework and never gets clutch; `uv run clutch` then fails or runs the wrong thing.

When this ticket is done, every one of those four install sites names `clutchwork`, the commands that run the console script (`uv run clutch <verb>`, `.venv/bin/clutch`) still name `clutch`, and a carried reproducer proves the docs at the base commit named the wrong distribution.

## Scope in / Scope out
Scope in:
- `README.md` `## Install`: the code block line `uv add --dev clutch` becomes `uv add --dev clutchwork`. Nothing else in the README changes.
- `clutch/docs/host-contract.md` `## Install`: `` `uv add --dev clutch` `` becomes `` `uv add --dev clutchwork` `` and `` `clutch==<version>` `` becomes `` `clutchwork==<version>` ``. The executable (`.venv/bin/clutch`), `uv run clutch <verb>`, and the Windows sentence stay as they are; line wrapping may shift.
- `clutch/docs/host-contract.md` `## Python host test setup`: ``Add dev dependencies `clutch`, `pytest`, `pytest-cov`, `pytest-xdist`, and `ruff`.`` becomes ``Add dev dependencies `clutchwork`, `pytest`, `pytest-cov`, `pytest-xdist`, and `ruff`.`` Nothing else in that section changes.
- New carried reproducer `tests/regress_install_docs_name.py`, stdlib only (`json`, `re`, `sys`, `tomllib`, `pathlib`), with the repo root taken as `Path(__file__).resolve().parents[1]`. It reads the distribution name from `pyproject.toml` `[project] name` with `tomllib`, collapses every whitespace run in each doc to one space, then collects the package name at every install site:
  - in `README.md`, each match of `uv add --dev ([A-Za-z0-9._-]+)`;
  - in `clutch/docs/host-contract.md`, each match of `uv add --dev ([A-Za-z0-9._-]+)`, each match of `` `([A-Za-z0-9._-]+)==<version>` ``, and each match of ``Add dev dependencies `([A-Za-z0-9._-]+)` `` (the first listed name).

  When `pyproject.toml` or either doc cannot be read, `[project] name` is absent, or any of those four patterns has no match in its file, it writes the reason to stderr, prints `{"regression_result": "error"}` and exits 2. When any collected name differs from the distribution name, it writes each offending `file: name` to stderr, prints `{"regression_result": "defect"}` and exits 1. Otherwise it prints `{"regression_result": "pass"}` and exits 0. It prints nothing else to stdout. Follow the shape of `tests/regress_engine_text_verbs.py`.

Scope out:
- A pytest test in the suite that ties install commands in docs to the distribution name; that is the cause fix, filed as Suggestion Box `box-000505-6d6378a2`. The reproducer above is run only by Check's regression step and by `## Verification`; it is not named `test_*.py` and pytest does not collect it.
- Prose that names the tool "clutch" (for example "Add clutch to your host project"), the `clutch` console script, `uv run clutch <verb>`, `.venv/bin/clutch`, and `python -m clutch`: all correctly name the script or package, not the distribution.
- `vscode-clutchwork/README.md` (it links to `## Install` and its PyPI links already name `clutchwork`), `docs/how-clutch-works.md`, `clutch/docs/host-running.md`, `clutch/docs/host-authoring.md`, `clutch/hostfiles.py`, `clutch/help.py`, `clutch/__main__.py`, and `clutch/specs/`: a grep at HEAD e66ee0be finds no install command naming the distribution in any of them.
- `docs/gemini-graphics-refactor-plan.md` and `docs/roadmap.md`, which name the not-yet-built extras `clutch[images]` and `clutch[images-embed]`: they are design records for the graphics row, whose author corrects them (`.claude/roadmap-docs-digest.json` already records the stale name). `CLUTCH_PLAN.md` is frozen. Ticket files under `tickets/` keep their historical text.
- `pyproject.toml` and the distribution, package, or script names: nothing is renamed.

## Scope fence
- README.md
- clutch/docs/host-contract.md
- tests/regress_install_docs_name.py

## Acceptance criteria
1. `uv run python tests/regress_install_docs_name.py` prints exactly `{"regression_result": "pass"}` and exits 0 on the branch. Ruled out: any of the four install sites still naming `clutch`, and an edit that deletes a site instead of fixing it (the reproducer reports `error` when a pattern has no match).
2. Check's regression run of the same command against the merge base, with `tests/regress_install_docs_name.py` carried over it, prints `{"regression_result": "defect"}` and exits 1, because the base `README.md` holds `uv add --dev clutch`. Ruled out: a reproducer that passes or reports `error` on the defective docs.
3. The `uv run python -c` command in `## Verification` exits 0: `README.md` and `clutch/docs/host-contract.md` each still contain `uv run clutch <verb>`, `clutch/docs/host-contract.md` still contains `.venv/bin/clutch`, and neither file contains `uv run clutchwork`, `clutchwork <verb>`, or `bin/clutchwork`. Ruled out: an over-eager rename that points hosts at a `clutchwork` command that does not exist (the console script is `clutch`, `pyproject.toml` `[project.scripts]`).
4. `./dev.py test tests/unit/test_readme.py tests/integration/test_host_contract.py` exits 0 with neither file edited: the README's links stay absolute, its `uv run clutch` verbs still exist, and the host contract's executable examples still hold.
5. `./dev.py test` exits 0.

## Verification
```
uv run python tests/regress_install_docs_name.py
uv run python -c "import pathlib; r, h = (' '.join(pathlib.Path(p).read_text().split()) for p in ('README.md', 'clutch/docs/host-contract.md')); assert 'uv run clutch <verb>' in r and 'uv run clutch <verb>' in h and '.venv/bin/clutch' in h; bad = [s for s in ('uv run clutchwork', 'clutchwork <verb>', 'bin/clutchwork') if s in r + h]; assert not bad, bad"
./dev.py test tests/unit/test_readme.py tests/integration/test_host_contract.py
./dev.py test
```

## Definition of rejected
The branch is rejected if any of the four install sites still names `clutch`; if a `uv run clutch`, `.venv/bin/clutch`, `python -m clutch`, or prose mention of the tool is renamed to `clutchwork`; if `pyproject.toml`, the package, or the console script is renamed; if it adds a pytest test (a `test_*.py` file or a test in an existing one), which is the separately filed cause fix; if it edits `docs/`, `CLUTCH_PLAN.md`, or any file outside `## Scope fence`; or if the reproducer reads anything but `pyproject.toml`, `README.md`, and `clutch/docs/host-contract.md`, or prints more than the one JSON object to stdout.

## Time budget
- expected: 15m
- stuck: 45m

## Regression
```
uv run python tests/regress_install_docs_name.py
```
- carries: tests/regress_install_docs_name.py
