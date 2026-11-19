---
state: confirmed
source: box:suggestion
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/docs/host-contract.md
- clutch/docs/host-running.md

## On-demand
- clutch/__main__.py
- tests/unit/test_main_provider_group.py

## Goal / Why
`clutch provider install` runs `pnpm add -D --allow-build=<package>`, and pnpm records that approval in `pnpm-workspace.yaml` (`allowBuilds`). The host contract and the command help tell hosts to commit only `package.json` and `pnpm-lock.yaml`. A host that follows them drops the build approval, and the next clean `pnpm install` skips claude-code's postinstall and leaves a provider CLI that cannot start (the 2026-11-18 incident). After this ticket the host contract and the `provider install` help name `pnpm-workspace.yaml` as written by the verb and committed with `package.json` and `pnpm-lock.yaml`.

## Boundary contract
### Provider install documentation
- disposition: extend
- owner: clutch/docs/host-contract.md
- consumers: host operators reading the contract, the run guide and `clutch provider install --help`
- observable change: the list of files the verb writes and the files a host commits includes `pnpm-workspace.yaml`
- compatibility: no behavior change; the verb's argv and writes are unchanged
- acceptance: the contract and the help text name `pnpm-workspace.yaml` beside `pnpm-lock.yaml`
- tests: a unit assertion on the `provider install` help text, plus existing help and host-contract tests
- post-merge source of truth: clutch/docs/host-contract.md and the `provider install` parser entry in clutch/__main__.py

## Scope in / Scope out
Scope in: in `clutch/docs/host-contract.md` (the provider install paragraph), say the verb also writes `pnpm-workspace.yaml` and that it is committed with `package.json` and `pnpm-lock.yaml`, with `node_modules/` still gitignored. In `clutch/__main__.py`, change only the `writes=` string of the `provider install` `_command` to list `pnpm-workspace.yaml`. In `tests/unit/test_main_provider_group.py`, add one test that renders the `provider install` help and asserts it contains `pnpm-workspace.yaml`; no other edit there. In `clutch/docs/host-running.md`, change only the `provider install` verb table row if it lists written files, otherwise leave it unchanged.
Scope out: preflight checking for the file (declined in box-000755), any change to the install argv, and other docs.

## Scope fence
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- clutch/__main__.py
- tests/unit/test_main_provider_group.py

## Acceptance criteria
1. `grep -n pnpm-workspace.yaml clutch/docs/host-contract.md` prints the provider install paragraph, which also names `pnpm-lock.yaml` and `package.json` as committed; it is not empty.
2. `uv run clutch provider install --help` output contains `pnpm-workspace.yaml` in its writes description, not only `pnpm-lock.yaml`.
3. The new test in `tests/unit/test_main_provider_group.py` fails if the help text lacks `pnpm-workspace.yaml`, and `./dev.py test tests/unit/test_main_help.py tests/unit/test_main_provider_group.py tests/unit/test_host_running.py tests/integration/test_host_contract.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_main_help.py tests/unit/test_main_provider_group.py tests/unit/test_host_running.py tests/integration/test_host_contract.py
```

## Definition of rejected
The branch changes the install argv or other behavior, adds a standing test pinning document text, or leaves `pnpm-workspace.yaml` out of either the contract or the help.

## Time budget
- expected: 10m
- stuck: 20m
