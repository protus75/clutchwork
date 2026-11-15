---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- review-unmerged-provisional

## Runs before
- vscode-snapshot-display
- vscode-graph-segments

## Context
- clutch/observe.py::snapshot
- clutch/control.py::ControlInbox.consume
- clutch/__main__.py::_verdict
- clutch/__main__.py::_review
- clutch/__main__.py::_order
- tests/integration/test_watch.py::test_snapshot_display_fields
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/package.json

## Goal / Why
The extension's right-click menus decide when each action shows, and whether it is greyed out, in `package.json` `when` and `enablement` clauses. Those clauses copy clutch's rules: the section regex `^(queued|blocked)$`, `!= 'merged'`, and which verbs need the writer lock (`!clutchEngine`). The thin-wrapper rule bans this, and the copies are wrong:
- On 2026-11-08 the owner could not confirm a held ticket from the menu while `serve` ran. The engine accepts confirm and reject for any known stem (`ControlInbox.consume`), and `clutch confirm`/`reject` hands the request to the running engine (`_verdict`).
- Review is offered on invalid rows, which `review` refuses at intake.

After this change, Python decides every ticket and box menu action. Each snapshot row carries a `menu` object of context keys, each set to `on`, `locked` (possible but the writer lock is held) or `off`. The extension passes `menu` through unchanged, and `package.json` only maps those values and the `clutch.unavailableMenuItems` setting to show, grey or hide.

## Scope in / Scope out
- In: `clutch/observe.py` `snapshot`. Every row in `rows` and every row in `box` gains `menu: dict[str, str]`, each value one of `on`, `locked`, `off`. "Engine alive" is the snapshot's existing `engine` value. A row is "invalid" when it is one of the `invalid:` rows. Ticket rows:
  - `clutchReview`: `off` unless the section is `queued` or `blocked` and the row is not invalid; then `locked` when the engine is alive, else `on`. (This ticket depends on `review-unmerged-provisional`, so unmerged dependencies no longer block review.)
  - `clutchLint`: `on` for every row whose section is not `merged`, else `off`.
  - `clutchRun`: `off` unless `runnable`; then `locked` when the engine is alive, else `on`.
  - `clutchConfirm` and `clutchReject`: `on` when the row is a draft or held, and is committed or the engine is not alive; else `off`. They are never `locked`: a running engine accepts them.
  - `clutchAskDiagnose`: `on` when the section is not `merged`, else `off`. `clutchAskReview`: `on` for `queued` or `blocked` rows, else `off`.
  - `clutchPriority` and `clutchRunsBefore`: `on` for `queued` or `blocked` rows that are not invalid, else `off`. `order` edits the working tree and takes no lock.
- In: box rows. `clutchTriage` and `clutchDismiss` are `off` unless the message is pending; then `locked` when the engine is alive, else `on`.
- In: `vscode-clutchwork/media/view.js` and `vscode-clutchwork/media/box.js`.
  - The row's `vscodeContext` becomes `{...r.menu, clutchStem: r.stem, preventDefaultContextMenuItems: true}` in `view.js`, and `{...row.menu, clutchIds, clutchPath, clutchLink, preventDefaultContextMenuItems: true}` in `box.js`.
  - Drop `clutchSection`, `clutchHeld`, `clutchDraft`, `clutchRunnable`, `clutchCommitted`, `clutchEngine` and `clutchState`.
- In: `vscode-clutchwork/package.json`. For each action key `K` above, the `webview/context` entry's `when` is the view check plus `(K == 'on' || K == 'locked' && config.clutch.unavailableMenuItems != 'hide')`, and the command's `enablement` is `K == 'on'`. `clutch.ticket.open`, `clutch.box.open`, `clutch.box.link` and `clutch.box.discuss` keep their presence checks (`clutchStem`, `clutchPath`, `clutchLink`, `clutchIds`). The `view/title` entries are unchanged.
- In: `tests/integration/test_watch.py`. A snapshot test asserts `menu` for each of these cases:
  - a held committed row while the engine is alive: `clutchConfirm` `on`, `clutchRun` `off`;
  - the same held row with an uncommitted edit (stem in `dirty`, not in `new`): with the engine alive, `clutchConfirm` and `clutchReject` `off`; with no engine, both `on`;
  - a queued runnable row with no engine (`clutchRun`/`clutchReview` `on`) and with an engine (`locked`);
  - an invalid row: `clutchReview` and `clutchPriority` `off`;
  - a merged row: `clutchLint` `off`;
  - a pending box message with an engine: `clutchTriage` `locked`.
- Out: the `view/title` menu, the CLI verbs, the rest of the extension's JavaScript (`vscode-snapshot-display` and `vscode-graph-segments` cover it), and `clutch.unavailableMenuItems` itself.

## Scope fence
- clutch/observe.py
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/package.json
- tests/integration/test_watch.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_watch.py` passes. It includes a held committed row whose `menu["clutchConfirm"]` is `on` while the engine is alive, not `off`, the same held row with an uncommitted edit whose `menu["clutchConfirm"]` is `off` while the engine is alive, not `on`, and an invalid row whose `menu["clutchReview"]` is `off`, not `on`.
2. No `when` or `enablement` in `vscode-clutchwork/package.json` mentions `clutchSection`, `clutchHeld`, `clutchDraft`, `clutchRunnable`, `clutchCommitted`, `clutchEngine` or `clutchState`, checked by reading the file.
3. `vscode-clutchwork/media/view.js` and `vscode-clutchwork/media/box.js` build `vscodeContext` by spreading the row's `menu`, with no condition, checked by reading the files.

## Verification
```
./dev.py test tests/integration/test_watch.py
```

## Definition of rejected
Any menu `when` or `enablement` decides availability from anything but a snapshot `menu` value and the `clutch.unavailableMenuItems` setting, or JavaScript computes a `menu` value.

## Time budget
- expected: 30m
- stuck: 75m
