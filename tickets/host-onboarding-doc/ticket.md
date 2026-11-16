---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- docs-truth-sweep

## Context
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- tests/integration/test_host_contract.py

## Goal / Why
`clutch/docs/host-contract.md` has an Install section and an Instance custody section, but no ordered path from a fresh host to its first merged ticket, and no single place that states the facts an operator needs while running (locks, state dir, upgrade, rollback). After this change the doc has an "Onboarding a host" section (a numbered checklist from install to first merge) and an "Operating facts" section (locks, state dir, upgrade, rollback). A new host owner can then follow one list, and the run facts are findable by name. This is roadmap row 27, a P8 gap.

## Scope in / Scope out
Scope in:
- Add `## Onboarding a host` to `clutch/docs/host-contract.md`. It is a numbered checklist of steps in order: install (link to the Install section, no restated commands), `clutch install` for the routed CLIs, `clutch init-config`, copy or edit `config.yaml` (link to Copyable configuration), `clutch doctor` and `clutch probe`, `clutch core` and commit the routed conduct files, author the first ticket with `clutch new` then `clutch lint` and `clutch review`, run it with `clutch drain` or `clutch serve`, and confirm it merged on main. Each step names a clutch verb, never a hand-built argv, and links to the owning section or to the host run guide for invocation detail.
- Add `## Operating facts` to the same file. It states in prose, from the code and the existing Instance custody text: the `<state_dir>/clutch.lock` flock and `<state_dir>/commit.lock`; what the state dir holds; upgrade and rollback by changing the dependency pin, running `uv sync` and restarting; and that a held lock means wait for or stop the holder and never delete the lockfile. It links to Instance custody instead of restating its text, and adds only facts that section lacks. Read `clutch/lockfile.py` and `clutch/config.py` before stating any fact not already in the doc.
- Place the two sections before `## Complete field inventory`. Leave the existing Install section, the yaml and toml blocks, and the install-name patterns (`uv add --dev clutchwork`, `clutchwork==<version>`, `Add dev dependencies` with `clutchwork`) byte-identical.
- Add a new test file `tests/integration/test_host_onboarding_doc.py`.

Scope out: any other section of `host-contract.md`, `host-running.md` (read only), code, and the existing `tests/integration/test_host_contract.py` (read only).

## Scope fence
- clutch/docs/host-contract.md
- tests/integration/test_host_onboarding_doc.py

## Acceptance criteria
1. `clutch/docs/host-contract.md` contains exactly one `## Onboarding a host` heading and exactly one `## Operating facts` heading, each before `## Complete field inventory`; checked by `./dev.py test tests/integration/test_host_onboarding_doc.py`, which fails if either heading is missing or duplicated.
2. The Onboarding section's numbered list has at least 8 items and its text names each of the verbs `clutch install`, `clutch init-config`, `clutch doctor`, `clutch probe`, `clutch core`, `clutch new`, `clutch lint`, and `clutch drain` or `clutch serve`, in that relative order; the test fails if a verb is absent or out of order.
3. The Operating facts section names `clutch.lock`, `commit.lock`, `state_dir`, `uv sync`, upgrade and rollback; the test fails when any of those terms is absent from that section.
4. Neither new section contains `shell=True`, `./dev.py`, or a fenced code block; the test fails if one appears, so no hand-built argv is copied.
5. Existing doc pins still hold: `./dev.py test tests/integration/test_host_contract.py tests/unit/test_help.py tests/integration/test_help.py` exits 0, and `python tests/regress_install_docs_name.py` prints `{"regression_result": "pass"}`.

## Verification
```
./dev.py test tests/integration/test_host_onboarding_doc.py tests/integration/test_host_contract.py tests/unit/test_help.py tests/integration/test_help.py
python tests/regress_install_docs_name.py
```

## Definition of rejected
The branch edits any file outside the fence, restates Install or Instance custody text instead of linking it, changes the install-name patterns, names a verb that does not exist, or states a lock or state-dir fact that contradicts `clutch/lockfile.py` or `clutch/config.py`.

## Time budget
- expected: 30m
- stuck: 60m
