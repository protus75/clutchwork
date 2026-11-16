---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
- install-docs-name-clutchwork

## Context
- pyproject.toml
- README.md#Install
- tests/unit/test_readme.py

## Goal / Why
The PyPI distribution is `clutchwork` (`pyproject.toml` `[project] name`); `clutch` on PyPI is an unrelated GAE web framework. Install docs have named the wrong distribution repeatedly (`pypi-package`, `pypi-readme-user-guide`, `vscode-venv-default`), and `docs/gemini-graphics-refactor-plan.md` line 226 still prescribes `uv add --dev "clutch[images]"`. A host that follows such a command installs a foreign package. Nothing in the suite checks the distribution name: `tests/unit/test_readme.py` checks links, dev.py placement and verb names only. After this change a test fails when any install command in the docs names `clutch` or `clutchwork` with a name other than the `pyproject.toml` `[project] name`, so a typo or a rename cannot ship.

## Scope in / Scope out
Scope in:
- New `tests/integration/test_install_docs_name.py` (it reads repo files). It reads the distribution name with `tomllib` from `pyproject.toml`. It scans `README.md`, `clutch/docs/*.md` and `docs/*.md`, with whitespace runs collapsed to one space. It collects the package name from each install command and each pin: `uv add`, `uv pip install`, `pip install` and `uv tool install`, each optionally followed by flags and an optional opening quote, and every `<name>==<version>` pin. A trailing extras suffix such as `[images]` is dropped. Only names that equal `clutch` or `clutchwork` count as naming this project; other packages (`pytest`, `ruff`) are ignored. Every collected project name must equal the `pyproject.toml` name.
- The test also asserts that the scan finds at least one install command in `README.md` and at least one in `clutch/docs/host-contract.md`, so it cannot pass with no sites found. It also checks the collector against a hand-built string: `uv add --dev clutch` yields `clutch`, and `uv add --dev "clutchwork[images]"` yields `clutchwork`.
- `docs/gemini-graphics-refactor-plan.md` line 226: `uv add --dev "clutch[images]"` becomes `uv add --dev "clutchwork[images]"`. Nothing else in that file changes; the extras name `clutch[images]` in prose stays as written.

Scope out:
- The `README.md` and `clutch/docs/host-contract.md` fixes: ticket `install-docs-name-clutchwork` owns them, and this ticket depends on it because the test is red until they merge.
- `CLUTCH_PLAN.md` (frozen) and `tickets/` text, which are not scanned.
- Prose that names the tool or console script (`uv run clutch <verb>`, `.venv/bin/clutch`); the collector matches only install commands and `==` pins.
- Edits to `tests/unit/test_readme.py` or any other existing test.

## Scope fence
- tests/integration/test_install_docs_name.py
- docs/gemini-graphics-refactor-plan.md

## Acceptance criteria
1. `./dev.py test tests/integration/test_install_docs_name.py` exits 0 on the branch. The scan of the real docs reports every collected project name equal to the `pyproject.toml` name. Ruled out: a test that passes while `docs/gemini-graphics-refactor-plan.md` still contains `uv add --dev "clutch[images]"`.
2. A test in that file feeds the collector the hand-built string `uv add --dev clutch` and asserts the result is `["clutch"]`, and `uv add --dev "clutchwork[images]"` yields `["clutchwork"]`, not `["clutchwork[images]"]`. Ruled out: a collector that returns an empty list for either string.
3. A test in that file asserts that the collected names for `README.md` and for `clutch/docs/host-contract.md` are each non-empty. Ruled out: a scan that finds no sites and passes vacuously.
4. A test in that file feeds a hand-built doc text containing `uv add --dev clutch` to the checking function with distribution name `clutchwork` and asserts it reports that name as a mismatch. Ruled out: a checker that returns no mismatch for a wrong name.
5. `git grep -n 'uv add --dev "clutch\[' -- docs README.md clutch/docs` prints nothing.
6. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_install_docs_name.py tests/unit/test_readme.py
./dev.py test
```

## Definition of rejected
The branch is rejected if the test hardcodes the string `clutchwork` instead of reading `pyproject.toml`; if it adds checks to an existing test file; if it edits `README.md`, `clutch/docs/`, `CLUTCH_PLAN.md` or any file outside `## Scope fence`; or if it renames `clutch[images]` in prose beyond the line 226 command.

## Time budget
- expected: 20m
- stuck: 60m
