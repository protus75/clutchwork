---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- vscode-help-catalog
- vscode-help-snapshot

## Context
- vscode-clutchwork/extension.js
- vscode-clutchwork/package.json
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/README.md
- clutch/observe.py::snapshot
- clutch/stats.py::stats_tree
- clutch/docs/host-contract.md#VS Code extension
- docs/how-clutch-works.md
- tests/integration/test_step_icons.py
- tests/integration/test_vscode_command_not_found.py
- tests/regress_vscode_task_identity.py
- tests/vscode_step_icons.js

## On-demand
- tests/vscode_task_identity.js
- tests/vscode_command_not_found.js

## Goal / Why
The VS Code extension's row statuses, section badges, lock icons, step kinds, Suggestion Box classes and counts, Stats rows, menu actions, and settings carry no hover text or doc links. `vscode-help-snapshot` puts help topics into the snapshot (`help`, `helpPick`, `headerHelp`, `boxHeaderHelp`, per-row and per-step keys, step `tooltip`) and Stats top-level `tooltip`s. This ticket makes the extension draw that help, adds the `clutch.help` command, and gives every setting help in the same shape, following the thin-wrapper rule: JavaScript only reads keys the snapshot or `stats --tree` row supplies.

## Scope in / Scope out
Scope in:
- `clutch/help.py` gains a `command.clutch.help` topic and maps `clutch.help` to it in its command map.
- `vscode-clutchwork/package.json` changes:
  - adds a `clutch.help` command (title `Help`, icon `$(question)`), visible in the Command Palette and placed in every clutch view's title overflow menu;
  - replaces each setting's `description` with a `markdownDescription` in the same three-part shape (what it is, a `Before:` line, an `After:` line), ending with a link to its doc section as a `https://github.com/protus75/clutchwork/blob/main/...#slug` URL. `clutch.command` links to `clutch/docs/host-contract.md` `## VS Code extension`. `clutch.statsWindow`, `clutch.refreshSeconds`, `clutch.unavailableMenuItems`, and `clutch.playAction` link to the `docs/how-clutch-works.md` section 2.2 heading;
  - adds `viewsWelcome` entries for `clutch.steps` and `clutch.stats` when they are empty: one sentence plus `[Open clutch help](command:clutch.help)`.
- `vscode-clutchwork/extension.js` changes:
  - registers `clutch.help`, which shows `snap.helpPick`. For the chosen item it runs `item.command` when the item has one, and otherwise runs `clutch.openHelp(item.topic)`;
  - registers an internal `clutch.openHelp(topic)`, not contributed. It opens a `path` link in a text editor with the selection at `line` and a `url` link with `openExternal`;
  - shows Recent Steps tooltips as a trusted `MarkdownString` of `step.tooltip` plus a `command:clutch.openHelp` "Learn more" link;
  - shows Stats top-level tooltips from `row.tooltip`;
  - handles a webview `{type: 'help', topic}` message by running `clutch.openHelp`;
  - handles a webview `{type: 'readme'}` message by opening the bundled `README.md` in the Markdown preview.
- Webview changes:
  - `media/view.js`: header counts and lock icons get `title` from their `headerHelp` topics; each row gets `title` from its status topic `text`; the priority tag gets `title` from the row's `priorityHelp` topic `text`.
  - `media/box.js`: header counts and rows get `title` from their topics.
  - `media/detail.js`: the section badge gets `title` from the section topic, and the status line is followed by the status topic `text` and a "Learn more" link; a `Next` section lists each `next` topic's `what` with its own "Learn more" link; a box message shows its class and outcome topic `text` the same way.
  - `media/view.js` and `media/box.js`: the `snapshot failed` error state adds an "Open setup help" link that posts `{type: 'readme'}`.
  - `media/view.css`: styling for the help text and links only.
- `tests/vscode_step_icons.js`, `tests/vscode_task_identity.js`, and `tests/vscode_command_not_found.js` may gain only the `vscode` mock members the new extension code calls, such as `MarkdownString`. Their assertions do not change.
- `tests/integration/test_help.py::test_manifest_covered` gains the settings and `clutch.help` placement checks in criterion 1.

Scope out:
- `vscode-clutchwork/README.md` `## Help` section, docs, and the agent rule belong to `vscode-help-docs`.
- The lifecycle panel and `media/ticket-lifecycle.svg` stay as they are, because the image is static.
- A `contributes.walkthroughs` onboarding flow is left out because it would copy the install steps that `clutch/docs/host-contract.md` owns.
- Priority QuickPick items, the Activity Bar badge tooltip, and `showErrorMessage` texts stay as they are.
- The Details view's empty-state sentence stays as it is: the snapshot names no topic key for the empty state, and JavaScript may not hard-code one.
- `clutch/observe.py` and `clutch/stats.py` stay as they are.
- No help text is written in JavaScript. The only user-visible JavaScript strings added are the link labels "Learn more" and "Open setup help", plus the section heading `Next`. Command ids, webview message types, and VS Code API arguments are not help text and may be added as needed.

## Scope fence
- clutch/help.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/package.json
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/detail.js
- vscode-clutchwork/media/box.js
- vscode-clutchwork/media/view.css
- tests/integration/test_help.py
- tests/vscode_step_icons.js
- tests/vscode_task_identity.js
- tests/vscode_command_not_found.js

## Acceptance criteria
1. `tests/integration/test_help.py::test_manifest_covered` reads `vscode-clutchwork/package.json`.
   - Every `contributes.commands[].command`, including `clutch.help`, is in the command map, and every mapped topic exists.
   - Every `contributes.views.clutch[].id` has a `view.*` topic, and `clutch.help` appears in `menus.view/title` for every one of those view ids.
   - Every `contributes.configuration.properties` entry has a `markdownDescription` containing `Before:` and `After:` and no `description` key. Its GitHub link starts with the package metadata Repository URL plus `/blob/main/`, names a repo file that exists, and has a fragment equal to the GitHub slug of a heading in that file.

   A new command, view, or setting without help fails.
2. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_watch.py` passes.
3. `node --check` exits 0 for `vscode-clutchwork/extension.js`, `vscode-clutchwork/media/view.js`, `vscode-clutchwork/media/detail.js`, and `vscode-clutchwork/media/box.js`.
4. `./dev.py test tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py` passes, so no step kind's icon becomes `null` and the not-found message text is unchanged. `uv run python tests/regress_vscode_task_identity.py` prints `{"regression_result": "pass"}` and exits 0, so `activate()` still runs under the harness mock.
5. `./dev.py test` exits 0.

## Verification
```
node --check vscode-clutchwork/extension.js
node --check vscode-clutchwork/media/view.js
node --check vscode-clutchwork/media/detail.js
node --check vscode-clutchwork/media/box.js
./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_watch.py
./dev.py test tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py
uv run python tests/regress_vscode_task_identity.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- JavaScript writes help text, builds a topic key from a string, parses a status or doc, or looks up help any other way than reading a key the snapshot or `stats --tree` row supplies;
- `clutch/help.py` contains the GitHub repository URL as a literal;
- a mock in `tests/vscode_*.js` changes an assertion;
- `clutch/observe.py`, `clutch/stats.py`, `clutch/docs/host-running.md`, or `clutch/__main__.py` changes.

## Time budget
- expected: 75m
- stuck: 120m
