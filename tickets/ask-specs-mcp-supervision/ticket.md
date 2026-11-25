---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- mcp-control-and-tickets

## Context
- docs/antigravity-plan.md#5. Supervising
- clutch/ask.py
- clutch/mcp.py::TOOLS
- docs/how-clutch-works.md#7.5 Roadmap operation
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_plan_handoff.py
- tests/integration/test_ask_plan_subagent_models.py
- tests/integration/test_ask_plan_priority_order.py
- tests/integration/test_ask_plan_read_queue.py
- tests/integration/test_ask_plan_conduct_covered.py
- tests/integration/test_ask_plan_shared_paths.py
- tests/integration/test_ask_depends_rule.py
- tests/integration/test_ask_view_events.py
- tests/integration/test_box_triage_inbox.py

## On-demand
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md

## Goal / Why
Roadmap row 224 (`ask-specs-mcp-supervision`, `docs/antigravity-plan.md` §5, plus 2026-11-25 owner decisions on Antigravity subagent models and Suggestion Box triage cadence). Today's shipped supervising prompts (`clutch/specs/ask/drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md`) still assume Claude Code primitives: `drain-loop.md` starts with a literal `/loop ` prefix, all three prompts shell out to `clutch` CLI verbs even when `clutch_*` MCP tools exist, all three assume a line-by-line streaming `Monitor` tool with no cursor-based one-shot wait path, `plan-ticket-serve.md` runs `clutch engine serve` under an agent background-process facility instead of detached, none specify Antigravity `invoke_subagent` model routing, and `drain-loop.md` runs Suggestion Box triage on every tick instead of once at the end of a phase right before the release gate.

After this ticket:
- `clutch/specs/ask/drain-loop.md` drops the leading `/loop ` prefix so MCP prompts and Antigravity skills invoke it cleanly while Claude Code users can still pass it to `/loop`.
- `drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md` prefer `clutch_*` MCP tools (`clutch_status`, `clutch_snapshot`, `clutch_roadmap_status`, `clutch_prompt`, `clutch_ticket_new`, `clutch_ticket_lint`, `clutch_ticket_order`, `clutch_ticket_confirm`, `clutch_ticket_reject`, `clutch_box_suggest`, `clutch_box_triage`, `clutch_box_dismiss`, `clutch_engine_start`, `clutch_engine_control`, and `clutch_evidence_captures`) when MCP is present, keep CLI commands as fallback when MCP is absent, and keep CLI mandatory for `clutch host doctor`, `clutch provider probe`, `clutch ticket review`, the host test suite, and `clutch roadmap gate <release>`.
- All three prompts specify dual-mode event waiting between ticks: either `clutch_wait_event(cursor=..., timeout_seconds=300)` / `clutch view events --once --cursor ... --timeout 300` (with zero missed events between turns) or a streaming monitor facility on `clutch view events` when the host provides one, never a timer polling loop.
- `plan-ticket-serve.md` supervises a detached `serve` daemon (`clutch_engine_start(mode="serve")` / `clutch engine serve --detach`, stopping cleanly via `clutch_engine_control(action="stop")` / `clutch engine stop` for no-engine steps and shutdown).
- `plan-ticket-drain.md` and `plan-ticket-serve.md` retain the Claude `Sonnet`-not-`Opus` and cross-family calibration rules and add explicit Antigravity `invoke_subagent` routing (owner decision 2026-11-25): use `Model: "inherit"` (or `"pro"` / strong model, never `"flash"`) for row authors (`clutch prompt author <stem>`) and phase-closing reviews; use `Model: "flash"` only for running `clutch roadmap gate <release>`.
- All three prompts and `docs/how-clutch-works.md` section 7.5 apply the owner decision (2026-11-25) on Suggestion Box triage cadence: do not run Suggestion Box triage on every tick; run it once at the end of a phase right before the release gate (unless the owner explicitly asks otherwise).

Rejected simpler approach: forking separate Antigravity-only prompt templates under `clutch/specs/ask/`. That violates `AGENTS.md` (*"Keep shipped process prompts in sync"* and *"One authoring process"*), creates duplicate prompt maintenance, and lets Claude Code and Antigravity supervision rules drift apart.

## Boundary contract

### Shipped supervising operator prompt specs
- disposition: extend
- owner: clutch/specs/ask/drain-loop.md, clutch/specs/ask/plan-ticket-drain.md, clutch/specs/ask/plan-ticket-serve.md
- consumers: `clutch/ask.py`, `clutch/mcp.py` (`prompts/get`, `clutch_prompt`), `clutch/__main__.py` (`prompt`), Claude Code and Antigravity supervising sessions, future `host-antigravity-plugin`
- observable change: removes the leading `/loop ` prefix from `drain-loop.md`; adds MCP-first `clutch_*` tool guidance with CLI fallback and mandatory CLI boundaries (`host doctor`, `provider probe`, host test suite, `roadmap gate`); adds dual-mode event waiting (`clutch_wait_event` / `clutch view events --once --cursor ... --timeout 300` with zero missed events, or streaming monitor on `clutch view events`); switches `plan-ticket-serve.md` from a session-tied background-process `serve` to detached `clutch_engine_start(mode="serve")` / `clutch engine serve --detach` and `clutch_engine_control(action="stop")`; adds Antigravity `invoke_subagent` model routing (`inherit`/`pro` for row authors and phase-closing reviews, `flash` only for `clutch roadmap gate`); and changes Suggestion Box triage cadence from every tick to once at the end of a phase right before the release gate (unless the owner explicitly asks otherwise).
- compatibility: `ask.KINDS`, `ask.TAKES`, `ask.render` placeholder substitution (`${state_dir}`), all CLI fallback verbs, Claude `Sonnet`-not-`Opus` and cross-family calibration rules, priority ordering, queue-reading rules, conduct-check rules, shared-paths exemption, `Depends on` commit rules, and `plan-ticket-drain`/`plan-ticket-serve` handoff parity remain intact; `tests/integration/test_ask_drain_loop.py`, `tests/integration/test_ask_drain_loop_agent.py`, and `tests/integration/test_ask_plan_serve.py` update their assertions for the dropped `/loop ` prefix, phase-end Suggestion Box cadence, and detached `serve`.
- acceptance: criteria 1, 2, 3, 4, 5, 6, and 7
- tests: tests/integration/test_ask_mcp_supervision.py, tests/integration/test_ask_drain_loop.py, tests/integration/test_ask_drain_loop_agent.py, tests/integration/test_ask_plan_serve.py, tests/integration/test_ask_plan_drain.py, tests/integration/test_ask_plan_handoff.py, tests/integration/test_ask_plan_subagent_models.py, tests/integration/test_ask_plan_priority_order.py, tests/integration/test_ask_plan_read_queue.py, tests/integration/test_ask_plan_conduct_covered.py, tests/integration/test_ask_plan_shared_paths.py, tests/integration/test_ask_depends_rule.py, tests/integration/test_ask_view_events.py, tests/integration/test_box_triage_inbox.py
- post-merge source of truth: clutch/specs/ask/drain-loop.md, clutch/specs/ask/plan-ticket-drain.md, clutch/specs/ask/plan-ticket-serve.md

### Roadmap operation documentation
- disposition: extend
- owner: docs/how-clutch-works.md
- consumers: operators and contributors reading section 7.5
- observable change: updates section 7.5 (`### 7.5 Roadmap operation`) to reflect MCP-first supervising tool usage and phase-end Suggestion Box triage cadence (once at the end of a phase right before the release gate unless the owner explicitly asks otherwise) instead of per-tick triage.
- compatibility: all other sections of `docs/how-clutch-works.md` (including section 2.1 verb tables edited by `mcp-control-and-tickets`) remain unchanged.
- acceptance: criterion 7
- tests: tests/integration/test_ask_mcp_supervision.py, tests/integration/test_ask_plan_drain.py, tests/integration/test_ask_plan_serve.py
- post-merge source of truth: docs/how-clutch-works.md

## Scope in / Scope out
In:
- `clutch/specs/ask/drain-loop.md`:
  - Remove the leading `/loop ` prefix so line 1 starts directly with `You are the supervising agent loop for the clutch engine.`.
  - Add MCP-first tool guidance: when `clutch_*` MCP tools are present in the session, prefer `clutch_status`, `clutch_snapshot`, `clutch_roadmap_status`, `clutch_prompt`, `clutch_ticket_lint`, `clutch_ticket_confirm`, `clutch_ticket_reject`, `clutch_box_suggest`, `clutch_box_triage`, `clutch_box_dismiss`, `clutch_engine_start`, and `clutch_engine_control` (model-visible `clutch_ticket_confirm` and `clutch_ticket_reject` always record `actor: operator`); keep the CLI verbs as fallback when MCP is absent, and keep CLI mandatory for `clutch host doctor`, `clutch provider probe`, `clutch ticket review`, the host test suite, and `clutch roadmap gate`.
  - Update event waiting between ticks to dual-mode: either call `clutch_wait_event(cursor=..., timeout_seconds=300)` (or run `clutch view events --once --cursor ... --timeout 300` as a background command) to wake reactively with zero missed events between ticks, or run `clutch view events` under your agent's monitor facility and start the next tick on each line it prints.
  - Update Suggestion Box triage cadence (step 4, Done check, and Hard limits) per the 2026-11-25 owner decision: do not run `clutch box triage` / `clutch_box_triage` on every tick; run Suggestion Box triage once at the end of a phase right before the release gate (unless the owner explicitly asks otherwise). Keep the existing rules that `roadmap_row` is never triaged or dismissed (`clutch roadmap author` owns it), `clutch box triage` queues through the engine inbox (keeping `"clutch box triage"` and `"inbox"` on the same line), `clutch box dismiss` runs only between drains (keeping `"clutch box dismiss"` and `"between drains"` on the same line), triage's verdict is final and never re-filed, and drafts written by triage are released through `clutch prompt drafts` the tick they appear.
  - Preserve all existing phrases required by `test_ask_drain_loop_agent.py`, `test_ask_plan_priority_order.py`, `test_ask_plan_read_queue.py`, `test_ask_depends_rule.py`, `test_ask_view_events.py`, `test_box_triage_inbox.py`, and `test_ask_plan_drain.py` (including no session facts and never writing the forbidden word `gemini` or any non-existent `clutch <group> <verb>` command in backticks).
- `clutch/specs/ask/plan-ticket-drain.md`:
  - Add MCP-first tool guidance in `Delegation:` / `Supervising:` naming `clutch_status`, `clutch_snapshot`, `clutch_roadmap_status`, `clutch_prompt`, `clutch_ticket_new`, `clutch_ticket_lint`, `clutch_ticket_order`, `clutch_ticket_confirm`, `clutch_ticket_reject`, `clutch_box_suggest`, `clutch_box_triage`, `clutch_box_dismiss`, `clutch_engine_start`, `clutch_engine_control`, and `clutch_evidence_captures` when MCP is present, keeping CLI as fallback when MCP is absent and mandatory for `clutch host doctor`, `clutch provider probe`, `clutch ticket review`, the host test suite, and `clutch roadmap gate <release>`.
  - In `Delegation:`, keep every existing Claude `Sonnet`-not-`Opus` and cross-family calibration requirement verbatim, and add Antigravity `invoke_subagent` model routing (owner decision 2026-11-25): use `Model: "inherit"` (or `"pro"` / strong model, never `"flash"`) for row authors (`clutch prompt author <stem>`) and phase-closing reviews; use `Model: "flash"` only for running `clutch roadmap gate <release>`. Refer to the host as `Antigravity` (never `gemini`).
  - In `Supervising:`, update event waiting to dual-mode: either call `clutch_wait_event(cursor=..., timeout_seconds=300)` (or run `clutch view events --once --cursor ... --timeout 300` as a background command) alongside any running authoring subagents—waking immediately with zero missed events when either an engine event or a subagent finishes—or `Arm \`clutch view events\` under your agent's monitor facility once with the longest timeout the facility allows, act on each line it prints, and re-arm only when it expires; never write a loop that polls \`clutch view status\`, \`clutch prompt drafts\`, or a process list on a timer.` immediately followed by ` Start new authoring...`. Keep this exact wording identical to `plan-ticket-serve.md`.
  - In `Supervising:` and `Closing each phase:`, record the 2026-11-25 owner decision on Suggestion Box triage cadence: do not run `clutch box triage` / `clutch_box_triage` on every tick; in `Closing each phase:` (on the `- Once the queue has drained` bullet line, identical to `plan-ticket-serve.md`), run Suggestion Box triage once for pending non-`roadmap_row` messages right before running `clutch roadmap gate <release>` (unless the owner explicitly asks otherwise), then run `clutch roadmap gate <release>` through one Sonnet subagent once per release (on Antigravity, use `Model: "flash"`).
- `clutch/specs/ask/plan-ticket-serve.md`:
  - Apply the exact same MCP-first tool guidance, Antigravity `invoke_subagent` model routing, dual-mode event waiting, and phase-end Suggestion Box triage cadence as `plan-ticket-drain.md` (keeping the `- Keep a log...`, `- Once the queue has drained...`, and `Arm \`clutch view events\`... Start new authoring` segments identical to `plan-ticket-drain.md` so `test_ask_plan_handoff.py::test_shared_session_rules_match` passes).
  - Switch `serve` lifecycle from a session-tied background-process facility to detached supervision: start and restart only with `clutch_engine_start(mode="serve")` or `clutch engine serve --detach` (removing `"background-process facility"`), monitor via `clutch_wait_event` / `clutch view events`, `clutch_evidence_captures`, and `${state_dir}/engine.log`, and stop cleanly with `clutch_engine_control(action="stop")` or `clutch engine stop` before no-engine steps (Reject-queue edits, `clutch box dismiss` / `clutch_box_dismiss`, `clutch host doctor`) and when the run finishes idle. Keep `"drain.out"` and `"clutch engine drain"` absent from `plan-ticket-serve.md`.
- `docs/how-clutch-works.md`:
  - Update only the supervising-loop paragraph in section 7.5 (`### 7.5 Roadmap operation`) to state that the supervising loop prefers `clutch_*` MCP tools when present (with CLI fallback) and runs Suggestion Box triage once at the end of a phase right before the release gate (unless the owner explicitly asks otherwise) rather than on every tick. Nothing else in `docs/how-clutch-works.md` changes.
- `tests/integration/test_ask_drain_loop.py`:
  - Update `test_drain_loop_renders_state_dir_and_loop_prefix` and `test_prompt_verb_drain_loop_prints_without_state` to assert `drain-loop` does NOT start with `/loop` and starts with `You are the supervising agent loop`.
- `tests/integration/test_ask_drain_loop_agent.py`:
  - Update `test_prompt_bounds_box_triage` to assert phase-end Suggestion Box triage cadence (once at the end of a phase right before the release gate unless the owner explicitly asks otherwise, not on every tick) instead of `"pending when the tick starts"` and `"at most once per tick"`. Nothing else in `tests/integration/test_ask_drain_loop_agent.py` changes.
- `tests/integration/test_ask_plan_serve.py`:
  - Update the two flipped phrases in `test_serve_prompt_and_docs` (`"only with \`clutch engine serve\`"` and `"background-process facility"`) to assert detached `serve` (`clutch engine serve --detach`, `clutch_engine_start(mode="serve")`, `clutch_engine_control(action="stop")`, and `"background-process facility" not in serve`). Keep all other assertions including `"drain.out" not in serve` and `"clutch engine drain" not in serve`.
- New integration test file `tests/integration/test_ask_mcp_supervision.py` (reads repo `clutch/specs/ask/*.md` via `ask.render` with `SimpleNamespace(state_dir=Path("/repo/.clutch"), ask_notes=None)` and `Path("/repo")`, zero disk writes and zero subprocesses): verifies all new behaviors in criteria 1-7 and asserts every `clutch_*` MCP tool name referenced in the three prompt specs is registered in `clutch.mcp.TOOLS`.
- Engine-written `# clutch:meta` header lines on newly created files under `tests/` updated by Check's meta step.

Out:
- `clutch/ask.py`, `clutch/mcp.py`, `clutch/__main__.py`, `clutch/docs/host-running.md`, `README.md`, `docs/roadmap.md`, `docs/antigravity-plan.md`, and `clutch/specs/ask/*.md` other than `drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md`.
- `clutch/antigravity.py` and Antigravity plugin/skill installation (deferred to `host-antigravity-plugin`).
- `clutch/ui/dashboard.html` and MCP App dashboard tools (deferred to `mcp-app-dashboard`).
- Any edits to the seven hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`).

## Scope fence
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/plan-ticket-serve.md
- docs/how-clutch-works.md
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_mcp_supervision.py

## Acceptance criteria
1. `clutch/specs/ask/drain-loop.md` does not start with `/loop` (starts with `You are the supervising agent loop`, ruling out a retained `/loop ` prefix) while preserving `${state_dir}` substitution and write-free `clutch prompt drain-loop` rendering. Verified by `./dev.py test tests/integration/test_ask_drain_loop.py tests/integration/test_ask_mcp_supervision.py`.
2. `drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md` instruct preferring `clutch_*` MCP tools (`clutch_status`, `clutch_snapshot`, `clutch_roadmap_status`, `clutch_prompt`, `clutch_ticket_confirm`, `clutch_ticket_reject`, `clutch_box_suggest`, `clutch_box_triage`, `clutch_box_dismiss`, `clutch_engine_start`, `clutch_engine_control`) when MCP is present, keeping CLI fallback when MCP is absent, and keeping CLI mandatory for `clutch host doctor`, `clutch provider probe`, the host test suite, and `clutch roadmap gate`; every concrete `clutch_*` tool name in all three prompts is a real key in `clutch.mcp.TOOLS` (ruling out typos or unimplemented tool names). Verified by `./dev.py test tests/integration/test_ask_mcp_supervision.py`.
3. `drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md` specify dual-mode event waiting: `clutch_wait_event` / `clutch view events --once --cursor ... --timeout 300` with zero missed events between turns OR a streaming monitor facility on `clutch view events`, never a timer polling loop (ruling out monitor-only instructions or polling loops). Verified by `./dev.py test tests/integration/test_ask_mcp_supervision.py tests/integration/test_ask_view_events.py tests/integration/test_ask_plan_handoff.py`.
4. `plan-ticket-serve.md` starts and restarts `serve` detached via `clutch_engine_start(mode="serve")` or `clutch engine serve --detach` and stops via `clutch_engine_control(action="stop")` or `clutch engine stop`, omitting `"background-process facility"`, `"drain.out"`, and `"clutch engine drain"` (ruling out session-tied foreground/background-process `serve` instructions). Verified by `./dev.py test tests/integration/test_ask_plan_serve.py tests/integration/test_ask_mcp_supervision.py`.
5. `plan-ticket-drain.md` and `plan-ticket-serve.md` retain the Claude `Sonnet`-not-`Opus` and cross-family calibration rules and add Antigravity `invoke_subagent` routing requiring `Model: "inherit"` (or `"pro"` / strong model, never `"flash"`) for row authors (`clutch prompt author <stem>`) and phase-closing reviews, reserving `Model: "flash"` only for running `clutch roadmap gate` (ruling out using `"flash"` for row authors or phase-closing reviews, and ruling out forbidden session strings such as `gemini`). Verified by `./dev.py test tests/integration/test_ask_mcp_supervision.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_drain.py`.
6. `drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md` specify that Suggestion Box triage does not run on every tick and runs once at the end of a phase right before the release gate unless the owner explicitly asks otherwise, while retaining `roadmap_row` exclusion, inbox queueing for `clutch box triage`, between-drains restriction for `clutch box dismiss`, and final triage verdicts (ruling out per-tick triage instructions). Verified by `./dev.py test tests/integration/test_ask_mcp_supervision.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_box_triage_inbox.py`.
7. `docs/how-clutch-works.md` section 7.5 documents the MCP-first supervising loop and phase-end Suggestion Box triage cadence (ruling out stale per-tick triage prose), and all existing ask/prompt tests pass (`./dev.py test tests/integration/test_ask_mcp_supervision.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_handoff.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_depends_rule.py tests/integration/test_ask_view_events.py tests/integration/test_box_triage_inbox.py tests/integration/test_ask.py tests/integration/test_mcp_read_server.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py` exits `0`).

## Verification
```
./dev.py test tests/integration/test_ask_mcp_supervision.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_plan_handoff.py tests/integration/test_ask_plan_subagent_models.py tests/integration/test_ask_plan_priority_order.py tests/integration/test_ask_plan_read_queue.py tests/integration/test_ask_plan_conduct_covered.py tests/integration/test_ask_plan_shared_paths.py tests/integration/test_ask_depends_rule.py tests/integration/test_ask_view_events.py tests/integration/test_box_triage_inbox.py tests/integration/test_ask.py tests/integration/test_mcp_read_server.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_plan_serve.py
```

## Definition of rejected
- `clutch/specs/ask/drain-loop.md` still starts with `/loop`.
- Any of the three supervising prompts references a non-existent `clutch_*` MCP tool name, a non-existent `clutch` CLI verb, or a forbidden session fact (including `gemini`).
- Any prompt instructs running `"flash"` for row authors or phase-closing reviews, or instructs running Suggestion Box triage on every tick.
- `plan-ticket-serve.md` still instructs running `clutch engine serve` under a `background-process facility` instead of detached, or mentions `drain.out` or `clutch engine drain`.
- `tests/integration/test_ask_mcp_supervision.py` writes to disk or spawns a process, or any file outside `## Scope fence` is modified.

## Time budget
- expected: 20m
- stuck: 40m
