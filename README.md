# ClutchWork

*CLI Lifecycle for Unattended Ticket-Chewing Hatchlings*

ClutchWork is an engine that runs CLI coding agents through the ticket lifecycle against a git repository. Each ticket lives in `tickets/<stem>/`; its markdown and JSON files, including `ticket.md`, `run.md`, `review.md`, `diagnosis.json`, and others, pass work between stages. Reviewed work merges to local `main`. See the [ticket lifecycle diagram](https://github.com/protus75/clutchwork/blob/main/vscode-clutchwork/media/ticket-lifecycle.svg).

[GitHub repository](https://github.com/protus75/clutchwork)

## Install

Add clutch to your host project and sync its environment:

```sh
uv add --dev clutchwork
uv sync
```

Install the provider CLIs you route with `uv run clutch provider install claude codex` (pnpm dev dependencies under `node_modules/.bin`; a CLI already on `PATH` works without it).

Run its verbs as `uv run clutch <verb>`. Use `clutch meta refresh` to update configured file metadata, `clutch meta check` to report missing, empty or drifted blocks, and `clutch meta fill` to fill missing or empty blocks using a read-only model and refresh drifted blocks without the model. Use `clutch index build` to build the project index and `clutch context suggest <stem>` to suggest context for a ticket. Your host also needs `config.yaml`; start with the [copyable configuration](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-contract.md), or create one with `uv run clutch config init --write` from the CLIs you installed.

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
uv run clutch view status   # show the journal projection
uv run clutch view watch    # show the live text view
uv run clutch view stats    # show health and efficiency figures
uv run clutch view events   # print one line per actionable engine change
uv run clutch view events --once --timeout 300  # wait once for changes as JSON
# Decisions
uv run clutch ticket confirm  # confirm a draft or Reject item
uv run clutch ticket reject   # reject a draft or Reject item
```

## VS Code extension

The [clutch tickets extension](https://marketplace.visualstudio.com/items?itemName=chunkydragon.vscode-clutchwork) (`chunkydragon.vscode-clutchwork`) shows the ticket graph, details, recent steps, Suggestion Box, and stats. Set `clutch.command` when the engine command differs from the default host `.venv/bin/clutch`.

## Guides

The host guides ship inside the installed package; `uv run clutch host docs` prints each local path so agents read the copy matching the installed version.

- [Host run guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-running.md): invocation and operation on a host.
- [Host ticket authoring](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-authoring.md): what to write in a ticket.
- [Host contract](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-contract.md): the config schema and host-facing contract.
- [Local qwen provider setup](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-qwen.md).
- [Gemini provider setup](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-gemini.md).
- [Training data guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-training.md).
- [How clutch works](https://github.com/protus75/clutchwork/blob/main/docs/how-clutch-works.md): how clutch behaves today. Tickets keep it current.

## Developing clutch

This section is for working on clutch's own repository, where every clutch verb runs from the checkout as `uv run clutch <verb>`, as in a host:

    ./dev.py                  # the full suite (unit under clutch.testguard)
    ./dev.py test [args]      # the suite, or named tests (unit under clutch.testguard)
    ./dev.py vscode           # package and install the vscode-clutchwork extension
    ./dev.py vscode-package   # build a VSIX for Marketplace upload

`CLUTCH_PLAN.md` is the frozen record of how clutch was first built. It is history, not a reference.
