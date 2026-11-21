---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Runs before
- extension-merged-hover-commit

## Context
- clutch/observe.py::MENU
- clutch/observe.py::row_menu
- clutch/help.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/media/view.js
- tests/integration/test_menu_verb_parity.py

## On-demand
- vscode-clutchwork/package.json

## Goal / Why
Getting a merged ticket's stem into another command or a chat today means retyping it. After this ticket, right-clicking a merged row in the Tickets view shows "Copy Stem", which puts that row's stem on the clipboard. Other rows don't show it.

## Boundary contract
### Ticket row menu
- disposition: extend
- owner: clutch/observe.py::MENU
- consumers: vscode-clutchwork/package.json `webview/context` `when` clauses and clutch/observe.py::snapshot row `menu` and `next`
- observable change: new extension-only entry `clutchCopyStem` for ticket rows, admitted (`on`) only when the row's section is `merged`, otherwise `off`; command `clutch.ticket.copyStem`
- compatibility: existing menu keys, admissions and lock handling are unchanged
- acceptance: criteria 1 and 2
- tests: tests/unit/test_menu_copy_stem.py and tests/integration/test_menu_verb_parity.py
- post-merge source of truth: clutch/observe.py

### Extension command and help
- disposition: extend
- owner: vscode-clutchwork/package.json and clutch/help.py
- consumers: VS Code users of the Tickets view
- observable change: command `clutch.ticket.copyStem` titled `Copy Stem` in the Tickets row context menu (group `1_open@2`) when `clutchCopyStem == 'on'`, hidden from the command palette, with a help entry; running it writes the row's `clutchStem` with `vscode.env.clipboard.writeText`
- compatibility: existing commands and menu entries are unchanged
- acceptance: criterion 3
- tests: tests/integration/test_help.py
- post-merge source of truth: vscode-clutchwork/package.json and clutch/help.py

## Scope in / Scope out
Scope in:
- clutch/observe.py: add `"clutchCopyStem": MenuEntry("ticket", lambda section: Admission("admit" if section == "merged" else "noop"), ("section",), extension_only=True, command="clutch.ticket.copyStem")` to `MENU`.
- vscode-clutchwork/package.json: add the command (title `Copy Stem`), a `webview/context` entry `"when": "webviewId == 'clutch.tickets' && clutchCopyStem == 'on'", "group": "1_open@2"`, and a `commandPalette` entry with `"when": "false"`.
- vscode-clutchwork/extension.js: register `clutch.ticket.copyStem` as `ctx => vscode.env.clipboard.writeText(ctx.clutchStem)`.
- clutch/help.py: add `"clutch.ticket.copyStem": "Copy the selected ticket's stem."` to the extension command descriptions.
- tests/integration/test_menu_verb_parity.py: add `"clutchCopyStem"` to the expected extension-only key set; nothing else changes there.
- New tests/unit/test_menu_copy_stem.py: `row_menu` gives `clutchCopyStem == "on"` for a merged row and `"off"` for queued, running and blocked rows.
Scope out:
- Copy actions for other sections or for box rows, and any change to view.js (the row context object already carries `clutchStem` and the menu keys).

## Scope fence
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/package.json
- tests/integration/test_menu_verb_parity.py
- tests/unit/test_menu_copy_stem.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_menu_copy_stem.py` proves `MENU["clutchCopyStem"].admission(section="merged")` admits and `queued`, `running` and `blocked` give `noop`, so `row_menu` yields `"on"` only for merged rows, not for every row.
2. `./dev.py test tests/integration/test_menu_verb_parity.py` proves snapshot ticket rows carry `clutchCopyStem` and the extension-only set is exactly `{"clutchAskDiagnose", "clutchAskReview", "clutchAskDrafts", "clutchCopyStem"}`.
3. `./dev.py test tests/integration/test_help.py tests/unit/test_help.py tests/integration/test_extension_argv.py` passes with `clutch.ticket.copyStem` in package.json and `COMMANDS`.

## Verification
```
./dev.py test tests/unit/test_menu_copy_stem.py tests/integration/test_menu_verb_parity.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_extension_argv.py tests/integration/test_watch.py
```

## Definition of rejected
JavaScript decides which rows show Copy Stem, the item appears on non-merged rows, or files outside the fence change.

## Time budget
- expected: 10m
- stuck: 20m
