---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- vscode-help-catalog

## Context
- chupa/observe.py::snapshot
- chupa/observe.py::recent_steps
- chupa/observe.py::STEP_KINDS
- chupa/observe.py::MENU
- chupa/observe.py::MenuEntry
- chupa/observe.py::row_menu
- chupa/stats.py::stats_tree
- chupa/stats.py::project_stats
- chupa/status.py::SETTLED
- chupa/box.py::MessageClass
- tests/integration/test_stats.py::test_stats_tree_generic_rows
- tests/integration/test_step_icons.py
- tests/integration/test_vscode_command_not_found.py
- tests/regress_vscode_task_identity.py
- vscode-chupa/package.json

## On-demand
- tests/integration/test_watch.py
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py

## Goal / Why
`vscode-help-catalog` adds the help registry `chupa/help.py`:
- `TOPICS`, the closed topic-key vocabulary;
- `COMMANDS`, the command-to-topic map;
- `topic_text(key)` for non-verb topics;
- `help_map(read, repo_url)`;
- `help_pick(help)`.

Nothing feeds that registry to the extension yet. The Engine... picker still shows `detail` strings hand-copied into `chupa/observe.py::snapshot`, which will drift from the run guide.

This ticket delivers the registry through the snapshot and `stats --tree` output. Rows, steps, box rows, header counts, and Stats rows then carry help keys or text, and the hand-copied `engineVerbs` strings are gone. The extension surfaces that draw this help are `vscode-help-surfaces`.

`COMMANDS` is keyed by VS Code command id (`chupa.ticket.run`), while `row_menu` emits `MENU` keys (`chupaRun`). Nothing in merged code joins the two, so this ticket gives each `MenuEntry` its command id rather than deriving one from the key's spelling.

## Scope in / Scope out
Scope in:
- `chupa/observe.py` gains one module-level function, `help_payload()`. It is the only place that calls `chupa.help.help_map` with `Path.read_text` and the `importlib.metadata` `Repository` Project-URL. It returns the `help` map and the `helpPick` list (`help_pick` of that map). `snapshot` itself reads no doc and no metadata.
- `chupa/observe.py::MenuEntry` gains one field, `command: str`, declared last: the VS Code command id that runs that action. Every entry in `MENU` names it:
  - `chupaReview` is `chupa.ticket.review`, `chupaLint` is `chupa.ticket.lint`, `chupaRun` is `chupa.ticket.run`, `chupaConfirm` is `chupa.ticket.confirm`, `chupaReject` is `chupa.ticket.reject`;
  - `chupaAskDiagnose` is `chupa.ticket.askDiagnose`, `chupaAskDrafts` is `chupa.ticket.askDrafts`, `chupaAskReview` is `chupa.ticket.askReview`;
  - `chupaPriority` is `chupa.ticket.priority`, `chupaRunsBefore` is `chupa.ticket.runsBefore`;
  - `chupaTriage` is `chupa.box.triage`, `chupaDismiss` is `chupa.box.dismiss`.

  `chupaRun`, `chupaTriage`, and `chupaDismiss` pass `needs_lock` as a keyword so the new field is unambiguous. No other `MenuEntry` field and no admission changes. No test constructs a `MenuEntry`, and `tests/integration/test_menu_verb_parity.py` reads only `kind`, `extension_only`, and `admission`, so it stays as it is and out of the fence.
- `chupa/observe.py` gains a module-level `STATUS_KEYS` tuple, the closed status-key vocabulary. Its members are `invalid`, `new`, `draft`, `held_change`, `held_operator`, `waits_on`, `not_eligible`, `interrupted`, `retry_pending`, `after`, `ready`, `running`, `merged`, and `already_satisfied`.
- Each status branch in `snapshot` names its `status.*` key next to the text it builds; `snapshot` never parses status text. The branches and their keys are:
  - `why_blocked`: new is `status.new`, frontmatter state is `status.draft`, held until change is `status.held_change`, both reject-queue holds are `status.held_operator`, waits on is `status.waits_on`, and not eligible is `status.not_eligible`;
  - an invalid row is `status.invalid`;
  - `why_queued`: `status.interrupted`, `status.retry_pending`, `status.after`, and `status.ready`;
  - a running row is `status.running`;
  - a merged-section row is `status.<settled state>`.
- `snapshot` adds these top-level fields:
  - `help` and `helpPick`, from `help_payload()`;
  - `headerHelp`, the topic keys for each Tickets header count (`section.*`) and each lock indicator (`lock.engine`, `lock.commit`);
  - `boxHeaderHelp`, the `boxOutcome.*` topic key for each `boxCounts` key.
- Snapshot items carry topic keys:
  - each ticket row carries `help: {"section": key, "status": key}`, and `priorityHelp: "priority"` when its `priorityTag` is non-empty;
  - each ticket row carries `next`, the help keys of its menu actions that are `on`, in `MENU` order. Each key comes from `chupa.help.COMMANDS[MENU[key].command]`; no code derives a command id from a menu key's spelling;
  - each box row carries `help: {"class": "box.<messageClass>", "outcome": "boxOutcome.<outcome>"}`;
  - each step carries `help`, its `step.<STEP_KINDS[kind]>` key, so start, ok, and failed share one topic;
  - each step carries `tooltip`, the full text that Python builds from `dateDisplay`, stem, step text, and the topic's `text`.
- In `engineVerbs`, each `detail` becomes the `what` of the `verb.<argv[0]>` topic in the `help` map. This removes the hand-copied strings.
- `chupa/stats.py::stats_tree` gives each top-level row whose key has a `stat.<key>` topic in `chupa.help.TOPICS` a `tooltip` equal to `chupa.help.topic_text(f"stat.{key}")`. Rows without a topic and all child rows do not change. `stats_tree` reads no doc.
- `tests/integration/test_watch.py` changes one expectation: `engineVerbs[0]` `detail` equals the `drain` row's `What it does` cell from `chupa/docs/host-running.md` with backticks removed, not the old literal. It also gains the assertions in criterion 3.
- In `tests/unit/test_menu_admission.py`, both fixtures that fake `Path.read_text` with a dict of ticket paths monkeypatch `observe.help_payload` to return a fixed in-memory payload, as they already fake `observe.journal` and `observe.load_tickets`. The `world` fixture in `tests/unit/test_verdict_menu_parity.py` does the same. Their assertions do not change, and they still read no disk.
- New `tests/unit/test_help_snapshot.py` holds criteria 1 and 2.

Scope out:
- `chupa/help.py` and its tests stay as `vscode-help-catalog` leaves them.
- Every `vscode-chupa/` file belongs to `vscode-help-surfaces`. Docs and agent rules belong to `vscode-help-docs`.
- `chupa/docs/host-running.md`, `chupa/__main__.py`, and `chupa/stats.py::project_stats` stay as they are.

## Scope fence
- chupa/observe.py
- chupa/stats.py
- tests/unit/test_help_snapshot.py
- tests/integration/test_watch.py
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py

## Acceptance criteria
1. `tests/unit/test_help_snapshot.py::test_status_keys_covered` checks three things:
   - `STATUS_KEYS` equals the 14 keys in Scope in;
   - every `status.<k>` for `k` in `STATUS_KEYS` is a key of `chupa.help.TOPICS`;
   - every state in `chupa.status.SETTLED` is in `STATUS_KEYS`.

   Adding a status key without a topic fails.
2. `tests/unit/test_help_snapshot.py::test_stats_tree_tooltips`: `stats_tree` of `project_stats` on an empty journal gives every top-level row a `tooltip` equal to `chupa.help.topic_text` of its `stat.*` key, and no child row has a `tooltip` key. A missing or mismatched tooltip fails.
3. `./dev.py test tests/integration/test_watch.py` passes with the existing snapshot fixture.
   - `snap["engineVerbs"][0]["detail"]` equals the `drain` row's `What it does` cell with backticks removed, not `"Run every eligible ticket to quiescence, then exit."`.
   - Every `engineVerbs` `detail` equals `snap["help"]["verb." + argv[0]]["what"]`.
   - Every `MENU` entry's `command` is a key of `chupa.help.COMMANDS` and is one of the `contributes.commands[].command` values in `vscode-chupa/package.json`. A menu entry whose command id is misspelled or undeclared fails.
   - For every row, `next` equals `[COMMANDS[MENU[key].command] for key, value in row["menu"].items() if value == "on"]` in `MENU` order, and at least one fixture row has one menu action `on` and another `off`, so the assertion is not vacuous. A `next` that lists an `off` action, drops an `on` one, or reorders them fails.
   - Every row's `help.section` and `help.status` and every key in its `next` are keys of `snap["help"]`. `help.section` is `section.<row section>`, and a `merged` section row's `help.status` is `status.merged` or `status.already_satisfied`.
   - Every step's `help` is a key of `snap["help"]`, and its `tooltip` contains that topic's `text`.
   - Every `headerHelp` and `boxHeaderHelp` value is a key of `snap["help"]`.
   - Every non-separator `helpPick` item carries either a `topic` that is a key of `snap["help"]`, or a `command`, which only the settings item carries.

   A row, step, or header that names a key missing from the map fails.
4. `./dev.py test tests/integration/test_stats.py` passes unchanged, including `test_stats_tree_generic_rows`.
5. `./dev.py test tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py` passes. The assertions are unchanged, and no disk read happens for docs or metadata.
6. `./dev.py test tests/integration/test_menu_verb_parity.py tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py` passes unchanged. `uv run python tests/regress_vscode_task_identity.py` prints `{"regression_result": "pass"}` and exits 0, so the snapshot changes break no extension harness.
7. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_help_snapshot.py tests/integration/test_watch.py tests/integration/test_stats.py
./dev.py test tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py
./dev.py test tests/integration/test_menu_verb_parity.py tests/integration/test_step_icons.py tests/integration/test_vscode_command_not_found.py
uv run python tests/regress_vscode_task_identity.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `snapshot` reads a doc or package metadata other than through `help_payload()`;
- `snapshot` derives a status key by parsing status text;
- a `next` key is derived from a menu key's spelling instead of that entry's `command`;
- `engineVerbs` still carries a hand-written `detail` string;
- `stats_tree` reads a doc or package metadata;
- `chupa/help.py`, any file under `vscode-chupa/`, `chupa/docs/host-running.md`, `chupa/__main__.py`, or `project_stats` changes.

## Time budget
- expected: 55m
- stuck: 90m
