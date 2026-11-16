---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- vscode-clutchwork/extension.js
- clutch/observe.py::snapshot
- tests/vscode_task_identity.js

## Goal / Why
Every clutch verb the VS Code extension runs, except `snapshot` itself, takes its argv from one table in `clutch/observe.py` that `snapshot` emits. After a snapshot has loaded, `clutchRoot()` returns the snapshot's `root`, not a filesystem probe.

Today `order`, `review`, `lint`, `run`, `triage`, `dismiss`, `serve`, `stop`, `stats --tree` and `prompt <kind>` are JavaScript literals in `vscode-clutchwork/extension.js`. The `order` flags `--priority` and `--runs-before` are also literals there. The repo rule "The extension is a thin wrapper; clutch owns the logic" says JavaScript only runs argv that the snapshot supplies. `confirm`, `reject`, `drain` and the Engine picker already do this. This is roadmap row 24 (`docs/roadmap.md`, section 3.5). Why it matters: a verb rename or flag change then needs one Python edit and cannot leave the extension running a stale command line.

`snapshot` is the bootstrap verb. The extension needs a root and a command to run it before any snapshot exists. Its argv and the first-run folder probe in `clutchRoot()` stay as they are. Once a snapshot has published, the snapshot's root wins.

## Scope in / Scope out
In `clutch/observe.py`:
- Add a module-level function `extension_fields(root: Path) -> dict` returning exactly three keys.
  - `root`: `str(root.resolve())`.
  - `commands`: the argv-prefix table below.
  - `orderFlags`: `{"priority": "--priority", "runsBefore": "--runs-before"}`.
- `commands` is exactly: `review` `["review"]`, `lint` `["lint"]`, `run` `["run"]`, `triage` `["triage"]`, `dismiss` `["dismiss"]`, `serve` `["serve"]`, `stop` `["stop"]`, `order` `["order"]`, `stats` `["stats", "--tree"]`, `askDiagnose` `["prompt", "diagnose"]`, `askReview` `["prompt", "review"]`, `askDrafts` `["prompt", "drafts"]`, `askDrainLoop` `["prompt", "drain-loop"]`, `askBox` `["prompt", "box"]`.
- `snapshot` spreads `**extension_fields(ctx.root)` into its returned dict. Nothing else in `snapshot` changes. `drainCommand`, `engineVerbs` and `verdictCommands` stay as they are.

In `vscode-clutchwork/extension.js`:
- Replace every literal verb argv listed above with the matching `snapshot.snap.commands` entry, and the two order flags with `snapshot.snap.orderFlags`. Existing stems and ids are appended after the table argv, as today.
- `StatsTree.refresh` keeps appending `--window` and the setting value to the `stats` argv.
- Add a module-level `known` root. `Snapshot.publish` sets it from `snap.root` when a snapshot is present. `clutchRoot()` returns `known` when set, else runs the existing folder probe.
- The extension adds no verb, flag or root logic of its own.

In `tests/vscode_task_identity.js`: this node harness calls the review and lint handlers with no snapshot loaded, so it must load one first. Its `execFile` stub answers the `snapshot` verb with a minimal JSON snapshot carrying `root`, `commands` and `orderFlags`. Its output shape, a JSON array of `{type, args}` task definitions, stays unchanged.

Out of scope: the `snapshot` argv, `confirm`, `reject`, `drain`, `engineVerbs`, help text, `package.json`, `docs/`. The extension surface set does not change, so `clutch/help.py` is untouched. No existing test file other than `tests/vscode_task_identity.js` is edited. The new tests go in new files.

## Scope fence
- clutch/observe.py
- vscode-clutchwork/extension.js
- tests/vscode_task_identity.js
- tests/unit/test_observe_extension_fields.py
- tests/integration/test_extension_argv.py

## Acceptance criteria
1. `tests/unit/test_observe_extension_fields.py` asserts `extension_fields(tmp_path)` equals `{"root": str(tmp_path.resolve()), "commands": <the 14-entry table in Scope in>, "orderFlags": {"priority": "--priority", "runsBefore": "--runs-before"}}`. A missing key or a changed argv fails the test; an extra key also fails it.
2. `tests/integration/test_extension_argv.py` reads `vscode-clutchwork/extension.js` and asserts that the regex `devCommand\(\s*['\"]` has no match. This rules out a literal verb passed to `devCommand`.
3. The same test asserts that the regex `\[\s*['\"](review|lint|run|triage|dismiss|serve|stop|order|stats|prompt)['\"]` has no match in `extension.js`. This rules out a verb array literal passed to `runData`, `openClaude` or `orderTicket`. It also asserts that the strings `--priority` and `--runs-before` do not appear in `extension.js`.
4. The same test asserts that `extension.js` contains `snap.root` and that the `snapshot` verb literal `['snapshot']` appears exactly once, so the bootstrap is not lost.
5. `node tests/vscode_task_identity.js` exits 0 and prints `[{"type":"clutch","args":["review","x"]},{"type":"clutch","args":["lint","x"]},{"type":"clutch","args":["review","x"]}]`. A `TypeError` from reading `commands` of an unloaded snapshot is the wrong result this rules out.
6. `./dev.py test tests/integration/test_watch.py tests/integration/test_vscode_command_not_found.py tests/integration/test_step_icons.py` passes unchanged. The snapshot gains keys and loses none.

## Verification
```
./dev.py test tests/unit/test_observe_extension_fields.py tests/integration/test_extension_argv.py tests/integration/test_watch.py tests/integration/test_vscode_command_not_found.py tests/integration/test_step_icons.py
node tests/vscode_task_identity.js
```

## Definition of rejected
The branch is rejected if `extension.js` still holds a literal verb argv other than `snapshot`, or if it computes any argv, flag or root itself instead of reading the snapshot. It is also rejected if it adds a second root source that bypasses `snap.root`, adds a compatibility path for a snapshot without `commands`, or edits an existing snapshot key.

## Time budget
- expected: 40m
- stuck: 90m
