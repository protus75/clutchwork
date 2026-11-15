---
state: rejected
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/observe.py::snapshot
- clutch/observe.py::recent_steps
- clutch/observe.py::STEP_NAMES
- clutch/observe.py::PHASE_NAMES
- clutch/observe.py::STEP_KINDS
- clutch/stats.py::stats_tree
- clutch/stats.py::project_stats
- clutch/status.py::SETTLED
- clutch/box.py::MessageClass
- clutch/__main__.py::_parser
- clutch/docs/host-running.md
- clutch/docs/host-contract.md#VS Code extension
- docs/how-clutch-works.md
- vscode-clutchwork/package.json
- tests/unit/test_host_running.py
- tests/integration/test_stats.py::test_stats_tree_generic_rows
- tests/integration/test_step_icons.py
- tests/integration/test_vscode_command_not_found.py
- tests/regress_vscode_task_identity.py

## On-demand
- tests/integration/test_watch.py
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py

## Goal / Why
The VS Code extension explains almost nothing on screen, and the one place with explanatory text, the Engine… picker, uses `detail` strings hand-copied into `clutch/observe.py::snapshot` that restate rows of the run guide's verb table and will drift from it.

This ticket builds the Python half of extension help: one help registry in `clutch/help.py`, delivered through the snapshot and `stats --tree` output, with tests that fail when a vocabulary value or contributed command or view lacks help, or a help link points at a missing heading. The extension surfaces that draw this help are `vscode-help-surfaces`; the docs and agent rule are `vscode-help-docs`.

Every topic has the same shape. A short description says what the thing is. A `Before:` line says what generally comes before it, and an `After:` line says what generally follows. A link opens the doc section that owns the fact.

Help text sources, in order of preference:
1. A string the code already owns: the status reasons `clutch/observe.py::snapshot` builds stay as they are, with their help attached alongside.
2. A string a doc owns: a verb topic's `what` sentence is the `What it does` cell of that verb's row in `clutch/docs/host-running.md`, read at snapshot time with backticks removed. That table is already pinned to the CLI parser by `tests/unit/test_host_running.py`.
3. Otherwise, text written in `clutch/help.py` that links to the doc heading that owns the fact. `Before:` and `After:` text is always written there.

Link targets, deterministic per doc file (no fallback path):
- A doc shipped in the package (`clutch/docs/*.md`, found as `Path(clutch.__file__).parent / "docs"`) links to that installed file and the 0-based line of the target heading. A verb topic links to the line of its verb-table row.
- A doc not shipped in the package (`docs/how-clutch-works.md`) links to `<Repository URL>/blob/main/<repo path>#<GitHub heading slug>`. The Repository URL is read from the installed package metadata (`importlib.metadata`, the `Project-URL` named `Repository`), never typed as a literal in `clutch/help.py`.

## Scope in / Scope out
Scope in:
- New `clutch/help.py` holds the help registry.
  - Topic keys form one closed vocabulary with kind prefixes: `view.<view id>`, `command.<command id>` (non-verb commands only), `verb.<verb>`, `section.<section>`, `status.<reason>`, `step.<step>`, `box.<message class>`, `boxOutcome.<outcome>`, `stat.<key>`, `lock.<engine|commit>`, and `priority`.
  - Each topic has `what`, `before`, `after`, and a link target (doc path plus heading, or for verbs, the verb row).
  - A command map sends each command id now in `vscode-clutchwork/package.json` `contributes.commands` to its topic: a verb-backed command maps to its `verb.*` topic, for example `clutch.ticket.review` to `verb.review` and `clutch.ticket.priority` to `verb.order`. Every other command has its own `command.*` topic. Every view id in `contributes.views.clutch` has a `view.*` topic, including `view.clutch.details`.
  - A function builds, for the snapshot, `{key: {"what", "before", "after", "text", "link"}}`. `text` is exactly `<what>\nBefore: <before>\nAfter: <after>`. `link` is `{"label", "path", "line"}` for a packaged doc and `{"label", "url"}` otherwise.
  - The same module supplies a builder for the Help picker list (`helpPick` below).
  - A link whose heading or verb row does not resolve raises; it does not return a partial map.
  - The builders take the doc reader (`read: Callable[[Path], str]`) and the Repository URL (`repo_url: str`) as parameters. The builders call `read` only for packaged docs under `Path(clutch.__file__).parent / "docs"`. A `url` link to a doc not shipped in the package is built from the heading text written in `clutch/help.py` and its computed GitHub slug, without reading that file. Unit tests pass a fake `read` serving in-memory text that holds every heading and verb row the registry links to, plus a fixed URL, so `tests/unit/test_help.py` reads no file and no package metadata. Checks against the real docs, the real manifest, and installed metadata live in `tests/integration/test_help.py`.
- `snapshot` takes everything it needs from `clutch/help.py` (the `help` map, `helpPick`, `headerHelp`, `boxHeaderHelp`, and the verb `what` text that `engineVerbs` shows) from one module-level function in `clutch/observe.py`. That function is the only place that passes `Path.read_text` and the `importlib.metadata` Repository URL to the builders; `snapshot` itself reads no doc and no metadata. `tests/unit/test_menu_admission.py` (both fixtures that fake `Path.read_text` with a dict of ticket paths) and `tests/unit/test_verdict_menu_parity.py` (the `world` fixture) monkeypatch that function to return a fixed in-memory payload, the same way they already fake `observe.journal` and `observe.load_tickets`. Their assertions do not change and they still read no disk.
- `clutch/observe.py::snapshot` adds these fields:
  - top-level `help`, the map above;
  - `helpPick`, an ordered QuickPick list, with one `{"kind": "separator", "label"}` per topic kind, then `{"label", "description", "detail", "topic"}` items, plus one final settings item `{"label", "detail", "command": "clutch.openSettings"}`, which carries `command` and no `topic`;
  - `headerHelp`, the topic keys for each Tickets header count and each lock indicator;
  - `boxHeaderHelp`, the topic key for each Suggestion Box header count.
- Each status branch in `snapshot` names its `status.*` key next to the text it builds; `snapshot` never parses status text. The branches are:
  - invalid, new, draft, held until change, held for keep or kill, waits on, not eligible;
  - interrupted, retry pending, after, ready;
  - running, merged, and each other settled state.

  These keys form a closed module-level vocabulary in `clutch/observe.py`.
- Snapshot items carry topic keys:
  - each ticket row carries `help: {"section": key, "status": key}`, and `priorityHelp` when it shows a priority tag;
  - each ticket row carries `next`, the help keys of the menu actions that are `on` for it, in menu order;
  - each box row carries `help: {"class": key, "outcome": key}`;
  - each step carries `help`, its `step.*` key (start, ok, and failed share one step topic) and `tooltip`, the full tooltip text that Python builds from the date, stem, step text, and topic text.
- In `engineVerbs`, `detail` becomes the `what` of the verb topic. This removes the hand-copied strings.
- `clutch/stats.py::stats_tree` gives each top-level row whose key has a `stat.<key>` topic a `tooltip` equal to that topic's `text`. Child rows do not change.
- `tests/integration/test_watch.py` changes one expectation: the `engineVerbs[0]` `detail` equals the `drain` row's `What it does` cell from `clutch/docs/host-running.md` with backticks removed, not the old literal. It also gains the snapshot help assertions in criterion 8.

Scope out:
- Every `vscode-clutchwork/` file, the `clutch.help` command and its topic, setting `markdownDescription`s, and the JavaScript mocks belong to `vscode-help-surfaces`.
- `CLAUDE.md`, `AGENTS.md`, `docs/how-clutch-works.md`, `clutch/docs/host-contract.md`, and `vscode-clutchwork/README.md` belong to `vscode-help-docs`.
- `clutch/docs/host-running.md` content, `clutch/__main__.py`, and `clutch/stats.py::project_stats` stay as they are.
- Shipping `docs/how-clutch-works.md` inside the package stays out of scope; it is linked on GitHub.

## Scope fence
- clutch/help.py
- clutch/observe.py
- clutch/stats.py
- tests/unit/test_help.py
- tests/integration/test_help.py
- tests/integration/test_watch.py
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py

## Acceptance criteria
1. `tests/unit/test_help.py::test_topic_shape`: every topic's `text` has exactly three lines.
   - Line 1 is the non-empty `what` and ends with `.`.
   - Line 2 starts with `Before: ` and line 3 starts with `After: `, each followed by non-empty text.

   A topic missing `before` or `after`, or with an empty `what`, fails.
2. `tests/integration/test_help.py::test_links_resolve`: every topic's link, built with `Path.read_text` and the installed metadata Repository URL, resolves.
   - A `path` link names a file under the installed `clutch/docs`, and its `line` holds the named heading or, for a verb, that verb's table row.
   - A `url` link starts with the package metadata Repository URL plus `/blob/main/`, names a repo file that exists, and has a fragment equal to the GitHub slug of a heading in that file.

   A link to a renamed or missing heading fails, as does a line number off by one.
3. `tests/unit/test_help.py::test_vocabularies_covered`: each of these has a topic:
   - `blocked`, `queued`, `running`, and `merged`;
   - every member of the `clutch/observe.py` status-key vocabulary;
   - every step in `STEP_KINDS` values;
   - every `clutch.box.MessageClass` member;
   - every box outcome (`pending`, `reopened`, `author`, `tombstone`, `declined`);
   - every top-level key of `project_stats` run on an empty journal;
   - both lock indicators;
   - every `engineVerbs` argv verb.

   Adding a value to any of these vocabularies without a topic fails.
4. `tests/integration/test_help.py::test_manifest_covered` reads `vscode-clutchwork/package.json`.
   - Every `contributes.commands[].command` is in the command map, and every mapped topic exists.
   - Every `contributes.views.clutch[].id` has a `view.*` topic.

   A new command or view without help fails.
5. `tests/integration/test_help.py::test_verb_what_from_run_guide`: for every `verb.*` topic, `what` equals that verb's `What it does` cell in `clutch/docs/host-running.md` with backticks removed. `tests/unit/test_help.py::test_verb_what_follows_run_guide` passes the builder in-memory run-guide text with the `review` cell rewritten and asserts that `verb.review`'s `what` changes to match. A separately typed string fails either test.
6. `tests/unit/test_help.py::test_unresolved_link_raises`: the builder raises in two cases, when given in-memory doc text with a linked heading renamed, and when given run-guide text missing a verb row. Returning a map without the topic fails.
7. `tests/unit/test_help.py::test_help_pick_list`: the Help picker builder returns one separator per topic kind, each before that kind's items. Every non-separator item except the last carries a `topic` that is a help key. The last item carries `"command": "clutch.openSettings"` and no `topic`.
8. `./dev.py test tests/integration/test_watch.py` passes with the existing snapshot fixture.
   - `snap["engineVerbs"][0]["detail"]` equals the `drain` row's `What it does` cell with backticks removed, not `"Run every eligible ticket to quiescence, then exit."`.
   - Every row's `help.section` and `help.status` and every key in its `next` are keys of `snap["help"]`.
   - Every step's `help` is a key of `snap["help"]`, and its `tooltip` contains that topic's `text`.
   - Every non-separator `helpPick` item carries either a `topic` that is a key of `snap["help"]`, or a `command`, which only the settings item carries.

   A row or step that names a key missing from the map fails.
9. `tests/unit/test_help.py::test_stats_tree_tooltips`: `stats_tree` of `project_stats` on an empty journal gives every top-level row a `tooltip` equal to its `stat.*` topic `text`. The existing `tests/integration/test_stats.py::test_stats_tree_generic_rows` still passes unchanged, so child rows have no `tooltip` key.
10. `./dev.py test tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py` passes with unchanged assertions and no disk read for docs or metadata.
11. `./dev.py test tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py` passes, and `uv run python tests/regress_vscode_task_identity.py` prints `{"regression_result": "pass"}` and exits 0, so the snapshot changes break no extension harness.
12. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_watch.py tests/integration/test_stats.py tests/unit/test_host_running.py
./dev.py test tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py
./dev.py test tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py
uv run python tests/regress_vscode_task_identity.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `clutch/help.py` contains the GitHub repository URL as a literal, or copies a verb's `What it does` text instead of reading it from `clutch/docs/host-running.md`;
- a link built by `clutch/help.py` falls back from a local path to a URL, or the reverse, for the same doc;
- `snapshot` reads a doc or package metadata other than through the one module-level help function;
- `engineVerbs` still carries a hand-written `detail` string;
- any file under `vscode-clutchwork/` changes;
- `clutch/docs/host-running.md`, `clutch/__main__.py`, or `project_stats` changes.

## Time budget
- expected: 75m
- stuck: 120m
