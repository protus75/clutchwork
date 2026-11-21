---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Runs before
- extension-copy-merged-stem

## Context
- clutch/observe.py::extension_fields
- clutch/providers.py::ADAPTERS
- clutch/help.py
- vscode-clutchwork/extension.js
- tests/unit/test_observe_extension_fields.py
- tests/integration/test_help.py

## On-demand
- vscode-clutchwork/package.json

## Goal / Why
Updating a provider CLI today means typing `clutch provider install <name>` in a terminal (the drain's preflight prints that notice when claude or codex is behind). After this ticket the Tickets view's More Actions (`...`) menu has an "Update Provider CLI..." item that opens a quick pick with one entry per installable provider and one entry for all of them, and runs the matching `clutch provider install` command.

## Boundary contract
### Extension snapshot provider installs
- disposition: extend
- owner: clutch/observe.py::extension_fields
- consumers: vscode-clutchwork/extension.js (new `clutch.updateProvider` command)
- observable change: `extension_fields(root)` gains `providerInstalls`, a list of `{"label", "detail", "argv"}`: one entry per name in `sorted(ADAPTERS)` with `argv == ["provider", "install", name]`, label `Update <name>` and detail `installs <ADAPTERS[name].PACKAGE>@latest`, followed by one entry labeled `Update all providers` whose argv is `["provider", "install", *sorted(ADAPTERS)]`
- compatibility: every existing `extension_fields` key is unchanged; the extension draws the list and runs the chosen argv, it never builds argv or filters the list
- acceptance: criteria 1 and 2
- tests: tests/unit/test_observe_provider_installs.py and tests/unit/test_observe_extension_fields.py
- post-merge source of truth: clutch/observe.py

### Extension command and help
- disposition: extend
- owner: vscode-clutchwork/package.json and clutch/help.py
- consumers: VS Code users of the Tickets view
- observable change: command `clutch.updateProvider` titled `Update Provider CLI...` appears in the Tickets view title overflow menu (group `clutch@8`), is hidden from the command palette, and has a help entry
- compatibility: existing commands and menu entries are unchanged
- acceptance: criterion 3
- tests: tests/integration/test_help.py
- post-merge source of truth: vscode-clutchwork/package.json and clutch/help.py

## Scope in / Scope out
Scope in:
- clutch/observe.py: add the `providerInstalls` key to `extension_fields` as stated in the boundary contract, importing `ADAPTERS` from clutch.providers.
- vscode-clutchwork/package.json: add the `clutch.updateProvider` command (title `Update Provider CLI...`), a `view/title` entry `"when": "view == clutch.tickets", "group": "clutch@8"`, and a `commandPalette` entry with `"when": "false"`, matching the existing `clutch.engine` entries.
- vscode-clutchwork/extension.js: register `clutch.updateProvider` exactly like `clutch.engine`: `showQuickPick(snapshot.snap?.providerInstalls ?? [])`, then `devCommand(...choice.argv)` for the chosen entry.
- clutch/help.py: add `"clutch.updateProvider": "Choose a provider CLI to update."` to the extension command descriptions so `COMMANDS` covers it.
- tests/unit/test_observe_extension_fields.py: add the `providerInstalls` value to the exact expected dict.
- New tests/unit/test_observe_provider_installs.py: the entries cover every `ADAPTERS` name once, in sorted order, plus the all entry last, and every argv parses with the clutch CLI parser as `provider install`.
Scope out:
- `clutch provider install` itself, the snapshot shape outside `extension_fields`, other menus, and the drain's preflight notice.

## Scope fence
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/package.json
- tests/unit/test_observe_extension_fields.py
- tests/unit/test_observe_provider_installs.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_observe_provider_installs.py` proves `providerInstalls` has `len(ADAPTERS) + 1` entries, the per-provider argv lists are `["provider", "install", name]` in sorted name order (not one entry per configured route or an empty list), and the last entry's argv names every adapter.
2. `./dev.py test tests/unit/test_observe_provider_installs.py` proves every `providerInstalls` argv parses with the clutch parser to the `provider install` verb with the listed names, not a refusal.
3. `./dev.py test tests/integration/test_help.py tests/integration/test_extension_argv.py tests/unit/test_help.py` passes with `clutch.updateProvider` in package.json and `COMMANDS`, and with no literal argv in extension.js.

## Verification
```
./dev.py test tests/unit/test_observe_provider_installs.py tests/unit/test_observe_extension_fields.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_extension_argv.py
```

## Definition of rejected
JavaScript builds or filters provider argv, hardcodes provider names, or the command appears outside the Tickets view title overflow menu.

## Time budget
- expected: 12m
- stuck: 24m
