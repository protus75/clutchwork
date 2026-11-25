<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Onboard Google Antigravity as the primary ClutchWork operator UI, MCP server, and unattended drain/serve supervisor in place of VS Code
relates: [clutch/__main__.py, clutch/ask.py, clutch/events.py, clutch/graph.py, clutch/help.py, clutch/hostfiles.py, clutch/observe.py, clutch/status.py, docs/engine-state-db-plan.md, docs/how-clutch-works.md, docs/mcp-server-notes.md, docs/roadmap.md, vscode-clutchwork/extension.js]
owner: engine
verified: bb5f97db
hash: fb24a903fd15413e8fec26f76fdbba5a2be34dda00efef0ed113d8efb6057c70
-->
# Antigravity UI, MCP server, and supervising agent: plan

Replace the VS Code extension workflow with Google Antigravity (Antigravity IDE and Antigravity 2.0) as the primary operator UI and supervising agent environment for ClutchWork. A pure-Python stdio MCP server (`clutch mcp serve`) exposes typed observation, prompt, ticket, Suggestion Box, and non-blocking engine-control tools over Clutch's existing Python domain owners, while keeping deterministic Check/Verification commands, release gates, and environment bootstrap on the CLI. The same MCP server serves a single-file MCP App (`ui://clutch/dashboard.html`) into Antigravity's side pane and global sidebar, reusing Clutch's snapshot, pure graph layout, shared JS renderers, and single-source help registry. Shipped supervising prompts (`drain-loop`, `plan-ticket-drain`, `plan-ticket-serve`) become MCP-first and host-agnostic with reactive one-shot event wakeups and detached `serve` lifecycle, and `clutch host antigravity` installs the `clutchwork` Antigravity plugin and thin wrapper skills across all host repositories.

## Status

Draft plan. Nothing in it is in effect and no ticket is authored. Written 2026-11-24 at commit `bb5f97db2`; revised 2026-11-24 at commit `bb5f97db2`.

## Roadmap

Release phase `0.7.0` in `docs/roadmap.md` (which ships as PyPI `0.8.0` / tag `v0.8.0`, since `clutch release ship` bumps `--minor` at phase close: phase `0.5.0` shipped as `v0.6.0`, and current `pyproject.toml` `0.6.1` drives phase `0.6.0` toward `v0.7.0`). Scheduled as rows 218–225 at `P1` ahead of the `P2`/`P3` document-agent rows, starting once phase `0.6.0` completes the engine state rewrite and tags `v0.7.0` (`docs/roadmap.md` §6, decision 24 forbids feature tickets during the phase `0.6.0` window). Needs from other plans: `state-service-handoff` (`docs/engine-state-db-plan.md`, row 214) so MCP reads, verdicts, and `engine ping` liveness talk to the lockless per-user DuckDB state service and project registry rather than retiring lockfiles; `view-events-stream` (row 161, merged) for actionable event filtering; `cli-help-standard` (row 129, merged) for command-group help. What needs this plan: daily operator supervision and UI inspection in Antigravity across Clutch and all external host repos; supersedes the exploratory `docs/mcp-server-notes.md`. Shared budgets: one new CLI group `mcp` (`clutch mcp serve`), one new `host` subcommand (`clutch host antigravity`), `--once`/`--cursor`/`--timeout` on `clutch view events`, `--detach` on `clutch engine serve`, and zero bytes of `CORE_TEMPLATE` budget (`AGENTS.md` is already loaded natively by Antigravity).

## Current state

- **UI is coupled to VS Code APIs.** `vscode-clutchwork/extension.js` provides five Activity Bar views (`Tickets`, `Details`, `Recent Steps`, `Suggestion Box`, `Stats`), runs `clutch view snapshot` and CLI actions via `child_process.execFile`, opens files through `vscode.window.showTextDocument`, and launches supervising sessions via an undocumented `anthropic.claude-code/open` URI (`vscode-clutchwork/extension.js:68-73`). Its browser scripts (`vscode-clutchwork/media/graph.js`, `view.js`, `detail.js`, `box.js`) keep domain logic in Python (`clutch/observe.py`, `clutch/graph.py`, `clutch/help.py`) but call `acquireVsCodeApi()` and VS Code CSS variables directly.
- **No MCP adapter exists.** Every agent interaction runs `clutch` subprocesses in a shell. In Antigravity's sandboxed non-login shell, `~/.local/bin` (`uv`) is absent from default `PATH`, shell commands require command-shape approval or path prefixes, and agents parse human-oriented text output from `clutch view status` and `clutch roadmap status`. `docs/mcp-server-notes.md` recorded exploratory notes concluding that any MCP layer must remain a thin adapter over the CLI's Python owners and never own daemon process lifetime.
- **Supervising prompts assume Claude Code primitives.** `clutch/specs/ask/drain-loop.md` begins with Claude Code's `/loop` slash command, and `drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md` require arming `clutch view events` under a line-by-line streaming `Monitor` tool and selecting Claude `Sonnet` to avoid `Opus` inheritance. Antigravity has no line-by-line stdout monitor: background `run_command` notifies on process exit, while MCP tool calls, `invoke_subagent` completions, and `schedule` timers wake the agent turn-by-turn.
- **`clutch view events` only streams forever, and `engine serve` has no `--detach`.** `clutch/events.py::stream` loops until `Ctrl-C` with no cursor or single-event exit mode. `clutch engine drain --detach` detaches its own session and writes `<state_dir>/drain.out`, whereas `clutch engine serve` runs in the foreground (`plan-ticket-serve.md` relies on a session-tied background process).
- **`AGENTS.md` already loads in Antigravity, but skills and plugins are not installed.** `clutch host core` (`clutch/__main__.py:1476`, `clutch/providers.py:194-202`) refreshes `CLAUDE.md` and `AGENTS.md`. Antigravity natively discovers `AGENTS.md` at the repository root, so core conduct rules already apply without a `GEMINI.md` file, and discovers plugins under `~/.gemini/config/plugins/<name>/` and workspace skills under `.agents/skills/<name>/SKILL.md`.

## Departures from the design record

| Record says | This plan | Why |
|---|---|---|
| `CLUTCH_PLAN.md` §18.1 closed CLI verb set of 16; `docs/mcp-server-notes.md` deferred mutating MCP tools and daemon start/stop | Adds `clutch mcp serve` (group `mcp`), `clutch host antigravity`, `view events --once`, and `engine serve --detach`; exposes admission-gated ticket, box, and detached engine-control MCP tools | Owner decision 2026-11-24 to onboard Antigravity as primary UI instead of VS Code and drive `drain` and `serve` through MCP where appropriate. Daemon lifetime stays detached in the engine service (`--detach` / `0.6.0` service), never tied to the MCP stdio pipe |
| `AGENTS.md` Pure Python rule (with `vscode-clutchwork/` as the sole operator-only JS exception) | Extends the operator-only client JS exception to the shared UI bundle rendered into `clutch/ui/dashboard.html` for the MCP App | Same boundary and reason: the engine never executes JS; `clutch/observe.py`, `clutch/graph.py`, and `clutch/help.py` own all projection, layout, admission, and help logic, while browser JS only renders DOM/SVG and calls MCP App bridge methods |

`CLUTCH_PLAN.md` stays frozen. Implementation tickets update `docs/how-clutch-works.md` §2.1–2.2, `clutch/docs/host-running.md`, `clutch/docs/host-contract.md`, and `README.md`.

## Target design

### 1. Event cursor and reactive wakeup (`events-once-cursor`)

 Supervising agents in Antigravity wake on completed tool calls, subagent messages, or timers rather than per-line stdout hooks. `clutch/events.py` gains an opaque JSON/base64 state cursor (encoding the journal offset, Reject-queue stem set, seen engine-lifecycle step keys, and gate map already computed by `changes()`) and a `wait_once(state, *, cursor=None, timeout=300.0, sleep=time.sleep, clock=time.monotonic, interval=POLL_SECONDS)` function:

- With `cursor=None`, `poll()` establishes the baseline cursor and blocks up to `timeout` seconds until `changes()` produces at least one actionable line, returning `(next_cursor, lines, timed_out)`.
- With a previously returned `cursor`, `poll()` immediately diffs current state against `cursor`—so zero events are missed between turns while the agent is thinking or acting—and returns immediately if lines already arrived, or waits up to `timeout` seconds otherwise.
- `clutch view events` gains `--once`, `--cursor CURSOR`, and `--timeout SECONDS` (printing JSON `{"cursor": ..., "events": [...], "timed_out": bool}` when `--once` is passed, while bare `clutch view events` preserves its streaming line behavior for terminal/Claude monitors).

### 2. Detached daemon lifecycle (`engine-serve-detach`)

Following the `AGENTS.md` rule *"Launchers carry no process policy"*, `clutch engine serve` gains `--detach` matching `clutch engine drain --detach`:

- Starts `serve` in its own detached OS session (`start_new_session=True` through the exec seam), redirects stdout/stderr to `<state_dir>/serve.out`, waits briefly to confirm startup or surface an immediate refusal, and exits 0.
- Reloading Antigravity, restarting the MCP server, or ending a chat conversation never kills a running `drain` or `serve`. Stopping or killing uses `clutch engine stop` / `clutch engine kill` (or `clutch_engine_control`).

### 3. Clutch MCP server vs. direct CLI boundary (`mcp-read-server`, `mcp-control-and-tickets`)

`clutch mcp serve` runs a pure-Python JSON-RPC 2.0 MCP server over **Stdio** (`clutch/mcp.py`), using Pydantic schemas already in core Clutch (no heavy third-party framework required). Each tool accepts an optional `repo` path (defaulting to the current working directory and validated against registered checkouts in the `0.6.0` state service) so a single global Antigravity plugin works seamlessly across every host project.

**Principle — MCP where structured or interactive, CLI where deterministic or headless:**

| Category | Surface | Why |
|---|---|---|
| **Observation & Projections** (`snapshot`, `status`, `stats`, `roadmap_status`, `evidence_captures`, `evidence_show`, `context_suggest`) | **MCP tools** (`clutch_*`, `visibility: ["model", "app"]`) | Returns typed `structuredContent` plus concise model text; eliminates brittle text scraping and sandbox `PATH` friction |
| **Event Monitoring** (`clutch_wait_event`) | **MCP tool** (`visibility: ["model"]`) | Passes `cursor` and `timeout_seconds` directly to `events.wait_once()`; wakes the supervising turn reactively with zero missed events between ticks |
| **Operator Prompts** (`drain-loop`, `plan-ticket-drain`, `plan-ticket-serve`, `diagnose`, `running`, `drafts`, `box`, `author`, `review`, `roadmap`, `host`) | **MCP Prompts + `clutch_prompt` tool** | Agents and the MCP App fetch canonical rendered specs from `clutch/ask.py` without shell calls |
| **Ticket & Box Mutations** (`ticket_new`, `ticket_lint`, `ticket_order`, `ticket_confirm`, `ticket_reject`, `box_suggest`, `box_triage`, `box_dismiss`) | **MCP tools** (gated by `clutch/status.py` admission functions) | Structured validation findings and paved roads. Model-visible `clutch_ticket_confirm` / `clutch_ticket_reject` always record `actor: operator` (never `--extension`); a separate `visibility: ["app"]` tool serves human clicks in the MCP App |
| **Engine Lifecycle Signals** (`engine_start` with `drain`/`serve` always detached; `engine_control` for `pause`, `resume`, `stop`, `kill`, `ping`; `engine_retro`) | **MCP tools** | Non-blocking requests only; daemon lifetime lives in the detached engine/service process, never inside the MCP server |
| **Ticket Verification, Regression, Mechanical Gates & Release Gates** (`./dev.py test`, `clutch coverage gate`, `clutch meta check`, `clutch roadmap gate`, `clutch roadmap accept`) | **Direct CLI (`run_command` / engine exec)** | Must remain reproducible, recorded argv commands in `checks.json` and `docs/roadmap.md` fenced `gate` blocks that run identically with no UI or MCP host present |
| **Environment Bootstrap & Multi-Minute Foreground Runs** (`clutch host doctor`, `clutch host core`, `clutch provider probe`, `clutch provider install`, `clutch engine run <stem>`, `clutch release ship`) | **Direct CLI** | Bootstrap must diagnose broken venvs before MCP can start; `release ship` stays manual-operator CLI per prompt delegation rules; synchronous multi-minute runs avoid stdio RPC timeouts |

Every MCP tool calls the underlying Python functions in `clutch` directly and maps `Refusal` exceptions to structured MCP tool errors carrying `code`, `message`, and `paved_road`. No business logic, sorting, filtering, or admission rules live in `clutch/mcp.py`.

### 4. Antigravity MCP App dashboard replacing VS Code views (`ui-shared-renderers`, `mcp-app-dashboard`)

`clutch mcp serve` declares UI resource `ui://clutch/dashboard.html` (`mime_type="text/html;profile=mcp-app"`) and attaches Antigravity entrypoints on `clutch_open_dashboard` (`meta={"ui": {"resourceUri": "ui://clutch/dashboard.html"}, "com.google.antigravity/ui": {"entrypoints": [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]}}`):

- **Side-pane (`aux_pane`) and full-page sidebar (`global`) parity with `vscode-clutchwork`:**
  1. **Tickets tab:** SCM-style SVG dependency graph rendered from `clutch/graph.py` lanes (`blocked`, `queued`, `running`, `merged`), engine liveness indicator (`engine ping`), play/stop (`drain` or `serve`), priority and `runs-before` controls, and admission-gated `confirm`/`reject` actions.
  2. **Details pane:** Focused ticket or Suggestion Box message, `Shared fence` collisions, status reason, and clickable artifact links (`ticket.md`, `run.md`, `checks.json`, `review.md`, `diagnosis.json`, `rework.md`, `config.yaml`).
  3. **Recent Steps tab:** Closed `STEP_KINDS` activity feed from `clutch/observe.py` opening step artifacts on click.
  4. **Suggestion Box tab:** Pending/resolved messages, multi-select, manual `triage`, and `dismiss`.
  5. **Stats tab:** Windowed health, spend, and throughput figures from `view stats`.
  6. **Help & Lifecycle:** Every surface renders its description and doc link from `clutch/help.py`; includes the `ticket-lifecycle.svg` diagram.
- **Native Antigravity integrations (via `@modelcontextprotocol/ext-apps`):**
  - **Theme sync:** Applies `--color-background-*`, `--color-text-*`, `--color-border-*`, and `--font-sans` via `applyDocumentTheme` and `applyHostStyleVariables` on `connect()` and `onhostcontextchanged`.
  - **File opening:** Sends `com.google.antigravity/toggle-aux-pane` (`{tabType: "fileView", uri: "file:///..."}`) to open `ticket.md`, `run.md`, `review.md`, or `config.yaml` directly in an Antigravity editor/side-pane tab (gracefully hidden/disabled when `global` view reports `-32601` or `isError`).
  - **Agent kickoff (replacing `openClaude`):** Action buttons (*"Supervise Drain Loop"*, *"Run Roadmap (Drain)"*, *"Run Roadmap (Serve)"*, *"Diagnose Stem"*, *"Review Drafts"*) call `app.sendMessage()` to send the prompt into the current conversation, or pass `_meta: {"com.google.antigravity/message": {"target": "new"}}` to spin up a dedicated background supervising conversation in the project. Selecting a row optionally attaches a `resource_link` pill via `app.updateModelContext()`.
  - **Payload cap safety:** Because Antigravity caps trajectory `CallToolResult` at 1 MiB (`mcp-app-development`), `clutch_open_dashboard` returns a compact summary for the model while the iframe fetches full snapshots and stats through `visibility: ["app"]` server tools (`clutch_app_snapshot`, `clutch_app_stats`) and refreshes on poll/focus without bloating chat history.
- **One shared renderer, zero duplicate JS logic:** `vscode-clutchwork/media/{graph,view,detail,box}.js` are refactored to accept a tiny host-bridge object (`callTool`, `openFile`, `sendPrompt`, `openHelp`), bundled with `@modelcontextprotocol/ext-apps` via a `./dev.py ui-bundle` task into self-contained `clutch/ui/dashboard.html`.

### 5. Supervising `drain` and `serve` in Antigravity (`ask-specs-mcp-supervision`)

In keeping with `AGENTS.md` (*"Keep shipped process prompts in sync"* and *"One authoring process"*), `clutch/specs/ask/drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md` remain the single canonical specifications and are updated rather than forked:

- **Drop the leading `/loop` literal** from `drain-loop.md` (Claude Code users can still pass it to `/loop`, while Antigravity skills and MCP prompts invoke it cleanly).
- **MCP-first action mapping:** Where `clutch_*` MCP tools are present in the session, the operator uses `clutch_status`, `clutch_snapshot`, `clutch_roadmap_status`, `clutch_prompt`, `clutch_ticket_*`, `clutch_box_*`, `clutch_engine_start`, and `clutch_engine_control`; CLI commands remain the fallback when MCP is absent and remain mandatory for `clutch host doctor`, `clutch provider probe`, the host test suite, and `clutch roadmap gate <release>`.
- **Dual-mode event waiting (no polling loops):** Between ticks, the operator either (a) calls `clutch_wait_event(cursor=..., timeout_seconds=300)` (or runs `clutch view events --once --cursor ... --timeout 300` as a background command) alongside any running authoring subagents—waking immediately when either an engine event or a subagent finishes—or (b) uses a streaming `Monitor` on `clutch view events` when the host agent provides one.
- **Explicit child-model routing across agent hosts:** Retains the Claude `Sonnet`-not-`Opus` rule for Claude hosts and adds explicit Antigravity `invoke_subagent` guidance: use `Model: "flash"` for row authors (`clutch prompt author <stem>`), `roadmap gate` runners, and open-decision proposal agents, and `Model: "pro"` (or `"inherit"`) for phase-closing acceptance reviews, while keeping calibration/baseline label panels routed through Clutch's cross-family provider config (`docs/roadmap.md` §5, decision 13).
- **Detached `serve` supervision:** `plan-ticket-serve.md` starts the daemon via `clutch_engine_start(mode="serve")` / `clutch engine serve --detach`, monitors via `clutch_wait_event` and `clutch_evidence_captures` / `engine.log`, stops cleanly with `clutch_engine_control(action="stop")` when no-engine steps (`box dismiss`, Reject-queue edits, `host doctor`) require quiescence, and restarts detached afterward.

### 6. Host and machine onboarding (`host-antigravity-plugin`)

- **`clutch host antigravity [--plugin-dir PATH] [--workspace]`:**
  - Default (global machine setup): writes/refreshes `~/.gemini/config/plugins/clutchwork/` containing:
    - `plugin.json`: `name: "clutchwork"`, `displayName: "ClutchWork"`, `logo: "assets/logo.svg"`, and 3 `suggestedPrompts` (*"Open the ClutchWork dashboard"*, *"Supervise the Clutch queue (drain-loop)"*, *"Run docs/roadmap.md unattended with serve"*).
    - `mcp_config.json`: configures `"clutchwork"` stdio server invoking the exact Python/clutch executable of the installing environment (`sys.executable -m clutch mcp serve`), avoiding `PATH` lookup failures inside sandboxed shells.
    - `assets/logo.svg`: copied from Clutch's package assets.
    - Thin skills (`skills/clutch-drain-loop/SKILL.md`, `skills/clutch-plan-drain/SKILL.md`, `skills/clutch-plan-serve/SKILL.md`): each skill is under 40 lines, instructs Antigravity to call `clutch_prompt` for the canonical spec, binds Antigravity's `invoke_subagent` / `clutch_wait_event` / side-pane UI tools, and carries zero duplicated process rules.
  - With `--workspace`: writes `.agents/skills/clutch-*/SKILL.md` into the target host checkout for teams checking Antigravity skills into VCS (leaving `routed_conduct_paths` and `CoreDriftGate` strictly scoped to `CLAUDE.md` and `AGENTS.md`).
- **`clutch host core`:** Unchanged in scope—continues to render `CORE_TEMPLATE` into `AGENTS.md`, which Antigravity loads automatically in every workspace.
- **`clutch host doctor`:** When `~/.gemini/config/plugins/clutchwork/` exists, verifies its `mcp_config.json` executable still resolves and matches the current schema, printing a warning with paved road `clutch host antigravity` if drifted.

## Where each piece lives

| Piece | Home |
|---|---|
| Stateful event cursor & `wait_once`, `view events --once` | `clutch/events.py`, `clutch/__main__.py` |
| `engine serve --detach` | `clutch/__main__.py`, `clutch/serve.py` |
| Stdio MCP JSON-RPC server, tools, prompts, `ui://` resource | new `clutch/mcp.py`, `clutch/__main__.py` (`mcp serve` group/verb) |
| Shared pure DOM/SVG renderers & host bridge | `vscode-clutchwork/media/{graph,view,detail,box}.js`, `vscode-clutchwork/extension.js`, `clutch/help.py` |
| Bundled Antigravity MCP App HTML | `clutch/ui/` (source + built `dashboard.html`), `./dev.py` (`ui-bundle`) |
| Host-agnostic MCP-first supervising prompts | `clutch/specs/ask/drain-loop.md`, `clutch/specs/ask/plan-ticket-drain.md`, `clutch/specs/ask/plan-ticket-serve.md` |
| Antigravity plugin & thin skill installer, doctor check | new `clutch/antigravity.py`, `clutch/__main__.py` (`host antigravity`), `clutch/doctor.py` |
| Documentation | `docs/how-clutch-works.md`, `clutch/docs/host-running.md`, `clutch/docs/host-contract.md`, `README.md` |

## Ticket breakdown

Each ticket targets <= 30 AI minutes (`docs/roadmap.md` §6, decision 22) and places all new unit and integration tests in new `tests/unit/test_<module>_<behavior>.py` / `tests/integration/test_<behavior>.py` files outside the seven do-not-grow test files (`docs/parallel-tickets-plan.md` §7). Release `0.7.0`.

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| 1 | `events-once-cursor` | feature | P1 | `state-service-handoff` | Cursor token and `wait_once(state, *, cursor, timeout, sleep)` in `clutch/events.py`; `--once`, `--cursor`, and `--timeout` on `clutch view events` emitting structured JSON; CLI help and doc updates. |
| 2 | `engine-serve-detach` | feature | P1 | `state-service-handoff` | `--detach` on `clutch engine serve` (detached session, `<state_dir>/serve.out`, startup check) matching `engine drain --detach`; CLI help and command docs. |
| 3 | `mcp-read-server` | feature | P1 | `events-once-cursor` | `clutch/mcp.py` stdio JSON-RPC 2.0 server and `clutch mcp serve` verb: read-only tools (`clutch_snapshot`, `clutch_status`, `clutch_stats`, `clutch_roadmap_status`, `clutch_wait_event`, `clutch_evidence_captures`, `clutch_evidence_show`, `clutch_context_suggest`, `clutch_prompt`) and MCP Prompts for `clutch/specs/ask/*.md`, with optional `repo` routing. |
| 4 | `mcp-control-and-tickets` | feature | P1 | `mcp-read-server`, `engine-serve-detach` | Admission-gated MCP tools for `ticket_new`, `ticket_lint`, `ticket_order`, `ticket_confirm`, `ticket_reject` (separating model `actor: operator` from `app`-only UI verdicts), `box_suggest`, `box_triage`, `box_dismiss`, detached `engine_start` (`drain`/`serve`), `engine_control` (`pause`/`resume`/`stop`/`kill`/`ping`), and `engine_retro`. |
| 5 | `ui-shared-renderers` | chore | P1 | `state-service-handoff` | Refactor `vscode-clutchwork/media/{graph,view,detail,box}.js` and `view.css` behind a thin host adapter (`callTool`, `openFile`, `sendPrompt`, `openHelp`) while keeping `vscode-clutchwork` behavior identical; update `clutch/help.py` surfaces for shared UI views. |
| 6 | `mcp-app-dashboard` | feature | P1 | `mcp-control-and-tickets`, `ui-shared-renderers` | Build `clutch/ui/dashboard.html` with `@modelcontextprotocol/ext-apps` (`./dev.py ui-bundle`) and serve `ui://clutch/dashboard.html` on `clutch_open_dashboard` (`aux_pane` and `global` entrypoints) plus `app`-only data tools, theme variable binding, `toggle-aux-pane` file open, and `app.sendMessage` prompt launch. |
| 7 | `ask-specs-mcp-supervision` | feature | P1 | `mcp-control-and-tickets` | Update `clutch/specs/ask/drain-loop.md`, `plan-ticket-drain.md`, and `plan-ticket-serve.md`: remove `/loop` prefix, prefer `clutch_*` MCP tools where appropriate while keeping CLI for bootstrap/tests/gates, use `clutch_wait_event` cursor wakeups, detached `serve`, and explicit Antigravity `flash`/`pro` subagent mapping. |
| 8 | `host-antigravity-plugin` | feature | P1 | `mcp-app-dashboard`, `ask-specs-mcp-supervision` | `clutch host antigravity` installer for `~/.gemini/config/plugins/clutchwork/` (`plugin.json`, `mcp_config.json`, logo, and thin `clutch-drain-loop`, `clutch-plan-drain`, `clutch-plan-serve` skills), optional `--workspace` `.agents/skills/` output, `host doctor` check, and host/README onboarding docs. |

`Runs before`: `doc-facet-registry` and the other `P2`/`P3` rows of release `0.7.0`.

## Risks

- **MCP stdio lifecycle vs. running engine.** Antigravity terminates stdio MCP servers when the plugin disables or the app exits. Mitigated by never running `drain`, `serve`, or worker subprocesses as children of `clutch mcp serve`; `engine_start` always launches detached (or delegates to the `0.6.0` per-user state service).
- **Trajectory bloat from large snapshots.** Antigravity caps tool results stored in conversation trajectories at 1 MiB. Mitigated by keeping model-facing `clutch_open_dashboard` / `clutch_status` responses concise and fetching full dashboard payloads through `visibility: ["app"]` tools that do not enter model context.
- **Prompt drift between Antigravity skills and `clutch/specs/ask/`.** Mitigated by shipping thin (<40-line) wrapper `SKILL.md` files that call `clutch_prompt` at runtime rather than copying rules.
- **Multi-project ambiguity in a global plugin.** A global MCP server has no fixed checkout CWD when opened from a global sidebar view. Mitigated by requiring `repo` when CWD is not a Clutch checkout and listing registered projects from the `0.6.0` per-user state database in the MCP App's project switcher.
- **Stale MCP server process after `clutch` upgrade.** As documented in Antigravity's MCP guide, a running stdio server keeps its old Python process until restarted. `clutch host antigravity` prints the refresh hint / `customization://clutchwork` toggle instruction, and `clutch_status` includes the running server's package version so mismatches are visible immediately.

## Open decisions

Decided by the owner on 2026-11-24:

1. **Fate of `vscode-clutchwork/` once `mcp-app-dashboard` ships.** **Decided: keep.** Keep `vscode-clutchwork/` in tree sharing the extracted `media/` renderers (`ui-shared-renderers`) so existing extension tests and VSIX builds continue passing without churn; freeze new VS Code-only features and retire `vscode-clutchwork/` only in a later chore ticket if the owner asks.
2. **MCP protocol implementation (`mcp` PyPI SDK vs. pure-Python JSON-RPC over Pydantic).** **Decided: plain Python.** Implement stdio JSON-RPC 2.0 in `clutch/mcp.py` using Clutch's existing `pydantic` dependency (~250 lines, zero new core dependencies, direct control over `_meta` `ui://` and `com.google.antigravity/ui` entrypoints, unit-testable with in-memory streams under `clutch.testguard`).
3. **Plugin scope (`~/.gemini/config/plugins/clutchwork/` global vs. `.agents/` per repo).** **Decided: global by default.** Install globally to `~/.gemini/config/plugins/clutchwork/` via `clutch host antigravity` (required by Antigravity for MCP servers and sidebar UI panels), with `--workspace` available to emit `.agents/skills/` when a repo wants versioned workspace skills.
