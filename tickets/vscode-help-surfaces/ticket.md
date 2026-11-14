---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- vscode-help-registry

## Context
- vscode-chupa/extension.js
- vscode-chupa/package.json
- vscode-chupa/media/view.js
- vscode-chupa/media/detail.js
- vscode-chupa/media/box.js
- vscode-chupa/README.md
- chupa/observe.py::snapshot
- chupa/stats.py::stats_tree
- chupa/docs/host-contract.md#VS Code extension
- docs/how-chupa-works.md
- tests/integration/test_step_icons.py
- tests/integration/test_vscode_command_not_found.py
- tests/regress_vscode_task_identity.py
- tests/vscode_step_icons.js

## On-demand
- tests/vscode_task_identity.js
- tests/vscode_command_not_found.js

## Goal / Why
The VS Code extension's row statuses, section badges, lock icons, step kinds, Suggestion Box classes and counts, Stats rows, menu actions, and settings carry no hover text or doc links. `vscode-help-registry` puts help topics into the snapshot (`help`, `helpPick`, `headerHelp`, `boxHeaderHelp`, per-row and per-step keys, step `tooltip`) and Stats top-level `tooltip`s. This ticket makes the extension draw that help, adds the `chupa.help` command, and gives every setting help in the same shape, following the thin-wrapper rule: JavaScript only reads keys the snapshot or `stats --tree` row supplies.

## Scope in / Scope out
Scope in:
- `chupa/help.py` gains a `command.chupa.help` topic and maps `chupa.help` to it in its command map.
- `vscode-chupa/package.json` changes:
  - adds a `chupa.help` command (title `Help`, icon `$(question)`), visible in the Command Palette and placed in every chupa view's title overflow menu;
  - replaces each setting's `description` with a `markdownDescription` in the same three-part shape (what it is, a `Before:` line, an `After:` line), ending with a link to its doc section as a `https://github.com/protus75/chupa/blob/main/...#slug` URL. `chupa.command` links to `chupa/docs/host-contract.md` `## VS Code extension`. `chupa.statsWindow`, `chupa.refreshSeconds`, `chupa.unavailableMenuItems`, and `chupa.playAction` link to the `docs/how-chupa-works.md` section 2.2 heading;
  - adds `viewsWelcome` entries for `chupa.steps` and `chupa.stats` when they are empty: one sentence plus `[Open chupa help](command:chupa.help)`.
- `vscode-chupa/extension.js` changes:
  - registers `chupa.help`, which shows `snap.helpPick`. For the chosen item it runs `item.command` when the item has one, and otherwise runs `chupa.openHelp(item.topic)`;
  - registers an internal `chupa.openHelp(topic)`, not contributed. It opens a `path` link in a text editor with the selection at `line` and a `url` link with `openExternal`;
  - shows Recent Steps tooltips as a trusted `MarkdownString` of `step.tooltip` plus a `command:chupa.openHelp` "Learn more" link;
  - shows Stats top-level tooltips from `row.tooltip`;
  - handles a webview `{type: 'help', topic}` message by running `chupa.openHelp`;
  - handles a webview `{type: 'readme'}` message by opening the bundled `README.md` in the Markdown preview.
- Webview changes:
  - `media/view.js`: header counts and lock icons get `title` from their `headerHelp` topics; each row gets `title` from its status topic `text`; the priority tag gets `title` from `priority`.
  - `media/box.js`: header counts and rows get `title` from their topics.
  - `media/detail.js`: the section badge gets `title` from the section topic, and the status line is followed by the status topic `text` and a "Learn more" link; a `Next` section lists each `next` topic's `what` with its own "Learn more" link; a box message shows its class and outcome topic `text` the same way; the empty state shows the `view.chupa.details` topic `text`, not the hard-coded sentence.
  - `media/view.js` and `media/box.js`: the `snapshot failed` error state adds an "Open setup help" link that posts `{type: 'readme'}`.
  - `media/view.css`: styling for the help text and links only.
- `tests/vscode_step_icons.js`, `tests/vscode_task_identity.js`, and `tests/vscode_command_not_found.js` may gain only the `vscode` mock members the new extension code calls, such as `MarkdownString`. Their assertions do not change.
- `tests/integration/test_help.py::test_manifest_covered` gains the settings and `chupa.help` placement checks in criterion 1.

Scope out:
- `vscode-chupa/README.md` `## Help` section, docs, and the agent rule belong to `vscode-help-docs`.
- The lifecycle panel and `media/ticket-lifecycle.svg` stay as they are, because the image is static.
- A `contributes.walkthroughs` onboarding flow is left out because it would copy the install steps that `chupa/docs/host-contract.md` owns.
- Priority QuickPick items, the Activity Bar badge tooltip, and `showErrorMessage` texts stay as they are.
- `chupa/observe.py` and `chupa/stats.py` stay as they are.
- No help text is written in JavaScript. The only user-visible JavaScript strings added are the link labels "Learn more" and "Open setup help", plus the section heading `Next`. Command ids, webview message types, and VS Code API arguments are not help text and may be added as needed.

## Scope fence
- chupa/help.py
- vscode-chupa/extension.js
- vscode-chupa/package.json
- vscode-chupa/media/view.js
- vscode-chupa/media/detail.js
- vscode-chupa/media/box.js
- vscode-chupa/media/view.css
- tests/integration/test_help.py
- tests/vscode_step_icons.js
- tests/vscode_task_identity.js
- tests/vscode_command_not_found.js

## Acceptance criteria
1. `tests/integration/test_help.py::test_manifest_covered` reads `vscode-chupa/package.json`.
   - Every `contributes.commands[].command`, including `chupa.help`, is in the command map, and every mapped topic exists.
   - Every `contributes.views.chupa[].id` has a `view.*` topic, and `chupa.help` appears in `menus.view/title` for every one of those view ids.
   - Every `contributes.configuration.properties` entry has a `markdownDescription` containing `Before:` and `After:` and no `description` key. Its GitHub link starts with the package metadata Repository URL plus `/blob/main/`, names a repo file that exists, and has a fragment equal to the GitHub slug of a heading in that file.

   A new command, view, or setting without help fails.
2. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_watch.py` passes.
3. `node --check` exits 0 for `vscode-chupa/extension.js`, `vscode-chupa/media/view.js`, `vscode-chupa/media/detail.js`, and `vscode-chupa/media/box.js`.
4. `./dev.py test tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py` passes, so no step kind's icon becomes `null` and the not-found message text is unchanged. `uv run python tests/regress_vscode_task_identity.py` prints `{"regression_result": "pass"}` and exits 0, so `activate()` still runs under the harness mock.
5. `./dev.py test` exits 0.

## Verification
```
node --check vscode-chupa/extension.js
node --check vscode-chupa/media/view.js
node --check vscode-chupa/media/detail.js
node --check vscode-chupa/media/box.js
./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_watch.py
./dev.py test tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py
uv run python tests/regress_vscode_task_identity.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- JavaScript writes help text, builds a topic key from a string, parses a status or doc, or looks up help any other way than reading a key the snapshot or `stats --tree` row supplies;
- `chupa/help.py` contains the GitHub repository URL as a literal;
- a mock in `tests/vscode_*.js` changes an assertion;
- `chupa/observe.py`, `chupa/stats.py`, `chupa/docs/host-running.md`, or `chupa/__main__.py` changes.

## Time budget
- expected: 75m
- stuck: 120m
