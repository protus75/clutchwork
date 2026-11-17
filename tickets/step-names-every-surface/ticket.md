---
state: confirmed
source: box:roadmap_row
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/observe.py::STEP_NAMES
- clutch/specs/__init__.py::ENGINE_LLM_SURFACES
- tests/integration/test_step_icons.py

## On-demand
- clutch/help.py
- vscode-clutchwork/extension.js

## Goal / Why
`roadmap-accept` (`038fec29`) added `acceptance` to `clutch/specs/__init__.py::ENGINE_LLM_SURFACES` but not to `clutch/observe.py::STEP_NAMES`. The first acceptance run (engine log 2026-11-17T12:47:10, stem `acceptance`) therefore shows in the extension's step list as `acceptance start` with the fallback `stage` icon.

After this ticket, `acceptance` has a step name, step kinds `acceptance_start`, `acceptance_ok` and `acceptance_failed`, a help entry and its own icon. A new test fails whenever a member of `ENGINE_LLM_SURFACES` has no `STEP_NAMES` key, so the next surface cannot drift the same way.

This is the only set of section 2.2 with a recorded incident. The other sets stay with `release-audit-040`.

## Scope in / Scope out
Scope in:
- `clutch/observe.py`: add `"acceptance": "Acceptance"` to `STEP_NAMES`. `STEP_KINDS` is derived from it, so nothing else changes there.
- `clutch/help.py`: add `"acceptance"` to the name tuple of the `step` topic. `tests/unit/test_help.py` requires the topic's keys to equal `set(STEP_KINDS.values())`, so this edit is forced.
- `vscode-clutchwork/extension.js`: add `acceptance_start`, `acceptance_ok` and `acceptance_failed` to the `icons` table in `getTreeItem`. Use the `verified` ThemeIcon, which no other step uses, with `testing.iconPassed` and `testing.iconFailed` on ok and failed as for the other steps.
- New `tests/unit/test_step_names_cover_surfaces.py` asserting `ENGINE_LLM_SURFACES <= STEP_NAMES.keys()`.

Scope out:
- No other surface set changes.
- No file on the engine-plane safety inventory is edited.
- `tests/integration/test_step_icons.py` is not edited. It iterates `STEP_KINDS` and checks the icons are distinct, so it covers the new entries as is.

## Scope fence
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/extension.js
- tests/unit/test_step_names_cover_surfaces.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_step_names_cover_surfaces.py` passes. It asserts that every member of `ENGINE_LLM_SURFACES` is a key of `STEP_NAMES`. It fails on base, where `acceptance` is missing, and does not pass by checking only that the sets are non-empty.
2. `STEP_NAMES["acceptance"] == "Acceptance"` and `{"acceptance_start", "acceptance_ok", "acceptance_failed"} <= STEP_KINDS.keys()`, checked in the same new test with `./dev.py test tests/unit/test_step_names_cover_surfaces.py`. The checks must not pass if the event maps to the `stage` fallback.
3. `./dev.py test tests/integration/test_step_icons.py` passes. All three `acceptance_*` kinds get an icon, and the icon is distinct from every other step's icon. It does not map to `question`, the `stage` fallback.
4. `./dev.py test tests/unit/test_help.py` passes. The `step` topic has an `acceptance` entry, and the test does not report a missing entry for it.

## Verification
```
./dev.py test tests/unit/test_step_names_cover_surfaces.py tests/integration/test_step_icons.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_watch.py
```

## Definition of rejected
The branch is rejected if it changes any surface set other than `STEP_NAMES`, edits a file on the engine-plane safety inventory, or adds a test that passes while `acceptance` is missing from `STEP_NAMES`.

## Time budget
- expected: 10m
- stuck: 20m
