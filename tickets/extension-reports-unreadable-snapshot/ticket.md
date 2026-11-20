---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/README.md
- tests/integration/test_step_icons.py
- tests/vscode_step_icons.js

## Goal / Why
When the installed extension cannot read the snapshot that `clutch view snapshot` returns, the Tickets view shows its header and an empty list and says nothing (2026-11-20: `hot-paths-into-ticket-detail` removed `hotPaths` from the snapshot, the installed copy of view.js still read `snap.hotPaths.map`, threw after drawing the header, and the list stayed blank). After this ticket each of the three snapshot-reading views (Tickets, Suggestion Box, Details) catches an exception while drawing a snapshot and replaces its header (the Details view, its body) with `cannot draw the clutch snapshot: <error message>` followed by the existing `Open setup help` link, so a snapshot shape the installed extension cannot read is reported on screen with the error text. `vscode-clutchwork/README.md` gains a short troubleshooting entry saying that this message means the installed extension is older than the clutch it reads, and that `./dev.py vscode` reinstalls it.

Why: an installed extension is a separate copy from the repo, so any snapshot shape change leaves it stale until reinstalled, and a silent blank list reads as "no tickets".

## Boundary contract
### Extension snapshot draw failure reporting
- disposition: extend
- owner: vscode-clutchwork/media/view.js
- consumers: the person reading the Tickets, Suggestion Box and Details views
- observable change: a thrown error while drawing a snapshot now produces visible text in the view; the existing `snapshot failed: <message>` path for a failed snapshot command is unchanged
- compatibility: preserves the drawn output for every snapshot a view can read today; adds no snapshot field and reads no clutch constant
- acceptance: drawing a snapshot that lacks a field the view reads leaves the header text `cannot draw the clutch snapshot:` with the error message
- tests: tests/integration/test_extension_draw_failure.py
- post-merge source of truth: vscode-clutchwork/media/view.js

## Scope in / Scope out
In: in view.js, box.js and detail.js the message handler wraps the draw call in `try`/`catch` and, on a throw, sets the header (detail.js: the `detail` element) to `cannot draw the clutch snapshot: ` plus the error's message and the `Open setup help` link that each handler already builds for the `error` message. Create tests/vscode_draw_failure.js, a node harness shaped like tests/vscode_step_icons.js: it loads a media script against a minimal fake DOM, sends it a `data` message whose snapshot lacks `rows`, and prints the header text as JSON. Create tests/integration/test_extension_draw_failure.py, which runs the harness for view.js, box.js and detail.js and asserts each header starts with `cannot draw the clutch snapshot:`. vscode-clutchwork/README.md gets the troubleshooting entry described in Goal / Why.

Out: a version number or schema field in the snapshot, any change to the Python snapshot, and the extension host (extension.js).

## Scope fence
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/README.md
- tests/vscode_draw_failure.js
- tests/integration/test_extension_draw_failure.py

## Acceptance criteria
1. Sending view.js, box.js and detail.js a `data` message whose snapshot has no `rows`, `box` or `help` fields leaves each header (detail.js: the detail element) starting with `cannot draw the clutch snapshot:`, never empty or still `loading…`, checked by `./dev.py test tests/integration/test_extension_draw_failure.py`.
2. The `error` message path still produces `snapshot failed: <message>`, checked by `./dev.py test tests/integration/test_extension_draw_failure.py`.
3. `vscode-clutchwork/README.md` names `./dev.py vscode` in its troubleshooting entry, checked by `./dev.py test tests/integration/test_extension_draw_failure.py`.

## Verification
```
./dev.py test tests/integration/test_extension_draw_failure.py tests/integration/test_step_icons.py
```

## Definition of rejected
- The catch swallows the error without showing its message.
- The view script gains a clutch constant, a version comparison, or a policy choice.
- Any existing view draws differently for a valid snapshot.

## Time budget
- expected: 20m
- stuck: 40m
