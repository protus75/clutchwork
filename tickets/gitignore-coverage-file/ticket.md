---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- .gitignore
- pyproject.toml

## Goal / Why
`.gitignore` ignores coverage.py's JSON report (`coverage.json`) but not its data file. `pyproject.toml` sets `[tool.coverage.run] core = "ctrace"` and no `data_file`, so coverage.py writes its default `.coverage` into the repo root, and the `--cov` run in the unit check leaves it there. A 4 MB `.coverage` has been sitting untracked in this checkout since 2026-11-13, so `git status` and the VS Code SCM view report a dirty tree for a build artifact on every read. After this change `git check-ignore .coverage` succeeds and `git status --porcelain` is empty on a checkout whose only extra file is `.coverage`.

## Scope in / Scope out
Scope in: add one line, `.coverage`, to `.gitignore`, next to the existing `coverage.json` line. Nothing else changes in that file: no existing pattern is removed, reordered, or rewritten.

Scope out: `pyproject.toml` (do not add a `[tool.coverage.run] data_file` setting to move or rename the file), the `covgate`/`covmap` verbs and the `coverage.json` they read, `test-gate.toml`, and the untracked `.coverage` file in the owner's checkout (ignoring it is the fix; deleting it is not part of this ticket).

## Scope fence
- .gitignore

## Acceptance criteria
1. The first `## Verification` command exits 0: `.gitignore` has `.coverage` as its own whitespace-delimited entry (`".coverage" in Path(".gitignore").read_text().split()`), and still carries all six entries it has on main -- `.venv/`, `__pycache__/`, `.clutch/`, `dist/`, `coverage.json`, `node_modules/`. Ruled out: a `.coverage` pattern added by dropping or rewriting an existing entry, and a `.coverage*` glob or a `**/.coverage` path form, neither of which is the literal entry asserted.
2. The second `## Verification` command exits 0: `git check-ignore -q .coverage` in the worktree root reports the path as ignored. This rules out a pattern that is present in the file but does not match the repo-root path, which criterion 1's text assertion alone cannot catch.
3. `git diff --stat` for the branch against its merge base names `.gitignore` as the only changed file, with 1 insertion and 0 deletions. Ruled out: a second file edited "while in here", and a rewrite of `.gitignore` that lands as an insertion plus a deletion.

## Verification
```
uv run python -c "import pathlib; e = pathlib.Path('.gitignore').read_text().split(); assert '.coverage' in e, e; assert set(e) >= {'.venv/', '__pycache__/', '.clutch/', 'dist/', 'coverage.json', 'node_modules/'}, e"
git check-ignore -q .coverage
```

## Definition of rejected
The branch is rejected if it deletes the `.coverage` file instead of ignoring it, moves or renames the data file through a `[tool.coverage.run] data_file` setting, changes any `.gitignore` entry other than adding `.coverage`, or edits any file outside `## Scope fence`.

## Time budget
- expected: 5m
- stuck: 15m
