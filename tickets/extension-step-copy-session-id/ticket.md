---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- extension-copy-merged-stem

## Runs before
- extension-merged-hover-commit

## Context
- clutch/providers.py::CliAdapter.invoke
- clutch/evidence/schema.py
- clutch/evidence/store.py::EvidenceStore.write_record
- clutch/observe.py::live_call
- clutch/observe.py::recent_steps
- clutch/observe.py::MENU
- clutch/observe.py::ticket_menu_inputs
- vscode-clutchwork/media/view.js
- tests/integration/test_menu_verb_parity.py
- clutch/help.py
- vscode-clutchwork/extension.js
- tests/unit/test_live_call.py
- tests/unit/test_evidence_schema.py
- docs/how-clutch-works.md#10.4 Evidence records

## On-demand
- vscode-clutchwork/package.json

## Goal / Why
To look at the model session behind a step, the owner has to dig the Claude session id or Codex thread id out of evidence files, and while the call is still running clutch doesn't save it anywhere. After this ticket, right-clicking a Recent Steps row whose stage made a model call shows "Copy Session ID", which copies that call's Claude `session_id` or Codex `thread_id` to the clipboard. The owner can then find the session in the provider's own extension. Right-clicking a running row in the Tickets view shows the same item, for that ticket's current model call. Both work while the call is still running.

## Boundary contract
### Evidence start record native ids
- disposition: extend
- owner: clutch/evidence/schema.py::Start and clutch/providers.py::CliAdapter.invoke
- consumers: clutch/observe.py step sessions
- observable change: `Start` gains optional `native_ids: NativeIds | None = None`. During a captured call, the first stdout line that is a JSON object with a string `session_id` or `thread_id` makes `invoke` republish `start.json` once through `EvidenceStore.write_record` with `native_ids` set; later lines never rewrite it
- compatibility: start records without `native_ids` stay valid; `end.json` and its `native_ids` are unchanged; record kinds stay `start` and `end`; a line that is not JSON or holds no id is ignored
- acceptance: criterion 1
- tests: tests/unit/test_provider_live_native_ids.py
- post-merge source of truth: clutch/evidence/schema.py

### Snapshot step session
- disposition: extend
- owner: clutch/observe.py
- consumers: vscode-clutchwork/extension.js Recent Steps tree
- observable change: a snapshot step with a stem, surface, attempt and run_seq gains `session: {"provider": <name>, "id": <session_id or thread_id>}` and `contextValue: "session"` when the newest evidence start record whose `stem`, `surface`, `attempt` and `run_seq` match the step has `native_ids` with an id; otherwise the step has neither key
- compatibility: existing step keys are unchanged
- acceptance: criterion 2
- tests: tests/unit/test_observe_step_session.py
- post-merge source of truth: clutch/observe.py

### Running ticket row session
- disposition: extend
- owner: clutch/observe.py::MENU and clutch/observe.py::snapshot
- consumers: vscode-clutchwork/media/view.js row context and package.json `webview/context`
- observable change: a running ticket row gains `sessionId`, the session or thread id from the newest start record with `native_ids` under `llm/<stem>/` that has no `end.json` (the same open-call rule as `live_call`), or no key when none; new extension-only menu entry `clutchCopySession` with input `session`, admitted only when the row has `sessionId`, command `clutch.ticket.copySession`
- compatibility: existing row keys, menu keys and admissions are unchanged
- acceptance: criterion 4
- tests: tests/unit/test_observe_step_session.py and tests/integration/test_menu_verb_parity.py
- post-merge source of truth: clutch/observe.py

### Extension command and help
- disposition: extend
- owner: vscode-clutchwork/package.json and clutch/help.py
- consumers: VS Code users of the Recent Steps view
- observable change: command `clutch.steps.copySession` titled `Copy Session ID` in `view/item/context` when `view == clutch.steps && viewItem == session`, and command `clutch.ticket.copySession` titled `Copy Session ID` in the Tickets `webview/context` (group `1_open@3`) when `clutchCopySession == 'on'`; both hidden from the command palette, each with a help entry; they write the id with `vscode.env.clipboard.writeText`
- compatibility: existing commands, menus and the double-click open behavior are unchanged
- acceptance: criterion 3
- tests: tests/integration/test_help.py
- post-merge source of truth: vscode-clutchwork/package.json and clutch/help.py

## Scope in / Scope out
Scope in:
- clutch/evidence/schema.py: add `native_ids: NativeIds | None = None` to `Start`.
- clutch/providers.py `invoke`: keep the start record data in a local; in `stdout_line`, while `capture` is set, the start record was written and no id was saved yet, parse the line as JSON and on the first string `session_id` or `thread_id` call `store.write_record(key, "start", {**start_data, "native_ids": {"session_id": ..., "thread_id": ...}})`; ignore lines that do not parse.
- clutch/observe.py: one function beside `live_call` that, given the evidence dir and a step's stem, surface, attempt and run_seq, returns `{"provider", "id"}` from the newest matching start record with `native_ids`, or None. In `snapshot`, read `surface`, `attempt` and `run_seq` before they are popped, and set `session` and `contextValue` as in the boundary contract.
- vscode-clutchwork/extension.js: in `StepsTree.getTreeItem` set `item.contextValue = step.contextValue`; register `clutch.steps.copySession` as `step => vscode.env.clipboard.writeText(step.session.id)`.
- clutch/observe.py running rows: add `session=False` to the menu input defaults in `ticket_menu_inputs`, set `values["session"] = "sessionId" in r` in the snapshot's per-row loop beside `section`, set `sessionId` on running rows as in the boundary contract (reuse the open-call lookup `live_call` uses rather than a second evidence walk), and add `"clutchCopySession": MenuEntry("ticket", lambda session: Admission("admit" if session else "noop"), ("session",), extension_only=True, command="clutch.ticket.copySession")` to `MENU`.
- vscode-clutchwork/media/view.js: add `clutchSessionId: r.sessionId` to the row's context object; register `clutch.ticket.copySession` in extension.js as `ctx => vscode.env.clipboard.writeText(ctx.clutchSessionId)`.
- tests/integration/test_menu_verb_parity.py: add `"clutchCopySession"` to the expected extension-only set; nothing else changes there.
- vscode-clutchwork/package.json: add both commands, the `view/item/context` and `webview/context` entries, and a `commandPalette` entry with `"when": "false"` for each.
- clutch/help.py: add `"clutch.steps.copySession": "Copy the model session id of the selected step."` and `"clutch.ticket.copySession": "Copy the model session id of the running ticket."` to the extension command descriptions.
- docs/how-clutch-works.md section 10.4: add one sentence saying `start.json` is republished once with `native_ids` when the stream first reports a session or thread id.
- New tests/unit/test_provider_live_native_ids.py drives `invoke` with a fake exec seam that feeds `on_stdout_line` a non-JSON line, a Claude-style `{"session_id": "s1"}` line and a later `{"session_id": "s2"}` line, and reads `start.json` under `tmp_path` before the fake process returns.
- New tests/unit/test_observe_step_session.py writes start records under `tmp_path`.
Scope out:
- Opening sessions in the Claude or Codex extensions, copying provider transcripts, `end.json`, normalizers, and session ids on non-running ticket rows.

## Scope fence
- clutch/evidence/schema.py
- clutch/providers.py
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/media/view.js
- vscode-clutchwork/package.json
- docs/how-clutch-works.md
- tests/integration/test_menu_verb_parity.py
- tests/unit/test_provider_live_native_ids.py
- tests/unit/test_observe_step_session.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_provider_live_native_ids.py` proves `start.json` read mid-call holds `native_ids.session_id == "s1"` after the first id line (not `None`, and not `"s2"` after the later line), and a call whose stream has no id leaves `start.json` without `native_ids`.
2. `./dev.py test tests/unit/test_observe_step_session.py` proves a step matching a start record with `native_ids.thread_id == "t1"` and provider `codex` gets `session == {"provider": "codex", "id": "t1"}` and `contextValue == "session"`, while a step whose newest matching record has no `native_ids`, and a step with no matching record, have neither key.
3. `./dev.py test tests/integration/test_help.py tests/unit/test_help.py tests/integration/test_extension_argv.py tests/unit/test_evidence_schema.py tests/unit/test_live_call.py` passes with `clutch.steps.copySession` and `clutch.ticket.copySession` in package.json and `COMMANDS` and the extended `Start` schema.
4. `./dev.py test tests/unit/test_observe_step_session.py tests/integration/test_menu_verb_parity.py` proves a running row with an open start record holding `native_ids.session_id == "s1"` gets `sessionId == "s1"` and `menu["clutchCopySession"] == "on"`, a running row whose only matching record has `end.json` gets no `sessionId` and `"off"`, and the extension-only set is exactly `{"clutchAskDiagnose", "clutchAskReview", "clutchAskDrafts", "clutchCopyStem", "clutchCopySession"}`.

## Verification
```
./dev.py test tests/unit/test_provider_live_native_ids.py tests/unit/test_observe_step_session.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_extension_argv.py tests/unit/test_evidence_schema.py tests/unit/test_evidence_store.py tests/unit/test_evidence_envelope.py tests/integration/test_evidence_envelope.py tests/unit/test_live_call.py tests/unit/test_help_snapshot.py tests/integration/test_menu_verb_parity.py
```

## Definition of rejected
JavaScript reads evidence files or picks which steps have a session, a new evidence record kind is added, the provider CLI argv changes, or files outside the fence change.

## Time budget
- expected: 25m
- stuck: 50m
