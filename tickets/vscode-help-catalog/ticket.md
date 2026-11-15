---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/observe.py::snapshot
- clutch/observe.py::STEP_NAMES
- clutch/observe.py::PHASE_NAMES
- clutch/observe.py::STEP_KINDS
- clutch/stats.py::project_stats
- clutch/status.py::SETTLED
- clutch/box.py::MessageClass
- clutch/docs/host-running.md
- clutch/docs/host-contract.md#VS Code extension
- vscode-clutchwork/package.json
- tests/unit/test_host_running.py
- docs/how-clutch-works.md

## Goal / Why
The VS Code extension explains almost nothing on screen. The one place with explanatory text, the Engine... picker, uses `detail` strings hand-copied into `clutch/observe.py::snapshot`. Those strings restate rows of the run guide's verb table and will drift from it.

This ticket builds only the help registry, a new standalone module `clutch/help.py`, with its unit and integration tests. It wires nothing into the snapshot or Stats. `vscode-help-snapshot` delivers this registry through `clutch/observe.py::snapshot` and `clutch/stats.py::stats_tree`.

Every topic has the same shape. A short description says what the thing is. A `Before:` line says what generally comes before it, and an `After:` line says what generally follows. A link opens the doc section that owns the fact.

Help text sources, in order of preference:
1. A string a doc owns: a verb topic's `what` is the `What it does` cell of that verb's row in `clutch/docs/host-running.md`, read at build time with backticks removed. That table is already pinned to the CLI parser by `tests/unit/test_host_running.py`.
2. Otherwise, text written in `clutch/help.py` that links to the doc heading that owns the fact. `Before:` and `After:` text is always written there.

Link targets, deterministic per doc file (no fallback path):
- A doc shipped in the package (`clutch/docs/*.md`, found as `Path(clutch.__file__).parent / "docs"`) links to that installed file and the 0-based line of the target heading. A verb topic links to the line of its verb-table row.
- A doc not shipped in the package (`docs/how-clutch-works.md`) links to `<Repository URL>/blob/main/<repo path>#<GitHub heading slug>`. The Repository URL is a builder parameter. Its real value comes from the installed package metadata (the `Project-URL` named `Repository`) and is never typed as a literal in `clutch/help.py`.

## Scope in / Scope out
Scope in:
- New `clutch/help.py` holds the registry. It imports nothing from `clutch.observe` or `clutch.stats`, because `vscode-help-snapshot` makes both import it.
- A module-level `TOPICS` dict maps each topic key to its entry. The keys form one closed vocabulary with kind prefixes:
  - `view.<view id>` for each id in `vscode-clutchwork/package.json` `contributes.views.clutch` (`clutch.details`, `clutch.steps`, `clutch.tickets`, `clutch.box`, `clutch.stats`);
  - `command.<command id>` for non-verb commands only;
  - `verb.<verb>`;
  - `section.<section>` for `blocked`, `queued`, `running`, and `merged`;
  - `status.<reason>` for exactly these 14 reasons: `invalid`, `new`, `draft`, `held_change`, `held_operator`, `waits_on`, `not_eligible`, `interrupted`, `retry_pending`, `after`, `ready`, `running`, `merged`, `already_satisfied`;
  - `step.<step>` for each distinct value of `STEP_KINDS`;
  - `box.<message class>` for each `MessageClass` member;
  - `boxOutcome.<outcome>` for `pending`, `reopened`, `author`, `tombstone`, and `declined`;
  - `stat.<key>` for each top-level key of `project_stats`;
  - `lock.engine` and `lock.commit`;
  - `priority`.
- Each entry carries `before`, `after`, and a link target: a doc path plus heading, or for verbs, the verb row. Each non-verb entry also carries its `what`.
- A verb topic exists for each `engineVerbs` argv verb (`drain`, `serve`, `stop`, `kill`, `status`, `retro`) and for each verb a command maps to.
- A module-level `COMMANDS` map sends each command id now in `vscode-clutchwork/package.json` `contributes.commands` to its topic key.
  - A verb-backed command maps to its `verb.*` topic, for example `clutch.ticket.review` to `verb.review` and `clutch.ticket.priority` to `verb.order`.
  - Every other command has its own `command.*` topic.
- `topic_text(key)` returns `<what>\nBefore: <before>\nAfter: <after>` for a non-verb topic. It reads no doc, so `stats_tree` can call it in `vscode-help-snapshot`. `help_map` uses it for every non-verb topic.
- `help_map(read, repo_url)` returns `{key: {"what", "before", "after", "text", "link"}}` for every key in `TOPICS`.
  - `text` is exactly `<what>\nBefore: <before>\nAfter: <after>`.
  - `link` is `{"label", "path", "line"}` for a packaged doc and `{"label", "url"}` otherwise.
  - `read: Callable[[Path], str]` is called only for packaged docs under `Path(clutch.__file__).parent / "docs"`.
  - A `url` link is built from the heading text written in `clutch/help.py` and its computed GitHub slug, without reading that file.
  - A heading or verb row that does not resolve raises; the builder never returns a partial map.
- `help_pick(help)` takes a `help_map` result and returns the Help picker list.
  - For each topic kind, in kind order, one `{"kind": "separator", "label"}` comes first, then that kind's items as `{"label", "description", "detail", "topic"}`.
  - `label` is the key without its kind prefix, `description` is the link label, and `detail` is the `what`.
  - The list ends with one settings item `{"label", "detail", "command": "clutch.openSettings"}`, which has no `topic`.
- `tests/unit/test_help.py` passes a fake `read` that serves in-memory text holding every heading and verb row the registry links to, plus a fixed URL. It reads no file and no package metadata. Checks against the real docs, the real manifest, and installed metadata live in `tests/integration/test_help.py`.

Scope out:
- `clutch/observe.py`, `clutch/stats.py`, and their tests belong to `vscode-help-snapshot`.
- Every `vscode-clutchwork/` file belongs to `vscode-help-surfaces`. Docs and agent rules belong to `vscode-help-docs`.
- `clutch/docs/host-running.md`, `clutch/__main__.py`, and `docs/how-clutch-works.md` stay as they are. Shipping `docs/how-clutch-works.md` in the package stays out of scope.

## Scope fence
- clutch/help.py
- tests/unit/test_help.py
- tests/integration/test_help.py

## Acceptance criteria
1. `tests/unit/test_help.py::test_topic_shape`: every topic's `text` in the `help_map` result has exactly three lines.
   - Line 1 is the non-empty `what` and ends with `.`.
   - Line 2 starts with `Before: ` and line 3 starts with `After: `, each followed by non-empty text.
   - For every non-verb key, `topic_text(key)` equals that key's `text`.

   A topic missing `before` or `after`, or with an empty `what`, fails.
2. `tests/integration/test_help.py::test_links_resolve`: every link built with `Path.read_text` and the installed metadata Repository URL (`importlib.metadata`) resolves.
   - A `path` link names a file under the installed `clutch/docs`, and its `line` holds the named heading or, for a verb, that verb's table row.
   - A `url` link starts with the metadata Repository URL plus `/blob/main/`, names a repo file that exists, and has a fragment equal to the GitHub slug of a heading in that file.

   A link to a renamed or missing heading fails, as does a line number off by one.
3. `tests/unit/test_help.py::test_vocabularies_covered`: each of these has a key in `TOPICS`:
   - `section.` plus `blocked`, `queued`, `running`, and `merged`;
   - `status.` plus each of the 14 reasons in Scope in, and plus every state in `clutch.status.SETTLED`;
   - `step.` plus every value in `STEP_KINDS`;
   - `box.` plus every `MessageClass` member;
   - `boxOutcome.` plus `pending`, `reopened`, `author`, `tombstone`, and `declined`;
   - `stat.` plus every top-level key of `project_stats` run on an empty journal;
   - `lock.engine`, `lock.commit`, and `priority`;
   - `verb.` plus `drain`, `serve`, `stop`, `kill`, `status`, and `retro`.

   Adding a value to any of these vocabularies without a topic fails.
4. `tests/integration/test_help.py::test_manifest_covered` reads `vscode-clutchwork/package.json`.
   - Every `contributes.commands[].command` is a key of `COMMANDS`, and every mapped topic is in `TOPICS`.
   - Every `contributes.views.clutch[].id` has a `view.*` topic.

   A new command or view without help fails.
5. `tests/integration/test_help.py::test_verb_what_from_run_guide`: for every `verb.*` topic, `what` equals that verb's `What it does` cell in `clutch/docs/host-running.md` with backticks removed.
   - `tests/unit/test_help.py::test_verb_what_follows_run_guide` passes `help_map` in-memory run-guide text with the `review` cell rewritten, and asserts that `verb.review`'s `what` changes to match.
   - A separately typed string fails either test.
6. `tests/unit/test_help.py::test_unresolved_link_raises`: `help_map` raises in two cases. The first is in-memory doc text with a linked heading renamed. The second is run-guide text missing a verb row. Returning a map without the topic fails.
7. `tests/unit/test_help.py::test_help_pick_list`: `help_pick` returns one separator per topic kind, each before that kind's items.
   - Every non-separator item except the last carries a `topic` that is a `help_map` key.
   - The last item carries `"command": "clutch.openSettings"` and no `topic`.
8. `./dev.py test tests/unit/test_host_running.py` passes unchanged.
9. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/unit/test_host_running.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `clutch/help.py` contains the GitHub repository URL as a literal, or copies a verb's `What it does` text instead of reading it from `clutch/docs/host-running.md`;
- a link built by `clutch/help.py` falls back from a local path to a URL, or the reverse, for the same doc;
- `clutch/help.py` imports `clutch.observe` or `clutch.stats`;
- any file outside the Scope fence changes.

## Time budget
- expected: 45m
- stuck: 90m
