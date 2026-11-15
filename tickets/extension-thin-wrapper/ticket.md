---
state: confirmed
source: human
priority: P3
kind: chore
---

## Depends on
- observe-verbs-host-extension

## Context
- clutch/ask.py
- clutch/tickets.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- tests/test_watch.py

## Goal / Why
The extension must be a thin drawing wrapper: all logic lives in the `clutch` package under pytest (the CLAUDE.md rule "The extension is a thin wrapper; clutch owns the logic"). An audit on 2026-11-06 found decisions still made in JavaScript, untested, after `observe-verbs-host-extension` moves the snapshot into `clutch/observe.py` and the commands onto argv:
- `extension.js` `STEM` copies the stem rule `clutch/tickets.py` owns.
- `askClaude` maps `diagnose` to `running` when the row's section is running.
- `orderTicket` decides which tickets are runs-before choices and hardcodes `P0`..`P3`.
- `StepsTree.getTreeItem` picks icons by matching step text (`' start'`, `'ok'`, `'ended without a stop record'`, `' started '`); a wording change in Python silently breaks it.
- `detail.js` `when()` computes "N min/hr/days ago", and `view.js` counts rows per section for the header.

After this change the snapshot carries each of these as data and the extension only displays it.

## Scope in / Scope out
- In: `clutch/observe.py` snapshot:
  - each step carries `kind` from a closed set (`stage_start`, `stage_ok`, `stage_failed`, `engine_start`, `engine_stop`, `engine_lost`), set where the step is built;
  - top level `priorities` (the ticket priority values `clutch/tickets.py` defines) and `counts` (rows per section);
  - each unmerged row carries `runsBeforeChoices`: the unmerged stems other than itself;
  - each time shown as relative carries a Python-rendered `...Ago` text beside it.
- In: `clutch prompt diagnose <stem>` renders the `running` prompt when the stem is running; the extension always sends `diagnose`.
- In: `extension.js`: delete `STEM` and every check of it (argv commands need no stem check); `orderTicket` uses `priorities` and `runsBeforeChoices`; `getTreeItem` maps `kind` to a ThemeIcon through a lookup table only.
- In: `detail.js` shows the `...Ago` texts; `view.js` builds the header from `counts`.
- In: tests in `tests/test_watch.py` for every new snapshot field and for the `diagnose` prompt choice.
- Out: the graph layout, colors, menu conditions, `extension-engine-picker`'s picker, engine behavior.
- Touch no file outside `## Scope fence`.

## Scope fence
- clutch/observe.py
- clutch/ask.py
- clutch/__main__.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- tests/test_watch.py
- tests/test_ask.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `vscode-clutchwork/extension.js`, `view.js`, and `detail.js` contain none of `STEM`, `'P0'`, `includes('ok')`, `endsWith(' start')`, `Date.now()`, or `=== 'running' ? 'running'`; the third Verification command checks it.
2. `tests/test_watch.py` asserts each step `kind`, `priorities`, `counts`, `runsBeforeChoices`, and the `...Ago` texts.
3. A test asserts `clutch prompt diagnose <stem>` renders the running prompt for a running stem.
4. `node --check` passes for the three JavaScript files, and `uv run pytest -q` exits 0.

## Verification
```
uv run pytest -q tests/test_watch.py
node --check vscode-clutchwork/extension.js
uv run python -c "from pathlib import Path; t = ''.join((Path('vscode-clutchwork') / p).read_text() for p in ('extension.js', 'media/view.js', 'media/detail.js')); assert not any(s in t for s in ('STEM', \"'P0'\", \"includes('ok')\", \"endsWith(' start')\", 'Date.now()', \"=== 'running' ? 'running'\"))"
node --check vscode-clutchwork/media/view.js
node --check vscode-clutchwork/media/detail.js
uv run pytest -q
```

## Definition of rejected
Reject the branch if any of the following holds:
- the extension still decides, computes, or parses anything the snapshot could supply;
- a snapshot field duplicates a value `clutch/tickets.py` already owns instead of reading it;
- a file outside `## Scope fence` changes.

## Time budget
- expected: 60m
- stuck: 150m
