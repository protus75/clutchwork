# ClutchWork

*CLI Lifecycle for Unattended Ticket-Chewing Hatchlings*

ClutchWork orchestrates CLI coding agents (`claude`, `codex`, `antigravity`, and `qwen`) through author → requisition → implement → check → review → merge to local `main`. It runs tickets in isolated worktrees with scope fences, mechanical gates, and cross-model review. Each ticket lives in `tickets/<stem>/`; its markdown and JSON files, including `ticket.md`, `run.md`, `review.md`, `diagnosis.json`, and others, pass work between stages. Reviewed work merges to local `main`. See the [ticket lifecycle diagram](https://github.com/protus75/clutchwork/blob/main/vscode-clutchwork/media/ticket-lifecycle.svg).

The engine plane owns the ClutchWork process and gates; the host plane supplies the target repository’s code, tests, `config.yaml`, and roadmap. Run `clutch engine drain` unattended until the queue is quiet, or `clutch engine serve` continuously as new work arrives. The Suggestion Box captures second problems and follow-ups without derailing a ticket. For Antigravity, an MCP server exposes tools and a live interactive dashboard, while thin supervising skills retrieve the engine’s procedures.

[GitHub repository](https://github.com/protus75/clutchwork)

## Install

The Antigravity plugin needs no `clutchwork` dependency in each host repository. Install it with `agy plugin install https://github.com/protus75/clutchwork`; its MCP server runs automatically in an isolated tool environment using `uvx --from clutchwork clutch mcp serve`.

For CLI use across repositories, install once with `uv tool install clutchwork` and run `clutch <verb>`, or use `uvx --from clutchwork clutch <verb>` in any host checkout.

Optionally, teams can pin ClutchWork as a dev dependency in a host project’s `pyproject.toml` and sync its environment:

```sh
uv add --dev clutchwork
uv sync
```

Install the provider CLIs you route with `uv run clutch provider install claude codex` (pnpm dev dependencies under `node_modules/.bin`; a CLI already on `PATH` works without it).

Run its verbs as `uv run clutch <verb>`. Use `clutch meta refresh` to update configured file metadata, `clutch meta check` to report missing, empty or drifted blocks, and `clutch meta fill` to fill missing or empty blocks using a read-only model and refresh drifted blocks without the model. Use `clutch index build` to build the project index, `clutch index query <text>` to search it read-only without a lock, and `clutch context suggest <stem>` to suggest context for a ticket. Your host also needs `config.yaml`; start with the [copyable configuration](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-contract.md), or create one with `uv run clutch config init --write` from the CLIs you installed.

## Set up a host

Run `uv run clutch host doctor` and `uv run clutch provider probe`, then `uv run clutch host core` to write the managed conduct block into `CLAUDE.md` for Claude and Qwen Code or `AGENTS.md` for other CLIs. Commit the files. The block gives a chat agent rules for authoring and editing tickets with `clutch ticket new`, `clutch ticket lint`, and `clutch ticket review`, and for supervising a drain. Re-run `host core` after upgrading clutch: `engine drain`, `engine serve`, and `engine run` refuse to start while the block is stale.

```sh
# Setup
uv run clutch config init  # print a suggested config.yaml
uv run clutch provider install  # install provider CLIs into the host
uv run clutch config update  # list current model names per provider
uv run clutch host doctor   # inspect host setup
uv run clutch provider probe   # probe declared providers and models
uv run clutch host core     # refresh managed conduct files
uv run clutch host antigravity  # optional Antigravity plugin
```

## Author and run tickets

1. Open Claude Code or Codex in the host checkout, often with auto permissions.
2. Work out a plan with the chat agent.
3. Ask it to turn the plan into tickets. It runs `clutch ticket new`, fills each ticket, and repeats `clutch ticket lint` and `clutch ticket review` until each is clean.
4. Ask it to drain the queue with `uv run clutch engine drain`, or leave `uv run clutch engine serve` running to pick up new tickets live. clutch coordinates CLI agents through authoring, implementation, checking, review, and merge.

One unattended drain ran about 30 tickets in about 4 hours, many of them triage-authored bug fixes and small features. The practical limit is how fast a person can plan enough work to fill the queue, so planning sessions with the chat agent are where the person spends their time.

```sh
# Authoring
uv run clutch ticket new      # create and lint a ticket skeleton
uv run clutch ticket lint     # validate tickets without writing
uv run clutch ticket review   # review a committed ticket
uv run clutch ticket order    # edit ticket priority or ordering
uv run clutch box suggest  # file an idea into the Suggestion Box
uv run clutch box issue    # link to report a critical clutch bug or process gap upstream
# Running
uv run clutch engine drain    # run eligible tickets to quiescence
uv run clutch engine serve    # run the continuous daemon
uv run clutch engine serve --detach  # run the continuous daemon detached
uv run clutch engine run      # run one ticket through the pipeline
uv run clutch engine stop     # finish active work and exit
uv run clutch engine kill     # stop the engine at a safe point
uv run clutch engine pause    # ask the engine to pause admission
uv run clutch engine resume   # ask the engine to release its current hold
```

Stop `engine serve` before `engine drain` or `engine run`: each takes the writer lock. See the [host run guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-running.md) for every verb.

## Observe and decide

5. Ask the chat agent to supervise: watch `clutch view status` and `clutch view watch`, diagnose rejected or blocked tickets from their `tickets/<stem>/` artifacts, fix small ticket problems, and stop with `clutch engine stop` or `clutch engine kill` and restart the drain as needed.
6. Use the Suggestion Box as an escape valve. An implementing agent reports second problems in its `second_problems` reply, and the engine files them to the box so the ticket can complete its own goal. Retros and `clutch box suggest` from a chat session also file there. An attempt-cap exhaustion puts the run in the Reject queue, where the supervisor may edit and keep a `gate_failed` or `premise_failed` ticket (`docs/how-clutch-works.md` section 6.6); otherwise it waits for `ticket confirm` or `ticket reject`. Triage resolves each message as `declined`, `tombstone` (already covered), or authored into a ticket; an authored ticket can start as a `draft` awaiting a person.
7. Keep the judgment calls: ask the chat agent for a plain-English summary of each draft or held ticket, then run `clutch ticket confirm` or `clutch ticket reject` on each.

In clutch's own repository history, measured on 2026-11-09 from `.clutch/state/box/` and the journal, 32 of 389 Suggestion Box messages (about 8%) became tickets, all as drafts. Of the 31 drafts decided, 24 were confirmed (about 77%) and 7 rejected.

Run `uv run clutch prompt roadmap` to print the procedure for creating or maintaining `docs/roadmap.md`. Then use `uv run clutch roadmap status` and hand off through `uv run clutch prompt plan-ticket-drain`.

For example, ask your chat agent:

- “Help me plan this feature and turn the plan into clutch tickets.”
- “Drain the queue and supervise any held tickets.”
- “Summarize the drafts in plain English so I can decide which to confirm.”

```sh
# Observing

uv run clutch mcp serve  # run the stdio MCP server
uv run clutch view status   # show the journal projection
uv run clutch view watch    # show the live text view
uv run clutch view stats    # show health and efficiency figures
uv run clutch view events   # print one line per actionable engine change
uv run clutch view events --once --timeout 300  # wait once for changes as JSON
# Decisions
uv run clutch ticket confirm  # confirm a draft or Reject item
uv run clutch ticket reject   # reject a draft or Reject item
```

## Examples

Bootstrap a new host without adding ClutchWork to its dependencies. From the host checkout, install the tool once, install the provider CLIs you need, and create and check the host configuration:

```sh
uv tool install clutchwork
clutch provider install claude codex
clutch config init --write
clutch host doctor
clutch provider probe
clutch host core
```

Review `config.yaml` and the generated conduct files, then commit them. Provider installation adds provider CLI dev dependencies to the host; an existing CLI on `PATH` can be used instead. To avoid a global tool installation, substitute `uvx --from clutchwork clutch` for `clutch` in these commands.

In any configured workspace with the Antigravity plugin installed, ask the agent:

- “Open the ClutchWork dashboard” to inspect the live queue.
- “Supervise the Clutch queue (drain-loop)” to watch and handle a drain.
- “Run docs/roadmap.md unattended with serve” to run the roadmap continuously.

For a feature, ask the chat agent to plan it and turn the plan into tickets, then run `clutch engine drain` unattended. After the drain, ask for summaries of drafts and Reject-queue items; use `clutch ticket confirm` or `clutch ticket reject` for your decisions. Run `clutch box triage` to process Suggestion Box follow-ups and review any resulting drafts.

## Antigravity plugin

The ClutchWork Antigravity plugin is a thin wrapper (`plugin.json`, `mcp_config.json`, `hooks.json`, `assets/logo.png`, and `skills/clutch-*/SKILL.md`) that exposes ClutchWork's MCP tools, live interactive dashboard, and supervising skills in Antigravity. No per-host `clutchwork` dependency is required, and `hooks.json` automatically tracks the active Antigravity workspace.

### Prerequisites and installation

Install the Antigravity CLI (`agy`) and sign in (see [Antigravity provider setup](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-antigravity.md)), and configure a host repository with `config.yaml` and `clutch host core` (which installs the `AGENTS.md` conduct block Antigravity reads).

- **Portable bundle (recommended)**: install directly from GitHub; the plugin runs its stdio MCP server in an isolated environment using `uvx --from clutchwork clutch mcp serve`:

```sh
agy plugin install https://github.com/protus75/clutchwork
```

- **Local machine installation**: install from an existing ClutchWork environment into `~/.gemini/config/plugins/clutchwork/`:

```sh
uv run clutch host antigravity
```

Use `--plugin-dir PATH` to choose a custom plugin directory, or `--workspace` to write workspace skills under `.agents/skills/`.

### Usage

In any configured workspace with the plugin enabled, ask Antigravity directly or invoke its bundled skills:

- **Live dashboard**: ask `"Open the ClutchWork dashboard"` to open the interactive queue, ticket graph, Suggestion Box, and engine status view.
- **Supervising skills**:
  - `clutch-drain-loop`: supervise an active `engine drain` queue (for example, `"Supervise the Clutch queue (drain-loop)"`).
  - `clutch-plan-drain`: turn a plan or roadmap into tickets and supervise a drain.
  - `clutch-plan-serve`: plan tickets and run `docs/roadmap.md` unattended with `engine serve` (for example, `"Run docs/roadmap.md unattended with serve"`).
- **MCP tools**: the `clutchwork` MCP server exposes tools for snapshots, status, stats, roadmap status, event waiting, evidence inspection, context/index queries, ticket authoring/linting/ordering/verdicts, Suggestion Box triage/dismissal, and engine start/control/retro.

### Upgrading and troubleshooting

After upgrading `clutchwork`, toggle ClutchWork at `customization://clutchwork` to reload the stdio MCP server. Run `clutch host doctor` to check for plugin configuration drift or an unresolvable server executable. After publishing a release to PyPI, maintainers can run `agy plugin validate --strict .` from the repository root before submitting to the Antigravity Marketplace.

## VS Code extension

The [ClutchWork tickets extension](https://marketplace.visualstudio.com/items?itemName=chunkydragon.vscode-clutchwork) (`chunkydragon.vscode-clutchwork`) adds a ClutchWork view to the VS Code Activity Bar for inspecting and operating a host repository.

### Prerequisites and installation

Open a repository containing `tickets/` with ClutchWork installed (see the Install section above and the [host contract](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-contract.md#vs-code-extension)). Under WSL or Remote-SSH, install and run the extension on the remote side where the repository and `clutch` executable live.

- **VS Code**: install **ClutchWork tickets** (`chunkydragon.vscode-clutchwork`) from the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=chunkydragon.vscode-clutchwork), or run:

```sh
code --install-extension chunkydragon.vscode-clutchwork
```

- **Cursor / VSCodium**: use **Install from VSIX** with a packaged `vscode-clutchwork` `.vsix` file.

### Usage

Click the **ClutchWork** icon in the Activity Bar to open five views:

- **Tickets**: SCM-style dependency graph of blocked, queued, running, and merged tickets. Use the title bar **Play** / **Stop** button or **Engine…** picker to start `drain` or `serve`, stop, kill, check status, or run a retro. Right-click a ticket to open `ticket.md`, lint, review, run now, confirm or reject, set priority, set `Runs before`, or ask Claude to diagnose, review, or assess drafts.
- **Details**: shows the selected ticket (including shared scope fences) or Suggestion Box message, with `Next` action links.
- **Recent Steps**: live engine activity log; clicking a step opens its ticket, message, or decision file.
- **Suggestion Box**: lists box messages with multi-select support for manual triage, dismissal, or opening the linked ticket/record.
- **Stats** (collapsed by default): health and efficiency figures for the configured window.

Hover over extension surfaces for inline help, open the **Help** command from any view menu to browse all topics, or open **Ticket lifecycle** from the Tickets **More Actions** menu to view the state diagram.

### Configuration and troubleshooting

- `clutch.command` (default `[".venv/bin/clutch"]`): command and arguments used to run `clutch`, resolved relative to the workspace folder. Override this when `clutch` is installed globally (for example `["clutch"]` or `["uvx", "--from", "clutchwork", "clutch"]`) or on native Windows (`[".venv\\Scripts\\clutch.exe"]`). If a view reports `clutch command not found`, update this setting.
- `clutch.playAction` (default `"drain"`): selects whether the Tickets play button starts `drain` or `serve`.
- `clutch.statsWindow` (default `"7d"`): time or settled-ticket window for the Stats view (for example `24h`, `7d`, `50t`).
- `clutch.refreshSeconds` (default `15`): timed refresh interval in seconds (`0` disables the timer while file-change refreshes continue).
- `clutch.unavailableMenuItems` (default `"disable"`): whether unavailable ticket context-menu actions are disabled or hidden (`"hide"`).

If a view reports `cannot draw the clutch snapshot`, the installed extension is older than the `clutch` version in the workspace; update the extension from the Marketplace and reload the window.

## Guides

The host guides ship inside the installed package; `uv run clutch host docs` prints each local path so agents read the copy matching the installed version.

- [Host run guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-running.md): invocation and operation on a host.
- [Host ticket authoring](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-authoring.md): what to write in a ticket.
- [Host contract](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-contract.md): the config schema and host-facing contract.
- [Local qwen provider setup](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-qwen.md).
- [Antigravity provider setup](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-antigravity.md).
- [Training data guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-training.md).
- [How clutch works](https://github.com/protus75/clutchwork/blob/main/docs/how-clutch-works.md): how clutch behaves today. Tickets keep it current.

## Developing clutch

This section is for working on clutch's own repository, where every clutch verb runs from the checkout as `uv run clutch <verb>`, as in a host:

    ./dev.py                  # the full suite (unit under clutch.testguard)
    ./dev.py test [args]      # the suite, or named tests (unit under clutch.testguard)
    ./dev.py vscode           # package and install the vscode-clutchwork extension
    ./dev.py vscode-package   # build a VSIX for Marketplace upload

`CLUTCH_PLAN.md` is the frozen record of how clutch was first built. It is history, not a reference.
