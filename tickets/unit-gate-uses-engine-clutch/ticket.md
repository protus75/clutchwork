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

## On-demand
- clutch/docs/host-contract.md

## Goal / Why
The `unit` mechanical check in `config.yaml` runs the gate through the ticket worktree's own source (`uv run python -m clutch covgate -- ...`). Check reads that argv from main's config, so a branch that renames or removes the `covgate` verb (cli-group-coverage) fails its own Check with argparse exit 2 on every attempt. Any ticket that edits `clutch/covgate.py` also weakens the gate that judges it. After this ticket the unit argv starts with the installed engine's `clutch covgate --` and runs pytest through `uv run python -m pytest` inside it, so main's gate code judges the branch's tests. This is an orchestration cause: it keeps breaking runs while it sits, so it is P0 and runs before cli-group-coverage.

## Scope in / Scope out
Scope in:
- `config.yaml`: change the `unit` argv prefix from `[uv, run, python, -m, clutch, covgate, --, python, -m, pytest, ...]` to `[clutch, covgate, --, uv, run, python, -m, pytest, ...]`. Every later argument stays byte-identical.
- `clutch/docs/host-contract.md`: change only the example `unit` argv line (the `argv: [uv, run, python, -m, clutch, covgate, --, ...]` line) to the same new prefix.
- `tests/integration/test_host_contract.py`: change the pinned prefix assertion in `test_python_host_setup_loads` (the `unit.argv[:7] == [...]` line) to the new prefix, so the slice becomes `[:8]`. Also add one assertion in that file that loads `ROOT / "config.yaml"` with `yaml.safe_load` and checks its `unit` entry has `argv[:8] == [clutch, covgate, --, uv, run, python, -m, pytest]`, plus any import that assertion needs. Nothing else in the file changes.

Scope out: the `integration`, `lint` and `format` checks; `clutch/covgate.py`; the `covmap` coverage_map argv; `cli-group-coverage`'s own rename of the verb to `coverage gate` (that ticket updates this argv again).

## Scope fence
- config.yaml
- clutch/docs/host-contract.md
- tests/integration/test_host_contract.py

## Acceptance criteria
1. The repo `config.yaml` `unit` entry has `argv[:8] == [clutch, covgate, --, uv, run, python, -m, pytest]`, not the old `uv run python -m clutch covgate` prefix; the new config.yaml assertion in `./dev.py test tests/integration/test_host_contract.py` fails if the old prefix remains.
2. The `argv:` line of the unit check in the `host-example`/`python-host` block of `clutch/docs/host-contract.md` has the same prefix; `test_python_host_setup_loads` fails if that doc block keeps `-m, clutch, covgate`; checked by `./dev.py test tests/integration/test_host_contract.py`.
3. The `-p clutch.testguard -p clutch.testreport`, `--clutch-results`, `--cov-context=test` and `--cov-report=json:` assertions in that test still pass unchanged; checked by `./dev.py test tests/integration/test_host_contract.py`.
4. `config.yaml` contains `[clutch, covgate, --` and does not contain `python, -m, clutch, covgate`; checked by `uv run python -c "import sys; t=open('config.yaml').read(); sys.exit(0 if 'python, -m, clutch, covgate' not in t and '[clutch, covgate, --' in t else 1)"`.

## Verification
```
./dev.py test tests/integration/test_host_contract.py
uv run python -c "import sys; t=open('config.yaml').read(); sys.exit(0 if 'python, -m, clutch, covgate' not in t and '[clutch, covgate, --' in t else 1)"
```

## Definition of rejected
The unit argv still invokes `python -m clutch covgate` from the worktree, any later unit argument changes, or `clutch/covgate.py` or another check is edited.

## Time budget
- expected: 10m
- stuck: 20m
