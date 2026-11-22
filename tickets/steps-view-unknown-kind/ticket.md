---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Runs before
- extension-provider-update-action

## Context
- vscode-clutchwork/extension.js
- tests/vscode_step_icons.js
- tests/integration/test_step_icons.py
- tests/integration/test_extension_draw_failure.py
- vscode-clutchwork/README.md
- docs/how-clutch-works.md#2. Commands

## Goal / Why
On 2026-11-21 at 21:28 a `clutch meta fill` run journaled the first `meta_start`/`meta_ok` engine-log steps. The installed extension build was older than the repo source (both said 0.4.4) and had no `meta_*` entries in `StepsTree.getTreeItem`'s icon table. `const [icon, color] = icons[step.kind]` threw on the undefined entry, and the whole Recent Steps view stopped rendering until the extension was reinstalled with `./dev.py vscode`.

The webviews (`media/view.js`, `media/box.js`, `media/detail.js`) already handle a snapshot they cannot draw: they show `cannot draw the clutch snapshot: <error>`, and `vscode-clutchwork/README.md` tells the reader to update the extension. `tests/integration/test_extension_draw_failure.py` pins that contract for those three views. Recent Steps, a native tree, is the one view without it.

After this ticket, a Recent Steps row whose `kind` is not in the icon table renders with the `warning` ThemeIcon. Its description reads `cannot draw the clutch snapshot: unknown step kind <kind>`, and every other row still renders normally. The README road then reaches people with an older extension.

## Boundary contract
### Recent Steps rendering
- disposition: extend
- owner: vscode-clutchwork/extension.js
- consumers: VS Code tree view `clutch.steps`, operators
- observable change: an unknown step kind yields a tree item with ThemeIcon `warning` and description `cannot draw the clutch snapshot: unknown step kind <kind>` instead of throwing; known kinds render exactly as today
- compatibility: the icon table and every known kind's icon are unchanged, so `tests/integration/test_step_icons.py` still passes
- acceptance: criteria 1 to 3
- tests: tests/integration/test_step_view_unknown_kind.py, tests/integration/test_step_icons.py
- post-merge source of truth: vscode-clutchwork/extension.js

## Scope in / Scope out
Scope in:
- In `StepsTree.getTreeItem`, when `icons[step.kind]` is undefined, set the item's icon to `new vscode.ThemeIcon('warning')` and its description to `cannot draw the clutch snapshot: unknown step kind ${step.kind}`. The label, tooltip and command stay as for any other row. This only maps a closed value to an icon through the lookup table, which the extension rule allows. It adds no filtering or derivation.
- New node harness `tests/vscode_step_unknown.js`, modeled on `tests/vscode_step_icons.js` (which stays unedited). It activates the extension with a stubbed `vscode` and prints `{"icon": <iconPath.id>, "description": <description>}` as JSON for a step whose kind is given on argv.
- New `tests/integration/test_step_view_unknown_kind.py` that runs the harness.
- `docs/how-clutch-works.md` section 2: in the Recent Steps sentences (the paragraph naming `STEP_KINDS`), add that an unknown kind renders with a warning row instead of breaking the view.

Scope out: version or build-skew detection, the webview draw-failure paths, `clutch/observe.py`, and the README (its road already covers this message).

## Scope fence
- vscode-clutchwork/extension.js
- tests/vscode_step_unknown.js
- tests/integration/test_step_view_unknown_kind.py
- docs/how-clutch-works.md

## Acceptance criteria
1. For a step with kind `not_a_kind`, the harness reports icon `warning` and description `cannot draw the clutch snapshot: unknown step kind not_a_kind`, not a thrown error and not a `null` icon; checked by `./dev.py test tests/integration/test_step_view_unknown_kind.py`.
2. For a known kind such as `check_ok`, the harness reports icon `checklist` and description equal to the step's `text`, not the warning text; checked by `./dev.py test tests/integration/test_step_view_unknown_kind.py`.
3. Every `STEP_KINDS` entry still maps to its own distinct icon; checked by `./dev.py test tests/integration/test_step_icons.py`.

## Verification
```
./dev.py test tests/integration/test_step_view_unknown_kind.py tests/integration/test_step_icons.py tests/integration/test_extension_draw_failure.py
```

## Definition of rejected
- Recent Steps hides or drops the unknown row instead of showing the warning.
- Any known kind's icon or color changes.
- Edits outside the fence, including `tests/vscode_step_icons.js`.

## Time budget
- expected: 10m
- stuck: 20m
