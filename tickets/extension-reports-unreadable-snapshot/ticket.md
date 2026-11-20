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
When the installed extension cannot read the snapshot that `clutch view snapshot` returns, the Tickets view shows its header and an empty list and says nothing (2026-11-20: `hot-paths-into-ticket-detail` removed `hotPaths` from the snapshot, the installed copy of view.js still read `snap.hotPaths.map`, threw after drawing the header, and the list stayed blank). After this ticket each of the three snapshot-reading views (Tickets, Suggestion Box, Details) catches an exception while drawing a snapshot and replaces its header (the Details view, its body) with `cannot draw the clutch snapshot: <error message>` followed by an `Open setup help` link, so a snapshot shape the installed extension cannot read is reported on screen with the error text. `vscode-clutchwork/README.md` gains a short troubleshooting entry saying that this message means the installed extension is older than the clutch it reads, and that the fix is to update the extension from the Marketplace (Extensions view, then Update, then reload the window). The entry never names `./dev.py`, which exists only in the clutch repo and is not something a host has.

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
In: in view.js, box.js and detail.js the message handler wraps the draw call in `try`/`catch` and, on a throw, sets the header (detail.js: the `detail` element) to `cannot draw the clutch snapshot: ` plus the error's message and an `Open setup help` link. view.js and box.js already build that link for their `error` message; detail.js builds its own (an `a.link` whose click posts `{type: 'readme'}`, which `handleHelpMessage` in extension.js:145 already handles for the Details view) and sets it after the text as the contents of the `detail` element. view.js and box.js wrap their `data` branch; detail.js wraps its whole existing handler body in the try/catch and adds no type check, because `DetailsView.post` sends `{snap, focus}` with no `type` (extension.js:251). Create tests/vscode_draw_failure.js, a node harness shaped like tests/vscode_step_icons.js: it loads a media script against a minimal fake DOM, sends it a `data` message (for detail.js `{snap, focus: undefined}`, exactly as extension.js:251 posts it) whose snapshot lacks `rows`, and prints the header text as JSON. Create tests/integration/test_extension_draw_failure.py, which runs the harness for view.js, box.js and detail.js and asserts each header starts with `cannot draw the clutch snapshot:`. vscode-clutchwork/README.md gets the troubleshooting entry described in Goal / Why.

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
2. For view.js and box.js, a `{type: 'error', message: 'boom'}` message still sets a header starting with `snapshot failed: boom`, checked by `./dev.py test tests/integration/test_extension_draw_failure.py`.
3. A minimal valid snapshot (view.js: `counts`, `help`, `headerHelp`, `rows: []`, `verdictDecisions: []` with a stub `renderGraph` global; box.js: `box: []`, `boxCounts`, `boxHeaderHelp`, `help`; detail.js: `rows: []` and no `runningStem`, which draws `Nothing running`) leaves each header (detail.js: the detail element) without the text `cannot draw the clutch snapshot`, checked by `./dev.py test tests/integration/test_extension_draw_failure.py`.
4. `vscode-clutchwork/README.md` has a troubleshooting entry that names updating the extension from the Marketplace and contains no `./dev.py`, checked by `./dev.py test tests/integration/test_extension_draw_failure.py`.

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
