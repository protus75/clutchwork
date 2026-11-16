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

Install the provider CLIs you route with `uv run clutch install claude codex` (pnpm dev dependencies under `node_modules/.bin`; a CLI already on `PATH` works without it).

Run its verbs as `uv run clutch <verb>`. Your host also needs `config.yaml`; start with the [copyable configuration](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-contract.md), or create one with `uv run clutch init-config --write` from the CLIs you installed.

## Set up a host

Run `uv run clutch doctor`, then `uv run clutch core` to write the managed conduct block into `CLAUDE.md` for Claude and Qwen Code or `AGENTS.md` for other CLIs. Commit the files. The block gives a chat agent rules for authoring and editing tickets with `clutch new`, `clutch lint`, and `clutch review`, and for supervising a drain. Re-run `core` after upgrading clutch: `drain`, `serve`, and `run` refuse to start while the block is stale.

## The working loop

1. Open Claude Code or Codex in the host checkout, often with auto permissions.
2. Work out a plan with the chat agent.
3. Ask it to turn the plan into tickets. It runs `clutch new`, fills each ticket, and repeats `clutch lint` and `clutch review` until each is clean.
4. Ask it to drain the queue with `uv run clutch drain`, or leave `uv run clutch serve` running to pick up new tickets live. clutch coordinates CLI agents through authoring, implementation, checking, review, and merge.
5. Ask the chat agent to supervise: watch `clutch status` and `clutch watch`, diagnose rejected or blocked tickets from their `tickets/<stem>/` artifacts, fix small ticket problems, and stop with `clutch stop` or `clutch kill` and restart the drain as needed.
6. Use the Suggestion Box as an escape valve. An implementing agent reports second problems in its `second_problems` reply, and the engine files them to the box so the ticket can complete its own goal. Retros and `clutch suggest` from a chat session also file there. An attempt-cap exhaustion puts the run in the Reject queue, where the supervisor may edit and keep a `gate_failed` or `premise_failed` ticket (`docs/how-clutch-works.md` section 6.6); otherwise it waits for `confirm` or `reject`. Triage resolves each message as `declined`, `tombstone` (already covered), or authored into a ticket; an authored ticket can start as a `draft` awaiting a person.
7. Keep the judgment calls: ask the chat agent for a plain-English summary of each draft or held ticket, then run `clutch confirm` or `clutch reject` on each.

In clutch's own repository history, measured on 2026-11-09 from `.clutch/state/box/` and the journal, 32 of 389 Suggestion Box messages (about 8%) became tickets, all as drafts. Of the 31 drafts decided, 24 were confirmed (about 77%) and 7 rejected.

One unattended drain ran about 30 tickets in about 4 hours, many of them triage-authored bug fixes and small features. The practical limit is how fast a person can plan enough work to fill the queue, so planning sessions with the chat agent are where the person spends their time.

For example, ask your chat agent:

- “Help me plan this feature and turn the plan into clutch tickets.”
- “Drain the queue and supervise any held tickets.”
- “Summarize the drafts in plain English so I can decide which to confirm.”

## Commands

```sh
# Setup
uv run clutch init-config  # print a suggested config.yaml
uv run clutch install  # install provider CLIs into the host
uv run clutch update-config  # list current model names per provider
uv run clutch doctor   # inspect host setup
uv run clutch core     # refresh managed conduct files
# Authoring
uv run clutch new      # create and lint a ticket skeleton
uv run clutch lint     # validate tickets without writing
uv run clutch review   # review a committed ticket
uv run clutch order    # edit ticket priority or ordering
uv run clutch suggest  # file an idea into the Suggestion Box
# Running
uv run clutch drain    # run eligible tickets to quiescence
uv run clutch serve    # run the continuous daemon
uv run clutch run      # run one ticket through the pipeline
uv run clutch stop     # finish active work and exit
uv run clutch kill     # stop the engine at a safe point
uv run clutch pause    # ask the engine to pause admission
uv run clutch resume   # ask the engine to release its current hold
# Observing
uv run clutch status   # show the journal projection
uv run clutch watch    # show the live text view
uv run clutch stats    # show health and efficiency figures
# Decisions
uv run clutch confirm  # confirm a draft or Reject item
uv run clutch reject   # reject a draft or Reject item
```

Stop `serve` before `drain` or `run`: each takes the writer lock. See the [host run guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-running.md) for every verb.

## VS Code extension

The [clutch tickets extension](https://marketplace.visualstudio.com/items?itemName=chunkydragon.vscode-clutchwork) (`chunkydragon.vscode-clutchwork`) shows the ticket graph, details, recent steps, Suggestion Box, and stats. Set `clutch.command` when the engine command differs from the default host `.venv/bin/clutch`.

## Docs

- [Host run guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-running.md): invocation and operation on a host.
- [Host ticket authoring](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-authoring.md): what to write in a ticket.
- [Host contract](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-contract.md): the config schema and host-facing contract.
- [How clutch works](https://github.com/protus75/clutchwork/blob/main/docs/how-clutch-works.md): how clutch behaves today. Tickets keep it current.

## Developing clutch

This section is for working on clutch itself. In this repo, run engine verbs with `uv run clutch` and tests with `./dev.py`:

    uv run clutch new STEM [--kind feature|bug|chore] [--evidence FILE...]   # write a ticket skeleton
    uv run clutch lint [STEM...]                         # check tickets
    uv run clutch review STEM...                       # review tickets against merged code
    uv run clutch drain                                  # run every eligible ticket to quiescence
    uv run clutch status                                 # what ran, what is held, total spend
    uv run clutch confirm STEM / uv run clutch reject STEM    # keep or kill a held ticket
    uv run clutch kill                                   # stop a running drain
    ./dev.py test [args]                            # run the test suite

`CLUTCH_PLAN.md` is the frozen record of how clutch was first built. It is history, not a reference.

Every clutch verb is listed in [how clutch works, section 2](https://github.com/protus75/clutchwork/blob/main/docs/how-clutch-works.md#2-commands).
