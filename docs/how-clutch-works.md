<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Maintained description of how ClutchWork behaves today: commands, tickets, stages, gates, failure handling, drain and serve, providers, panels, the Suggestion Box, state on disk, config and the project index
relates: [clutch/docs/host-authoring.md, clutch/docs/host-contract.md, clutch/docs/host-running.md]
owner: engine
verified: 97f3403f
hash: 3def293d16a0745cbc929a9ae04e1d904d7314709362f1e35588eb48b385114c
-->
# How ClutchWork works

This document describes ClutchWork as the code behaves today. It is maintained: a ticket that changes
behavior described here updates the matching section in the same change, and tickets cite its
section headings. `CLUTCH_PLAN.md` is the frozen bootstrap design record; it is history, never a
reference for current behavior. Where this document and the code disagree, the code wins and
this document is fixed.

Related documents: `clutch/docs/host-contract.md` (full config schema and host-facing contract) and
`clutch/docs/host-authoring.md` (what to write in a ticket).

## 1. What clutch is

clutch (CLI Harness for Unattended Pipeline Agents) runs tickets against a git repository (the host): Implement writes the change on a branch,
Check runs mechanical gates, Review has a model judge the diff, and Merge squashes the branch onto
`main`. Failures are harvested, diagnosed, retried within caps, or held for a human.

Two planes meet in clutch:

- **Engine plane** (clutch-owned): how work runs. Ticket grammar, prompt specs (`clutch/specs/`), gates,
  caps, git rules, the journal.
- **Host plane** (repo-owned): what to build. The host's code, docs, config, and the ticket
  content. Host material enters prompts as data, never as instructions.

clutch develops itself: this repo is both the engine and its own first host.

## 2. Commands

[Install clutch](../clutch/docs/host-contract.md#install) and run `uv run clutch <verb>`, including in this repo (global flag `--config PATH`, default `config.yaml` at the checkout root). `./dev.py` (section 2.2) covers only this repo's build tasks.

### 2.1 Verbs

Journal appends take a short-held exclusive `journal.lock` for tail repair, segment roll, and the write.

Exit codes are one contract for every verb: **0** success or quiescence, **1** a non-ok ticket
outcome or a halted/killed run, **2** an engine refusal (bad config, lock held, invalid intake,
journal corruption, provider setup, missing executable, corrupt conduct markers). A refusal
prints `clutch <verb>: <message> -- <what to do instead>`.

| Verb | Lock | What it does |
|---|---|---|
| `context suggest <stem>` | no | Suggest ticket context from the index. |
| `index build` | yes | Build or refresh the project index. |
| `meta refresh [paths]` | commit only | Insert or refresh metadata blocks under configured roots. |
| `meta check [paths]` | no | Report missing, malformed, empty-purpose and drifted blocks. |
| `meta fill [paths]` | yes | Fill metadata using a read-only model. |
| `view watch [--once]` | no | Prints a live text view of the configured host state, refreshing every three seconds unless `--once` is supplied. |
| `view snapshot [--all-merged]` | no | Refreshes the rebuildable journal cache and prints the extension snapshot as JSON, including the absolute state directory and `configPath`. The `snapshot_merged_limit` cap defaults to 100 merged rows; `--all-merged` includes all. |
| `view status` | no | Prints the journal projection, overdue retro and calibration reminders, and any evidence size warning (section 10.3). Read-only. |
| `view stats [--window W] [--json] [--tree]` | no | Prints a read-only health and efficiency projection over a time or ticket window (default `7d`); it is not an authority. |
| `view events` | no | Streams actionable engine changes after a silent baseline until Ctrl-C. |
| `ticket lint [stem ...]` | no | Validates ticket grammar, intake claims, committable bug evidence, the time budget limits (over 30m requires a reason when not split, over 60m always splits, and `stuck` is twice `expected`), and the `drain.max_ticket_minutes` stuck ceiling and graphics judge independence without running tickets or writing files, journal events, or git state. With no stems, checks every ticket except those settled or rejected in the journal; with no journal, checks all tickets. Prints each finding and its fix, then `lint: <valid>/<total> tickets valid`. Exits 0 when valid, 1 for findings, or 2 for a missing named ticket or unreadable tickets directory. |
| `evidence show` | no | Print call envelopes and stored normalized event lines. |
| `evidence schema` | no | Print the JSON Schema for start, end or event records. |
| `evidence renormalize` | no | Rebuild current normalized views from stored raw stdout, preserving older normalizer ids; count skipped calls. |
| `evidence prune --to-gb N` | yes | Take the writer lock and delete oldest eligible blobs to the target; print sizes before and after. |
| `evidence coverage` | no | Print known-event percentages and unknown native types by provider and CLI version, and unknown-major-version skip counts. |
| `evidence captures` | no | List ticket captures or print one by attempt and name. |
| `training export --out DIR [--kinds implement, preference, review, diagnosis, ticket, conflict, triage ...] [--since DATE] [--holdout PCT] [--no-trajectory] [--require-records]` | no | With `--require-records`, exit 2 after export if any requested kind has no records. Triage labels reflect operator overrides of the verdict. Ticket records include an `authored_by` filter; human tickets without a linked author call are omitted. Exports labelled training records from evidence and merged commits; implement records include a tool-call trajectory unless `--no-trajectory` is set, and `file_purposes` for changed paths found in the index. |
| `training eval --route TIER/review --holdout FILE` | no | Replay held-out review records through the selected route and print agreement to stdout only; exit 2 if no held-out review record was scored; no journal, evidence records or engine log. |
| `coverage map` | no | Runs `review.coverage_map.argv` and writes `<state_dir>/coverage-map.json`; exits 0 on success or 2 on refusal. |
| `coverage gate [--gate PATH] [--report PATH] -- <argv>` | no | Runs the unit-test command, then checks its fresh coverage report against `test-gate.toml` (default report `coverage.json`; paths relative to the invocation directory). Returns the command’s nonzero exit code, or 0 on coverage pass, 1 on threshold failures, or 2 for a refusal. |
| `host doctor` | no | Checks venv, config load, git, lock probe, journal readability, core check, and parallel provider concurrency, graphics judge independence and panel provider concurrency checks. Warns when evidence exceeds its configured threshold or retro or calibration is overdue, without failing. Git is not probed if config fails to load. Exit 2 on any failure. |
| `prompt <diagnose\|running\|review> <stem>` | no | Prints an operator prompt for an existing ticket without writing state; `diagnose` selects the running prompt for a live running ticket; `review` audits the ticket against merged code and every confirmed, unmerged ticket. |
| `host core` | no | Rewrites the managed `clutch:core` block in each routed agent's conduct file (section 12). |
| `provider probe [PROVIDER...]` | no | Probe declared providers and models; exits 1 when any probe fails and 2 for an undeclared provider name. |
| `provider install [PROVIDER...]` | no | Installs named provider CLIs into the host project as pnpm dev dependencies, or with no names reports each adapter's package, location, and version. |
| `config update` | no | Lists the model names each declared provider's CLI serves and compares them with `models_by_tier` and routing candidates; exit 0 when every name is current, 1 when a suggestion was printed. Writes nothing. |
| `config init [--write]` | no | Prints a suggested `config.yaml` built from the provider CLIs found (project or system) and the model names they serve, validated with the real loader; `--write` publishes it when no `config.yaml` exists. Undetermined models are written as `OPERATOR-SETS-THIS`. |
| `help [command ...]` | no | Prints command help and examples from each command parser in `clutch/__main__.py`; `--help` or `-h` before a command does the same. Exits 0, or 2 for an unknown command. |
| `host docs` | no | Prints the installed host guide paths and their purposes. |
| `config migrate` | no | Migrates a `schema_version: 0` config to the current schema. |
| `ticket new <stem> --kind feature\|bug\|chore\|graphics` | no | Writes `tickets/<stem>/ticket.md` with section placeholders for the selected kind (default `feature`) and `state: draft`, and lints it; intake keeps authored `state: draft`, stamps `confirmed` only when the state line is absent, and drafts are confirmed with `clutch ticket confirm`. Bugs include `## Regression`, require `--evidence <file>...`, and copy those files into `tickets/<stem>/evidence/`. Refuses a bad, reserved, or existing stem, or unknown kind (exit 2); successful authorship exits 0. |
| `ticket order <stem> [--priority P0\|P1\|P2\|P3] [--runs-before [stem ...]]` | no | Validates and edits priority and/or runs-before ordering in the working tree; a bare `--runs-before` removes the section. Refuses a running ticket while an engine is live, and settled, rejected, missing or invalid tickets. An interrupted run with no live engine is editable. Intake commits the edit. |
| `ticket review <stem>` | commit only | Only the named ticket's pending changes are committed through intake first; other pending tickets are left untouched. Reviews the committed ticket against merged code and journals its verdict and ticket blob SHA. A ticket with an unmerged dependency gets a provisional review that is printed but not journaled, so the drain reviews it again before its first run. Refuses missing, intake-failed, settled, or rejected tickets without a model call. Prints findings and exits 0 on approve, 1 on snag or rma. |
| `engine run <stem>` | yes | Reconciles orphans, intakes only the named ticket’s pending changes, then drives that ticket through every stage. Refuses a stem that failed intake, is missing, invalid, merged, not `confirmed`, or has unmerged dependencies. |
| `engine drain [--detach] [--parked STEM] [--deadline ISO]` | yes | Runs every eligible ticket to quiescence (section 7.1); `--detach` starts its own session and appends to `<state_dir>/drain.out`. The self-upgrade re-exec sets `--parked` and `--deadline`, not the operator. |
| `engine serve` | yes | Runs the continuous daemon until `engine kill`, `engine stop`, or a signal (section 7.2). |
| `engine retro` | try | Runs a retro report only when invoked, now or queued on the running engine (section 9.5); refuses while a non-engine holder has the lock. |
| `engine calibrate` | no | Runs only when invoked. Reads the last `calibration.every` completed Implement calls from the journal, measuring minutes from each `effect_intent` to `effect_completion` and taking provider and model from completion `cost`. Reads expected minutes from each `tickets/<stem>/ticket.md`; calls without a readable estimate are left out. Journals one `estimate_calibration` signal and prints rows with the run count, median estimate, and median and 90th-percentile actual minutes per provider and model. |
| `box suggest <summary>` | no | Files an idea straight into the Suggestion Box. |
| `box issue --class <class> <title> --body FILE` | no | Prints a link with title and body only, a version footer, and the Repository URL from package metadata; scrubs configured secrets when config loads. Refuses an unknown or missing class, unreadable or empty body, or a link over 3,000 bytes. Takes no lock, writes nothing, opens no browser, and submits nothing. |
| `roadmap status` | no | Prints per-release merged, authored, ready, and blocked row counts and the last gate result, followed by `next:` and `waits:` lines for held rows, including declined messages, rejected stems, drafts, and spent re-files. Read-only. |
| `roadmap merged [stem ...] [--release R [--priority P ...]] [--since TAG --at-least N [--source S] [--unattended] [--parallel]]` | no | Checks named roadmap rows and release rows for settlement, and counts distinct first-parent ticket merges since a tag with optional source and unattended filters. With `--parallel`, it counts only merges whose run overlapped another run and fails when any such ticket spent its conflict-rerun limit. Reports a draft without journal state as a draft. Prints unmet conditions or success; exits 0 when all hold, 1 otherwise, and 2 on refusal. Writes nothing. |
| `roadmap gate <release>` | no | Runs the release's fenced `gate` block from `docs/roadmap.md` section 8 in order from the checkout root, stopping at the first failed command. Prints command results and a verdict, journals one `roadmap_gate` signal, and exits 0 when every command passes, 1 on failure, or 2 on refusal. |
| `roadmap accept <release>` | commit only | Reviews the release’s merged rows together against its theme, ship gate, and owning plans through a read-only model call. Refuses a missing or dirty roadmap, unknown release, missing section 1 row, or a judge that implemented most of the release when another provider is declared. Appends new P1 gap rows to this release or deferred rows to the next in one `clutch(roadmap): accept <release>` commit. Exits 0 with no partial or unmet promises, 1 for those gaps, and 2 on refusal; takes no writer lock and works while serve runs. |
| `roadmap author [--ahead N]` | yes | Refuses a dirty roadmap, strikes merged rows and links existing tickets in individual commits, then files ready rows in release order: the current release (the `pyproject.toml` version as `<major>.<minor>.0`) first, then rows that earlier releases left unfinished, then later releases, until N rows are open (default 2). Settles recorded author verdicts through triage without a triage model call and links authored tickets with `clutch(roadmap): author <stem>` commits. Reports hand-test and bug-evidence waits. |
| `box triage [id ...]` | try | One sequential pass over named pending messages, or all pending messages; submits to a running engine for its next idle point (section 9.2). |
| `release bump --minor\|--patch` | yes | Takes the writer lock; refuses dirty `pyproject.toml`, `uv.lock`, or `CHANGELOG.md`; previews the next version with uv and refuses an existing `v<version>` tag before writing; bumps with uv, writes a new `CHANGELOG.md` section, commits all three files as `release: <version>`, and creates an annotated tag on the returned commit sha, then journals a `release` signal. Prints `release: tagged v<version> at <commit sha>` and exits 0; publishes nothing. |
| `release ship` | yes | Gates the current release, bumps and tags it, journals the release, optionally publishes, and runs configured packages. |
| `release publish` | yes | Takes the writer lock, checks the tracked tree is clean and the version tag is at HEAD, builds into `state_dir/dist`, and lists artifacts; uploads only with `release.publish: true` and never bumps. |
| `box dismiss <id> ...` | yes | Dismiss named messages without a model call. |
| `prompt host <name> [stem]` | no | Render a host-owned prompt. |
| `prompt list` | no | List engine and host prompts and report invalid host files. |
| `prompt box <id> ...` | no | Print a prompt for discussing named box messages. |
| `prompt drain-loop` | no | Print the supervising drain-loop prompt without writing state. |
| `prompt drafts` | no | Print an assessment prompt for all committed drafts awaiting a verdict. |
| `prompt author <stem>` | no | Print the hand-authoring prompt for one ticket from its roadmap row or a request; the ticket need not exist yet. |
| `prompt roadmap` | no | Print the roadmap creation and maintenance procedure; follow with `clutch roadmap status` and `clutch prompt plan-ticket-drain`. |
| `prompt plan-ticket-serve` | no | Print the unattended roadmap kickoff prompt for the continuous daemon with explicit Sonnet selection for Claude subagents, without writing state. |
| `prompt plan-ticket-drain` | no | Print the kickoff prompt that runs the roadmap to completion unattended, authoring its rows as tickets and draining them, with explicit Sonnet selection for Claude subagents, without writing state. |
| `engine pause` / `engine resume` / `engine kill` / `engine stop` | try | With a running engine, publish a control request to it (section 7.3). With a non-engine holder, refuses and asks the operator to wait. With none: `engine kill` and `engine stop` refuse (exit 2); `engine pause`/`engine resume` print "nothing running". |
| `ticket confirm <stem> [--yes|--extension]` | try | A person at a terminal answers `y` to keep (or uses `--yes` to skip the prompt): promotes a draft to confirmed, keeps a Reject-queue item (section 6.6). Same-content repeat keeps are refused for command-line confirms; the extension uses `--extension` to allow them. Intakes only the named ticket’s pending changes; with drain or serve running, does so before publishing the verdict to the engine; refuses while a non-engine holder has the lock. |
| `ticket reject <stem> [--yes|--extension] [--reason TEXT]` | try | A person at a terminal answers `y` to kill (or uses `--yes` or `--extension` to skip the prompt): stamps the ticket `rejected` (section 6.6). Refuses settled stems. Intakes only the named ticket’s pending changes; with drain or serve running, does so before publishing the verdict to the engine; refuses while a non-engine holder has the lock. |

### 2.2 `./dev.py`

The repo's one dev command; standard library only, every task through `uv`.
`./dev.py test` runs the suite in parallel on the available cores by default.
Each test has a 120-second hard limit.
Test temporary files go to the gitignored `.test-tmp/` folder in the checkout, never `/tmp`.
Tests live in `tests/unit/` (disk only under `tmp_path`, no network or process; run under `clutch.testguard`) and
`tests/integration/`. Integration test files carrying the `disk_io_skip` marker are skipped until rewritten onto in-memory fakes. Run one suite with `./dev.py test tests/unit` or
`./dev.py test tests/integration`.
A unit test file may share its name with an integration test file.

| Subcommand | Runs |
|---|---|
| (none) | `uv run pytest -q -p clutch.testguard tests/unit`, then `uv run pytest -q tests/integration`; a unit failure stops before integration |
| `test [args]` | With no args, the same as (none); otherwise pytest with those args, adding `-p clutch.testguard` when at least one test path is named and every test path is under `tests/unit` |
| `visual-baseline` | runs `uv run python -m eval.visual_harness run` to score the visual judge and record its verdict |
| `vscode-package` | packages the current manifest version into `dist/vscode-clutchwork-<version>.vsix` with the clutch `Built for` stamp inside the VSIX, restores the README, and prints the Marketplace upload page; an existing file is kept without rebuilding; under WSL also prints the Windows path |
| `vscode` | bumps the patch version in `vscode-clutchwork/package.json` (VS Code keeps an extension's old icon until its version changes), packages it with `npx @vscode/vsce`, and installs it with `code --install-extension --force`; reload the window to load it |

To release the extension, bump `version` in `vscode-clutchwork/package.json`.
`release ship` runs `./dev.py vscode-package` after tagging; it stamps `Built for` only in the VSIX and restores the README. An existing `dist/vscode-clutchwork-<version>.vsix` is kept without rebuilding, so bump `version` in `vscode-clutchwork/package.json` before ship to keep a new file. Upload the VSIX manually on the [chunkydragon management page](https://marketplace.visualstudio.com/manage/publishers/chunkydragon).
Under WSL, paste the printed Windows path into the upload dialog.
Choose New extension for the first release and the extension's Update action for subsequent releases.
The Marketplace refuses a version it already holds.

`vscode-clutchwork/` is an operator-only VS Code extension: an Activity Bar view of every ticket as an
SCM-style graph (blocked, queued, running, merged) with a detail pane. A line between ticket rows means a dependency; merged rows show their history line. Running and queued rows show their priority. Its Activity Bar badge shows the queued and running ticket count while the engine is alive, or the blocked and queued count while it is stopped, and is hidden when the count is zero. The Tickets view's More Actions
menu holds Ticket lifecycle, which opens `vscode-clutchwork/media/ticket-lifecycle.svg`, a hand-drawn diagram of ticket states, Ask Claude: drain loop, which opens a Claude Code chat with `prompt drain-loop`, and Ask Claude: prompt…, which lists every engine and host prompt.
Each unsettled ticket's detail shows a `Shared fence` entry listing its fenced paths that another unsettled ticket also fences, with those tickets.
Every verb-backed menu item is on exactly when its verb’s admission function admits the row, through the closed table in `clutch/observe.py`; an admitted action that needs the writer lock is locked while a holder is alive. Confirm and Reject use the shared verdict predicate without lock gating. The Ask items are extension-only.
The Tickets view’s play button and Engine… picker start drain detached. The picker also runs serve, stop, kill, status, or retro. Its start/stop icon follows the snapshot engine flag, which is true only while a drain or serve holds the lock; `clutch.playAction` selects drain or serve for starting. Open config.yaml, also in More Actions, opens the snapshot’s `configPath`. Recent Steps row kinds are the closed vocabulary `STEP_KINDS` in `clutch/observe.py`, and a test fails until each step in it has its own icon. An unknown kind renders as a warning row instead of breaking the view. Recent Steps opens a step’s file when it exists; an Author row opens its Suggestion Box message, authored ticket, or decision record. The collapsed Stats view shows health figures for the window configured by `clutch.statsWindow` (default `7d`). The Suggestion Box view lists messages, supports multi-selection and manual triage or dismissal, and shows message details alongside tickets. `clutch view snapshot` builds journal facts once per call from the journal cache and in-memory history, and checks the drain holds only for stems that can hold; `clutch/graph.py` computes the graph layout for the extension to draw. The engine never runs the extension.

The `clutch.command` setting supplies the command and arguments the extension runs the engine with; its default is `.venv/bin/clutch`, resolved from the workspace folder.

Extension help comes from `clutch/help.py` through the snapshot; each surface shows what it is and a link to its documentation, and `clutch.help` lists every topic. `clutch.refreshSeconds` sets the timed refresh interval (default 15 seconds); 0 disables the timer while file-change refreshes continue. `clutch.unavailableMenuItems` controls whether unavailable ticket actions are disabled (the default) or hidden.

## 3. Tickets

### 3.1 Files and fields

A ticket is `tickets/<stem>/ticket.md`. The stem matches `^[a-z0-9][a-z0-9-]{1,63}$`;
`decisions` and `retro` are reserved. `clutch/tickets.py` owns the format; `clutch/docs/host-authoring.md`
says what goes in each section.

Frontmatter fields that drive behavior:

- `state`: `draft` (awaiting `clutch ticket confirm`; intake keeps an authored `state: draft` and stamps `confirmed` only when the state line is absent), `confirmed` (dispatchable), `rejected`, `merged`.
- `source`: `human` (hand-written), `box:<class>` (written by the Author stage), `seed`
  (historical bootstrap tickets; nothing writes it now).
- `kind`: `feature`, `chore`, `graphics`, or `bug` (a bug must carry `## Regression` and evidence,
  section 5.2).
- `priority` (P0-P3), `## Depends on`, and the optional `## Runs before` section order the queue. `agent_tier` / `agent_effort` pick the
  starting model capability (section 6.4). `gate_bypass` softens named engine gates for this
  ticket (section 5.3).

Non-settled tickets must carry a `## Boundary contract` section; tickets with state `merged` or
`rejected` are exempt. Intake and `clutch ticket lint` check its presence and basic shape. The
[authoring guide](../clutch/docs/host-authoring.md) owns its fields, dispositions and `none` reasons.

### 3.2 Intake

`engine drain` and `engine serve` intake every pending ticket; `ticket review`, `engine run`, `ticket confirm`, and `ticket reject` intake only the named stem, including before verdict handoff to a running engine:

- It reads status, checks for stray staged paths, and commits under one `commit.lock` hold.
- It finds new or modified `tickets/<stem>/ticket.md` files in the working tree (`git status`).
- A new hand-written stem must be `draft` or `confirmed` and must not claim a machine `source`;
  intake stamps it `source: human`, keeps an authored `state: draft`, and stamps `confirmed` only when the state line is absent; confirm a draft with `clutch ticket confirm`.
- Bug evidence is checked as the authoring guide's [Evidence](../clutch/docs/host-authoring.md#evidence) section states.
- Each ticket that lints clean is committed with its new or changed regular, non-symlink evidence
  files as `clutch(<stem>): ticket` and journaled as
  `ticket_intake`. A ticket that fails lint stays on disk uncommitted, and the refusal names the
  fix.
- If anything other than pending ticket files and their committable evidence files is staged,
  intake refuses entirely; staged evidence deletions and symlinks must be unstaged first.
- An existing stem is never restamped.

So writing a ticket file is enough: the next `drain` commits it. After intake,
dispatch pins the committed `ticket.md` blob on `main`. Before each stage and
merge admission, both main's committed blob and its checkout bytes must still match. A committed
or uncommitted edit during the run stops it with `ticket_changed` and holds it for an operator.
Engine artifacts such as `run.md` and `checks.json` do not affect this identity.

Intake, `ticket lint`, `ticket new`, and requisition review also check that the Regression command names
a carried path, every carried prefix is fenced, and a fenced file with a positive
`test-gate.toml` file floor has a fenced path under `tests/unit/`. These authoring checks
do not change scan or merge admission. Requisition returns a snag without a model call
when ticket lint fails. A malformed coverage gate is a lint finding.

### 3.3 What the engine writes back

Stages write into an outbox in the ticket's worktree (`tickets/<stem>/` inside it). The lift
copies each selected new or changed artifact to the main checkout's `tickets/<stem>/` and commits it on `main`
as `clutch(<stem>): <kind>`, once per attempt (an Effect, section 10.2). `ticket.md` is never
lifted from a worktree: the agent cannot edit its own ticket. Each lift takes only its named artifact,
skips symlinks without error, and refuses a file over 256 KB.

| Lift kind | File |
|---|---|
| `run-record` | `run.md` (the Implement run record) |
| `checks` | `checks.json` (Check's report), plus registered report artifacts |
| `review` | `review.md` |
| `harvest` | `attempts/<n>/harvest.json` |
| `harvest-rework` | `attempts/<n>/harvest.json` when Rework itself failed |
| `diagnosis` | `diagnosis.json` |
| `rework-proposal` | `rework.md` (the supervisor's refused or escalated edit) |

Other engine commits on `main`: `ticket` (intake), `confirmed`, `rejected`, `rework`, `clutch(decisions): <id>` (a triage decision record), `clutch: retro NNNNNN`, `clutch(<stem>): undo refused rework`, and the squash merge itself. Check's `clutch(<stem>): autofix` and `clutch(<stem>): meta` commits land on the ticket branch, not on `main`.

## 4. A ticket's run

`runner.drive` reviews committed ticket content before Implement unless the journal already records an approval for that blob. It then takes the ticket through Implement, Check, Review, then Merge.

### 4.1 Worktree

Each attempt gets a worktree at `<worktree_root>/<stem>` (default
`<state_dir>/worktrees/<stem>`) on branch `<stem>`. A retry after a Check or Review failure
reuses the branch rebased onto `main`; if the rebase fails, it starts fresh. Every other attempt
starts fresh from `main`, removing any old worktree and branch first. Scratch worktrees under `.base/` and `.regression-base/` are
created at the merge base for base-red reruns and the bug gate, and removed after.

### 4.2 Implement

The `implement` prompt (`clutch/specs/implement.md`) gets the ticket text, its `## Context` files plus
`config.context_files`, and a "Prior attempts" block (last terminal, findings, diagnosis lessons,
log tails) when this is a retry. A conflict rerun marker also adds the discarded run record, approval findings, and non-conflicting prior diff as reference material. Context entries may select a Python top-level definition or
assignment (`path.py::Name`), a class method (`path.py::Class.method`), or a Markdown heading
(`path.md#Heading`), including its subheadings. Heading text may start with the selector followed
by a space. Selectors must resolve uniquely, and a file cannot be listed both whole and by section.
Ticket Context files are UTF-8 text; lint renders each entry exactly as Implement does.
`config.context_files` remains whole-file. The model works in the worktree with write access and replies:

- `ok`: it committed the change.
- `already_satisfied`: every acceptance criterion already holds on `main`; Check must prove it
  with green Verification on an empty diff.
- `incomplete`: work stopped before it was committed, without an established ticket defect.
- `premise_failed`: the ticket cannot be done as written; findings say why and name every forced
  file outside the scope fence separately.

Implement runs each Verification command whole and in sequence and reports that final result.
Implement runs its Verification commands and lint and format on changed files, leaving the full suites, coverage gates and base comparisons to Check.
Failures reproduced on the base commit are reported as second problems rather than `premise_failed`.
Implement updates documentation statements the diff makes false inside the scope fence in the same commit.

The Implement prompt also carries its test rules: suite placement, flaky tests, and coverage thresholds and test time budgets. The unit and integration suites are defined in the authoring guide's [Unit and integration tests](../clutch/docs/host-authoring.md#unit-and-integration-tests) section.

The Implement prompt asks for each assertion to name the likely wrong implementation it rules out
and use a fixture that gives a different value under that version. For filter, exclusion, ordering
or tie-break assertions, the target row must pass every other filter and its derived columns must
give the intended role; Implement applies the wrong version once to confirm the test fails, then
restores the code. It forbids asserting values a
default, zero, or shared fixture would produce anyway, and asks retries to check every assertion
this way, not only the one named by a finding.

The engine writes `run.md` from the reply and lifts it. Each `second_problems` entry is filed to
the Suggestion Box as a `suggestion`.

### 4.3 Check

1. When Implement replied `ok` and `review.autofix` is nonempty, runs configured autofix commands on existing changed files outside `tickets/` matching each entry's `files` patterns and commits changes. Refreshes metadata for changed files under `meta.paths` and commits rewrites before reporting blocks needing review.
2. For graphics `generate` tickets, Check returns `visual_undecided` before judging unless the latest `visual_baseline` is GO for the current judge routing and spec major. Otherwise, Check judges candidates separately per artifact and commits all selected images in one select commit, or returns `visual_undecided` without a select commit.
3. Runs each `## Verification` command in the worktree (provider keys removed from the
   environment, timeout = the ticket's stuck budget, output spooled to `check/verify-NN.txt`).
4. A failing command is rerun at the merge base. If it also fails there and names no path present in the branch but absent at the merge base, it is **base-red**: a
   pre-existing failure, excluded from the verdict and filed once to the Suggestion Box. A command naming a branch-only path is never base-red.
5. Runs the render command for graphics `command` tickets, then the engine Check gates (section 5.1).
6. Runs triggered host checks in config order, attributing failures also red at base to main.
7. Writes and lifts `checks.json`.

A hard gate failure ends the attempt `gate_failed`. Soft failures are recorded and the run
continues. `already_satisfied` stops here: there is no diff to review.

### 4.4 Review

The `review` prompt (`clutch/specs/review.md`) gets the ticket, the branch diff, and the previous review's
findings when it snagged, in a read-only session. It reports every defect in one pass, listing each
instance of a repeated flaw separately and marking findings that remain open. Verdicts: `approve`, `snag` (findings: `logic`, `acceptance`, `scope`, `leak`), or `rma`
(the ticket itself is wrong). `review.md` records the verdict and the reviewed branch head
(`reviewed_sha`). Review also snags a stale or missing doc update. Only `approve` continues;
`snag` and `rma` end the attempt `gate_failed`. A `findings-union` panel on the review route runs N member reviews and writes one combined `review.md`.

### 4.5 Merge

`run` and `drain` merge inline through `merge.merge`, a thin call into the queue’s admission; `serve` uses the merge queue (section 7.2).
For a nonempty branch, if main changed only paths under `tickets/` since the reviewed
merge base, the Check reruns and host checks are skipped; Merge gates still run.
Inline merge:

1. Rebases the branch onto current `main`. A refused rebase is `gate_failed`.
2. Re-runs Verification (and the bug regression) on the rebased candidate.
3. Runs the Check gates, Merge gates and triggered hard host checks (section 5.1). Any hard failure refuses the merge;
   `main` is untouched and the branch is kept.
4. Squash-commits onto `main`: subject `clutch(<stem>): <first Goal line>`, trailers
   `clutch-ticket: <stem>` and `clutch-reviewed-sha: <sha>`. Journals `to: merged`.
5. Removes the worktree and deletes the branch.

Inline merge does not run merge strategies or the conflict ladder; a rebase
conflict is simply refused.
- Before squash, `dirty_checkout` refuses tracked main-checkout edits overlapping the branch and staged changes outside the branch; commit or revert overlapping edits, or commit or unstage staged changes, and retry.

## 5. Checks

### 5.1 Engine gates

`meta_drift` is soft by default; every other engine gate is hard.

**Check gates** (on the branch head):

| Code | Fails when |
|---|---|
| `meta_drift` | After Check fills empty or drift-flagged purposes and refreshes headers, changed metadata remains malformed or has an empty purpose. |
| `scope_fence` | A changed file is outside `## Scope fence` (the stem's own outbox is exempt, except `ticket.md`). |
| `verification` | A Verification command fails and was green at the base; or `already_satisfied` came with a diff; or a required report is missing or invalid. |
| `run_record` | `run.md` is missing, or lacks its six fixed sections in order, or has an unknown outcome. |
| `diff_budget` | More than 1,500 inserted lines: split the ticket. |
| `core_drift` | A routed conduct file's managed `clutch:core` block does not match the current template (section 12). |
| `bug_evidence` | For `kind: bug` only: see section 5.2. |
| `image_quality` | Judges command-mode graphics render artifacts with deterministic image checks. |

**Merge gates** (on the rebased candidate, at admission):

| Code | Fails when |
|---|---|
| `ticket_schema` | The ticket on `main` no longer lints. |
| `post_rebase_regate` | The branch commits anything under `tickets/`, or the rebase was refused. |
| `correctness_review` | `review.md` on `main` is not an `approve` of the branch head that was reviewed. |

### 5.2 Bug tickets

A `kind: bug` ticket must prove the defect: at least one file under `tickets/<stem>/evidence/`;
a `## Regression` command that prints `{"regression_result": "pass"}` with exit 0 on the branch
head, and `{"regression_result": "defect"}` with a non-zero exit on the merge base with the
carried test or fixture files copied over it. Only files under `tests/`, `test/`, `fixtures/`, or
`fixture/` can be carried. The authoring guide's [Bug tickets](../clutch/docs/host-authoring.md#bug-tickets) section explains the protocol for authors, and its [Evidence](../clutch/docs/host-authoring.md#evidence) subsection says which ticket reads refuse a bug without evidence. The Check gate still verifies the regression proof.

### 5.3 Severity and bypass

- `review.gate_severity` in config can make an engine gate soft for every ticket.
- A ticket's `gate_bypass: [{code, reason}]` makes the named engine gates soft for that ticket
  only; bypassed codes are recorded in `checks.json`.
- A soft failure is recorded with its findings and does not stop the run.

### 5.4 Host checks

A host declares its own checks in `review.mechanical` (`code`, `argv`, `trigger: always` or a
list of path prefixes, `severity: hard | soft`). Check runs every triggered entry in order;
prefixes match an equal path or a descendant. A base-red failure is filed and excluded from
Check and retry findings. Soft failures are recorded without blocking. When main changed a path
outside `tickets/` since the reviewed merge base, or the branch diff is empty, inline merge reruns
triggered hard entries on the rebased candidate. The `serve` merge queue runs the hard entries
named in `merge.safety_checks` at safety and every always/hard entry at integration under the
same conditions. Otherwise only the Merge gates run, alongside the queue safety gates; see
sections 4.5 and 7.2.1. All use one shared command runner, and `triggered_hosts(tier=...)` selects entries for Check and both merge tiers. The runner puts the directory of the engine’s own Python interpreter first on each command’s `PATH`, so a check argv naming `clutch` runs the installed engine, not the worktree’s code.

An entry may declare a worktree-relative `results` file written by `clutch.testreport`. Check
clears it before each run and reruns a failing command with failed tests once. Edited flakes
block; unedited flakes are quarantined unless the cap is full. Quarantined unedited failures
do not block. Check releases a passing quarantined test when its resolved fix has merged or its report was declined; declined releases use `declined:<box_id>` as the fix identity and need no merge.
Missing or invalid results after a successful run or rerun fail the entry. Check records command wall time, outcome counts and slow tests from the first run, bounded by `slow_test_seconds` (default 1.0) and `slow_test_limit` (default 100). Readable coverage records the repository percentage and percentages for changed files. With a declared coverage.py JSON report, Check runs `flake_coverage_argv` for each flake whose test file is unchanged, and counts it as edited when executed lines include a changed line or a line adjacent to a pure deletion. Missing configuration or an invalid report fails classification.


## 6. When a run fails

### 6.1 Order of handling

`already_satisfied` is settled after Check proves it: `runner.drive` journals its stage and
`already_satisfied` reason, then removes the worktree. It makes no diagnosis call, draws no cap,
and records no dispatch or Reject routing marker.

After any other non-ok terminal, `runner.drive` does, in order:

1. **Harvest** the attempt (section 6.2).
2. **`ticket_changed`** journals a `gate_failed` terminal routed to the Reject queue, removes
   the worktree, and stops (section 6.7), skipping the cap, Diagnosis, and Rework steps.
3. A provider **drought** or quota result parks the stem with no diagnosis (section 8.3).
4. A failure reaching `caps.attempts` goes straight to the terminal, routed to the Reject queue
   with reason `attempts cap spent`, skipping the cap draw, Diagnosis, and step 7's Rework, then going to the dispatch and supervisor steps.
5. `infra_error` / `timeout` draw the `infra` cap; `premise_failed` draws `premise_bounce`, except a requisition-stage snag ends before dispatch and draws no cap (section 6.7); `incomplete` draws neither cap.
6. **Diagnosis** (section 6.3), unless the outcome is `budget_exceeded` or an over-bound render.
7. **Rework** if diagnosis said `split`, or the render was over bound (section 6.5).
8. Handle dispatch and supervision:
   - **8a.** Decide the dispatch (retry, escalate, or the Reject queue).
   - **8b.** Run the supervisor step (section 6.6) when it applies.
   - **8c.** Journal the terminal, then any supervisor keep.
9. Remove the worktree.

### 6.2 Harvest

`attempts/<n>/harvest.json` records the stage, terminal, findings, diff stat, the last 4,000
characters of the stage logs and of the provider event stream, time, and cost. It is lifted as
`clutch(<stem>): harvest` and feeds the next attempt's "Prior attempts" block. When training data is enabled, harvest also writes a `clutch.evidence.attempt/1.0` manifest with the filtered diff and check output blobs under `evidence/attempts/<stem>/<run_seq>/<attempt>.json`. A harvest failure is
journaled and never blocks the terminal.

### 6.3 Diagnosis

The `diagnose` prompt (`clutch/specs/diagnose.md`) reads the ticket, terminal, harvest, and run record
and replies with a verdict and 1-5 lessons:

- `retry`: run again with these lessons.
- `escalate`: run again with more capability (section 6.4).
- `split`: Rework the ticket into smaller ones.
- `reject`, `abandon-human`: send it to the Reject queue.

A `majority-verdict` panel on the diagnose route runs N member diagnoses and writes one `diagnosis.json` from the majority verdict, breaking ties by `escalate`, `abandon-human`, `split`, `reject`, `retry`.

An over-long lesson is trimmed at a word boundary and its index recorded in `diagnosis.json` `trimmed_lessons` rather than refused.

If a cap is already spent or the worktree is gone, the verdict is a mechanical `abandon-human`
with no model call. If the worktree exists, `diagnosis.json` is lifted and a `diagnosis` signal is journaled; if it is gone, no `diagnosis.json` is written or lifted and only the journaled `diagnosis` signal records the mechanical verdict.

### 6.4 Caps and escalation

Caps bound how much one ticket can fail over the stem's **lineage**: every event since the
last operator keep or supervisor keep (`reject_verdict keep actor: supervisor`). Editing `ticket.md` never resets a cap; only an operator `ticket confirm` or a supervisor keep does.
Machine keeps never reset counts. Draws are journaled `cap_consumed` events, except `attempts`,
which counts failed terminal `state_transition` events directly and journals no cap draw.
Conflict rerun signals are counted separately, with a limit of 2 per lineage; they never draw `retry` or count as failed attempts.

| Cap | Default | Drawn by |
|---|---|---|
| `attempts` | 5 | total failed attempts per lineage |
| `diagnosis` | 3 | each diagnosis call |
| `retry` | 3 (never above `diagnosis`) | each drain or serve re-offer, except after a `premise_failed` without escalation, a provider drought, a `conflict_rerun` terminal, or an `infra_error` or `timeout` that carries no escalation rung |
| `infra` | 3 | each `infra_error` or `timeout` (not droughts) |
| `premise_bounce` | 1 | each `premise_failed` (not over-bound renders or `requisition` snags) |
| `quarantine` | 5 | flake quarantine size |
| `supervise` | 2 | each supervisor keep; counted since the last operator keep, so supervisor keeps never reset it and it never routes a stem |

Failed attempts are `gate_failed`, `premise_failed`, `incomplete`, `infra_error`, and `timeout` terminals.
A `conflict_rerun` terminal, a requisition-stage `premise_failed`, an `infra_error` with reason `provider_drought`, `budget_exceeded`, an `abandoned` reap,
settled terminals, and `rejected` do not count. The failure reaching `caps.attempts` is itself
routed with reason `attempts cap spent`, without another diagnosis or rework call; a `gate_failed` or `premise_failed` that `runner.drive` or merge-route `TicketWriter.consume_result` routes this way still meets the supervisor step (section 6.6). Terminal routing also counts a pending failure after a published Rework
update or escalation and leaves the published ticket text intact. A published split still retires
its parent. The drain report shows the failed-attempt total, for example `attempts cap spent (5/5)`.

A spent cap, or a `reject` / `abandon-human` verdict, routes the stem to the Reject queue.
`escalate`, an Implement `premise_failed` whose Diagnose verdict is `retry`, or the same failure reason three times running, moves the stem up one **rung**: the
next higher tier whose Implement model differs, else one effort level higher. At the top rung
the stem goes to the Reject queue.

### 6.5 Rework

The `rework` prompt (`clutch/specs/rework.md`) proposes `update` (rewrite this ticket), `split` (two or
more new stems), or `escalate`. Each proposal is validated in a scratch worktree and reviewed by
`requisition_review`. Accepted proposals are committed as `clutch(<stem>): rework`. A split
journals `supersedes` and retires the original: its dependents wait on the successors.

Supervisor mode supplies a `supervise` trigger and diagnosis lessons and permits update or escalate. Its allowed-edit gate refuses splits, unchanged updates, changed goals, and dropped acceptance criteria, ending the call before review. On `gate_failed` the result carries the last refused proposal.

### 6.6 The Reject queue, keep and kill

Keep and kill work while serve runs.

The Reject queue holds stems whose latest terminal was routed there, plus stems the drain finds
with a spent cap at quiescence. `view status` lists them.
Settled stems (`merged` and `already_satisfied`) never await a verdict, even when a historical
terminal carries a Reject routing marker. `ticket reject` refuses settled stems.

- **`ticket confirm <stem>` (keep)** journals `reject_verdict keep actor: operator`. That resets the
  lineage, so every cap starts over. A second command-line keep at the same ticket content is refused: edit the
  ticket first. The extension uses `--extension` to keep unchanged content.
- **`ticket reject <stem>` (kill)** stamps `state: rejected`, commits it, and files one Suggestion Box
  `failure_report` per confirmed ticket that depended on it ("re-wire, re-scope, or reject it").
  Those dependents stay blocked.
- **Supervisor keep:** inside `runner.drive` and merge-route `TicketWriter.consume_result`, a `premise_failed` routed to the Reject queue, or a routed `gate_failed` with a spent cap, meets supervisor-mode Rework with the lineage's diagnosis lessons. It needs a worktree and budget below `caps.supervise` (default 2, counted since the last operator keep). It excludes `ticket_changed` and `abandoned` (operator decisions), provider/runtime failures (`infra_error`, `timeout`, `invalid_artifact`, `incomplete`, or provider drought, which ticket edits cannot fix). The idle step also takes attempts that already requested Rework, using the `sup` key scope so their Effect keys do not replay. The serve idle point before dispatch and drain between tickets also run this step for Reject-queue stems, including legacy `reject_arrival` entries, with no attempt since the last operator keep. They lazily prepare providers only for eligible stems and use a detached worktree from `main`, removed and pruned through git after the step. The idle hook journals no terminal. Every attempt journals one `supervisor_attempt` signal with the stem in its body before Rework and, for a terminal-path attempt, before the terminal, whether approved, refused, or escalated. On a terminal path a reviewed update publishes before the terminal; after the terminal, a `supervise` draw and `reject_verdict keep actor: supervisor` with the new ticket blob start a fresh lineage and release the stem for re-offer. The idle hook records the same draw and keep after an approved update. Refused, snagged, or escalated edits lift `rework.md` as `rework-proposal` (before the terminal on a terminal path) and leave the stem queued. A terminal path without a worktree, or either path with spent supervisor budget, makes no call or proposal.
- **Machine keep:** drain and serve use `awaiting_operator` and `reofferable` to hold queued stems with a spent cap, `ticket_changed`, or `merge_conflict_rerun_spent` and re-offer others with budget. `record_reoffer` journals `keep actor: machine` for a queued stem, then draws `retry` unless the terminal is `premise_failed` without escalation, carries `provider_drought` or `conflict_rerun`, or is `infra_error` or `timeout` without an escalation rung. A machine keep never resets caps. The snapshot holds Reject-queue stems only when they await the operator (content parks remain separate).
- `ticket confirm` on a `draft` ticket promotes it to `confirmed` instead.

Keep and kill normally require a person at an interactive terminal to answer `y` at the prompt before the verdict proceeds. `--yes` and `--extension` skip the terminal check and prompt.

### 6.7 Other holds

- **`ticket_changed`:** a committed or uncommitted change to `ticket.md` during a run ends the
  attempt `gate_failed` and holds it in the Reject queue, with no diagnosis, Rework, or cap draw.
  Review the change to `tickets/<stem>/ticket.md`, then keep (`clutch ticket confirm <stem>`) to run
  the changed ticket as a fresh attempt, or kill (`clutch ticket reject <stem>`). Machine keeps do
  not release this hold. Stage boundaries, admission, and queued or confirmed merge admissions
  all check the dispatch identity. Rework updates between attempts are fresh ticket inputs.

- **Premise park:** a requisition-stage `premise_failed` draws no cap, makes no Diagnose call, and is not routed to the Reject queue. Edit the committed ticket to release it; no `ticket confirm` is needed. The next review receives the last recorded review’s findings and the diff since, rules on those findings, and raises new findings only against changed text, except that a defect making a criterion or `## Verification` command impossible to satisfy against merged code is raised whether or not its text changed. Other premise failures: with the default `premise_bounce: 1`, the first `premise_failed` spends
  the cap and routes to the Reject queue via `premise_bounce cap spent`; only an operator
  `ticket confirm` or a supervisor keep (section 6.6) releases it. When a host sets `premise_bounce` above 1 and caps still have budget,
  an Implement premise overruled by Diagnose with `retry` escalates and is re-offered without an edit, drawing `retry` with the new rung and carrying the lessons. At the top rung it enters the Reject queue. Other premise failures park until their committed `ticket.md` changes; that re-offer draws no retry.
- **`budget_exceeded`:** not diagnosed, draws nothing. Ticket stages pass no spend budget, so in
  practice only eval runs reach it.
- **Reconcile:** whenever a verb other than pause, resume, kill or stop takes the writer lock, any stem still marked `running`
  (or with an unfinished effect) is reaped: harvested, journaled `abandoned`, worktree removed.
  A stem with a `HELD` merge-queue receipt for its current attempt is not reaped, nor is a stem whose only unfinished effects are standalone review `llm/review-<stem>/` calls. `abandoned` stems stay eligible. With no engine running, `view status` shows such a stem as interrupted, `ticket reject`
  reaps and rejects it, and `ticket order` treats it as open.
- **Flaky tests:** Check quarantines unedited fail-then-pass tests and releases them on a passing observation after a merged fix or a declined report (using `declined:<box_id>` without a merge). Edited flakes and cap-blocked flakes fail Check.

## 7. Drain and serve

A dispatch exception is journaled as an `infra_error` terminal, re-offered, and held in the Reject queue at the attempts cap.

### 7.1 `drain`

1. Takes the lock, reconciles, fires due timers, runs the provider preflight, runs intake once.
2. Loops: reload config, honor pause/kill/stop, run intake and ingest host bug reports into the Suggestion Box between tickets, run an operator-requested retro, scan committed tickets (skipping stems settled or rejected in the journal), pick the
   next ticket, review its committed content if it lacks an approval, run it, merge it inline. Serve applies the same review before Implement and holds a premise-parked ticket until its committed content changes.
3. **Pick order:** confirmed, unsettled, not rejected, every dependency settled (through split
   successors); among eligible fresh tickets and re-offers, `## Runs before` orders named stems
   after the ticket naming them, with fixes linked from confirmed flake reports first, then priority P0-P3, authored age, and stem breaking ties.
   Edges to ineligible stems never block a pick. Skipped: storm-held, drought-parked, Reject-queue stems without budget, and tickets
   whose `stuck` exceeds `drain.max_ticket_minutes` (default 90).
   Each pick records this order and its hints in `queue.json`; it also records idle free-slot reasons in `waiting` and `hold`, which `view watch` and the extension show as row status.
4. **Quiescence:** when nothing is eligible, it re-offers parked stems with budget (drawing
   `retry`, subject to the exclusions in section 6.6), and stops when nothing changes.
5. **Report:** merged, parked (with reasons and the command to continue), blocked on depends,
   invalid tickets excluding those settled or rejected in the journal, drafts awaiting confirm. A requisition
   park lists its review findings under the parked line.

SIGHUP, SIGTERM, and SIGINT stop a drain as `engine kill` does: the running ticket is aborted and journaled, and the report says the drain is not quiescent.

Bounds: `drain.max_runtime_hours` (default 12) halts it (exit 1). The ceiling is carried across a self-upgrade handoff.

**Self-upgrade:** when draining the engine’s own source tree, a merge changing `clutch/` causes the drain to journal a handoff,
releases the lock, and replaces its process in place so the new engine code runs the rest of the queue.
A host repo or pip-installed engine never self-upgrades through drain; upgrade those by reinstalling.
Both verbs use `uv run --project <engine checkout> python -m clutch` followed by their invocation arguments.

### 7.2 `serve`

The continuous daemon. On start it takes the lock, reconciles and rebuilds timers,
publishes `state_dir/control/active.json`, and runs five loops (every 0.1s):

- **Watcher:** runs intake and re-reads tickets, debounced, skipping stems settled or rejected in the journal; a ticket that fails to parse keeps
  its last good version.
- **Dispatch:** the scheduler selects one ticket at a time. It waits while
  `scheduler.max_unmerged` (default 2) finished tickets are waiting to merge, while paused, or
  while a stem is held (Reject queue awaiting an operator, storm, drought, or a premise or diff-budget park at unchanged ticket content). After a failed terminal, serve puts the ticket back for the re-offer rule and draws `retry` on re-offer as drain does, subject to the exclusions in section 6.6. Each fresh dispatch reviews committed content without an existing approval before Implement. Among eligible tickets,
  `## Runs before` orders named stems after the ticket naming them; fixes linked from confirmed flake reports lead ahead of priority, chain length, and age; priority, authored age,
  and stem break ties. Edges to ineligible stems never block dispatch. With parallel enabled, `parallel_order` ranks by priority, then the longest unsettled chain within a priority; candidates overlapping an in-flight fence are skipped and logged as `dispatch_skip`, a ticket rerun after a conflict discard and a candidate overlapping one ignore `shared_paths`, and a candidate skipped `SKIP_LIMIT` times blocks later candidates whose fences overlap it.
  Admission permits up to `scheduler.parallel.max_runs` slot-holding runs when enabled (one otherwise); the scheduler returns once a ticket occupies a slot and each run is its own task, with parallel off holding one in flight. Runs waiting for merge retain ownership but release their slot. A merge poll with work excludes the other exclusive sections, permits running implementations and new runs, and marks serve busy until it finishes; an idle poll takes no section. Box intake with work, retro, the idle supervise pass, maintenance, startup and sweeps still exclude slot-holding runs; intake and watch publication proceed beside running implementations. Idle checks include every owned run.
- **Merge queue:** serial admission (section 7.2.1).
- **Box intake:** ingests host bug reports into the Suggestion Box and never triages.
- **Verdicts:** applies accepted confirm and reject requests independently of merge polling and active Check or model work, using the ticket writer transaction.

Maintenance on each loop: control requests, timers, orphan sweeps, notification replay, and checkpoint pushes. If any loop dies,
`serve` stops; consumer failures remain fatal.

Requested retros stop new admission, wait for
the next idle point, run, and then resume admission. A pending stop takes precedence.

Retro and estimate calibration run only when an operator invokes `engine retro` or `engine calibrate`; `view status` and `host doctor` report overdue thresholds without holding admission.

A git-checkout engine records its `clutch` tree at startup and checks it before
admission and on every merge poll, including while implementations run. A change journals `serve_upgrade_pending` and stops new admissions; queued rows show the upgrade hold until `serve_handoff`. After running tickets,
pending or active merges, and any running roadmap pass finish, serve journals `serve_handoff`, cleans up, closes the journal,
releases the lock, and replaces its process in place with the new serve. A pending kill wins. An accepted stop waits for the same idle condition and exits without spawning. Non-git engines do not watch.

#### 7.2.1 Merge queue (serve only)

For a nonempty branch with no `HELD` receipt and only `tickets/` changes on main since the reviewed merge
base, the safety host checks and integration tier are skipped; safety and Merge
gates still run. Empty branches take the full path for report custody.

For each candidate, in pick order:

1. Rebase onto `main`. A conflicted path that matches exactly one `merge.strategies` entry is
   resolved mechanically (`union` for append-only files, `regenerate` re-runs a generator).
   If mechanical resolution cannot finish, the `resolve` model surface tries text conflicts
   bounded by engine constants: at most 3 files and 60 conflict-marker lines across the admission,
   no binary, modify/delete or rename conflicts, and no safety-inventory paths (except configured
   `scheduler.parallel.shared_paths`, which waive only that exclusion). It receives the ticket's
   and relevant main-side tickets' Goal and Scope in, plus each file's base, ours and theirs text.
   Resolve and its review may nest inside the merge stage, and visual review and meta fill may nest inside Check on the same driver.
   Resolved contents must have no markers and receive an approving call of the unchanged review
   surface over the resolution delta before the full safety and integration tiers run. The call
   writes no review record and lifts no outbox; the old approval alone cannot authorize the repair.
   Ineligible conflicts, decline, invalid replies and review refusals abort the rebase and return
   a refused `StageResult` with finding code `merge_conflict_rerun`. After admission unwinds,
   the consuming writer lifts the discarded diff's non-conflicted files to
   `tickets/<stem>/attempts/<n>/prior.diff` as reference, journals
   `merge_conflict_rerun` with the discarded attempt number, and retires the branch and worktree
   through git (remove + prune). The `gate_failed` terminal carries `conflict_rerun: true`:
   the ticket is re-offered for fresh Implement from current `main`, with no retry draw or
   failed-attempt charge. Discarded code is never applied to the new branch.
   `CONFLICT_RERUN_LIMIT` allows two reruns per lineage. A third conflict emits no rerun signal
   and parks with `merge_conflict_rerun_spent` in the Reject queue until an operator keep;
   its paved road is "split the ticket, or run it with parallel disabled".
   Conflict facts record `resolving_rung: none | mechanical | model | rerun`; historical
   `rework` facts still fold. Kept model repairs record `resolving_rung: model`.
2. **Safety tier:** scope fence, run record, Merge gates, and host safety checks.
3. **Integration tier:** all Check and Merge gates, plus host `always` + `hard` checks through the shared runner also used by Check and inline merge.
4. **Red streak:** three different stems failing integration in a row pause the queue; `engine resume`
   with the advertised hold releases it.
5. Squash-merge as in section 4.5, and verify `main`'s tree equals the checked tree.

- Before the admission receipt, `dirty_checkout` refuses tracked main-checkout edits overlapping the branch and staged changes outside the branch; commit or revert overlapping edits, or commit or unstage staged changes, and retry.

### 7.3 Control

`ticket confirm` and `ticket reject` publish verdict requests to the running drain or serve, which applies them.

Submission and acceptance do not mean application is complete. Serve applies accepted ticket verdicts while unrelated Check or model work continues, waiting for conflicting checkout writes only. The engine decides each published verdict request later. A verdict decision row marked `stale` or
`rejected` was not applied; its reason says why. Fix that cause and run `ticket confirm` or `ticket reject` again
for the stem. The row disappears once the stem is resolved.

`pause`, `resume`, `kill`, `retro`, and `stop` write a request file to `state_dir/control/inbox/`, bound to the
running engine's lifecycle id. The engine journals a `control_decision` (accepted, stale, or
rejected) for each request. Pause stops new dispatch; resume must name the advertised hold;
kill stops the engine at the next safe point. Stop admits no new ticket, lets work in progress finish and merge, then exits and releases the lock; unlike pause, it ends the process. `run` does not read control requests.

### 7.4 Storms, watchdog, notifications, pushes

- **Storm breaker:** every Suggestion Box arrival is counted per signature. More than 5 in an
  hour trips a hold on the emitting ticket's stage. Only `engine resume` naming that trip releases it.
- **Watchdog:** watches each model call's active time (soft past 1.5x expected, killed at the
  stuck budget) and spending without progress in the scope fence (warned past 3x a call's
  cost). It notifies on both.
- **Notifications:** sent by running `config.notify` (an argv) with the message. `serve` replays
  undelivered escalations (storm trips, red streaks, tree mismatches) from the journal. Unset
  `notify` only logs.
- **Checkpoint push:** in `serve`, idle, after 5 merges or 10 settled tickets (merged, already satisfied, or rejected) since the last push: `git push origin main`. A
  failed push is journaled and filed to the Suggestion Box.

### 7.5 Roadmap operation

The plan-ticket agent authors rows using `clutch roadmap author` and runs `clutch roadmap gate` after the queue drains. Once the release rows merge and the gate passes, it reports readiness to the owner. The owner runs `clutch release ship`, which gates the current release, bumps and tags it, publishes when configured, and runs packages. Serve and drain do not run these steps.

The supervising agent loop is printed by `clutch prompt drain-loop`. It releases Reject-queue stems and drafts by executing `clutch prompt diagnose` or `clutch prompt drafts` Recommendations with `clutch ticket confirm --yes` or `clutch ticket reject --yes`. It files cause fixes with `clutch box suggest` and never authors a ticket itself. It triages Suggestion Box messages pending when its tick starts, including during a drain, and dismisses them between drains, each at most once per tick, by executing a `clutch prompt box` Recommendation; triage's verdict is final. Running the prompt is the owner's delegation of those verdicts. They are journaled with `actor: operator`, so `roadmap merged --unattended` does not count those stems.

## 8. AI providers and prompts

### 8.1 Providers

Four CLI adapters ship: `claude`, `codex`, `qwen` (Qwen Code against a local Ollama model at the provider’s `base_url`), and `gemini` (Google's Gemini CLI with an API key). Only `kind: cli` providers are accepted.

- Implement is the only surface with write access (`claude --permission-mode
  bypassPermissions`, `codex --dangerously-bypass-approvals-and-sandbox`, `qwen --approval-mode yolo`, `gemini --approval-mode yolo`) and runs in the
  ticket's worktree. Every other surface is read-only. Gemini's grant is also a packaged system settings file chosen per call: `gemini-readonly.json` allows only read tools and `gemini-write.json` allows every tool.
`claude` and `qwen` read `CLAUDE.md`, and `codex` reads `AGENTS.md`. clutch points qwen at `CLAUDE.md` through its packaged `qwen-settings.json`. `gemini` reads `AGENTS.md` through the packaged settings files' `context.fileName`, and also loads any `GEMINI.md`, which that setting cannot exclude.

**Model names.** `claude` resolves the aliases `haiku`, `sonnet`, `opus`, `fable` with one small probe call each, reading the resolved name from the stream's `init` event. `codex` reads `codex debug models` (visible entries in priority order, no model call); `qwen` reads `ollama list` where `ollama` is on `PATH`. `gemini` lists none because the CLI has no listing command; a gemini call records the model its stream's `stats.models` names, because `-m` does not pin flash-family names. `clutch config update` prints listings beside the configured names.

- Each provider maps tiers `low | medium | high | max` to models (`models_by_tier`).
- A provider's `auth` env var is removed from every child process except that provider's own
  calls; git, checks, and notifications get no provider key. The env var named by `release.pypi_token` is removed likewise, except the `clutch release publish` upload receives it as `UV_PUBLISH_TOKEN`.
- **Preflight** (once per engine session, and again after a config reload changes `providers` or `routing`; also at the start of `box triage`/`ticket review` and standalone `engine retro` with a merge to report): checks each CLI's version against its
  latest release (a mismatch is only a notice) and sends one probe call to every routed model.
- A CLI installed in the host project (`clutch provider install <provider>`, a pnpm dev dependency under `node_modules/.bin`) is used before one on `PATH`, because the checkout's `node_modules/.bin` heads every provider child's `PATH`; the preflight's update road is `clutch provider install <provider>`.

### 8.2 Routing

`routing` rows map `(tier, surface)` to an ordered list of candidates. An optional `kinds` list restricts a row to those ticket kinds; matching kind rows precede unrestricted rows for the requested surface and then review. A surface with no row
falls back to the `(tier, review)` row. The model is the candidate's `model` or the provider's
`models_by_tier[tier]`. An optional `panel` declares a size and surface-compatible combiner; review, diagnose, and triage fan out, while the other surfaces do not yet.

### 8.3 Admission, breakers, droughts

- Each provider has `limits.concurrency` call slots. When the first candidate has no free slot and its projected wait is over 60 seconds, the call goes to the next candidate with a free slot before waiting.
- `circuit_breaker.k` (default 3) consecutive outages open a provider for `cooldown_minutes`
  (default 10).
- A quota error cools the provider for `limits.quota_window_minutes` (default 60). An auth error drops it for
  the session and notifies.
- When no candidate is available the stem is **drought-parked**: journaled
  `infra_error / provider_drought`, no cap drawn, re-offered when a route frees up.

### 8.4 Prompt specs and the driver

`clutch/specs/ask/` holds operator prompt templates rendered by `prompt`, not driver specs.

Every model call goes through one driver (`clutch/driver.py`) using a prompt spec from `clutch/specs/`:

| Spec | Used for | Replies |
|---|---|---|
| `implement.md` | writing the change | packing slip: outcome, summary, second problems |
| `review.md` | judging the diff | approve / snag / rma |
| `diagnose.md` | explaining a failure | retry / escalate / split / reject / abandon-human + lessons |
| `rework.md` | rewriting or splitting a ticket | update / split / escalate |
| `requisition_review.md` | short check of an authored ticket and its Context | approve / snag / rma |
| `author.md` | writing a ticket from a Suggestion Box message | stem + ticket |
| `triage.md` | settling a Suggestion Box message | author / tombstone / declined |
| `retro.md` | proposing prompt-spec changes | proposals |
| `acceptance.md` | judging a release’s merged rows together against its theme, ship gate, and plans | promises `met` / `partial` / `unmet` / `deferred` with gap rows |

Specs always load from the engine's `clutch/specs/`, never from the host. Host material is injected only
inside `<<clutch-data:...>>` blocks; a rendered prompt over 400,000 characters is refused. The
driver re-prompts with findings when a reply is invalid or fails a gate, up to `caps.retry`
times; each call is captured in the evidence store. `Driver.run_panel` runs members in turn under one stuck budget and returns their results and dropped members; member spools include `m<k>` beneath the surface.

### 8.5 Spend and redaction

- Spend is the sum of each call's journaled cost (the stream's reported USD, else the provider's
  `est_cost_per_call_usd`). `view status` prints the total.
- Configured secret values are replaced with `[REDACTED:NAME]` in captures, the engine log,
  the evidence store's blobs, notifications, retro reports, and harvests (`attempts/<n>/harvest.json`). The journal itself is not scrubbed; model
  results are scrubbed before they are journaled.

## 9. Suggestion Box

### 9.1 Messages

Problems found while working are filed, not fixed in the current diff. Classes: `suggestion`,
`failure_report`, `override_report`, `retro_finding`, `bug_report`, `roadmap_row`. A `roadmap_row` carries a roadmap row and its owning plan path. Each message is a file in
`state_dir/box/`. A repeat of the same signature is folded into the existing message. Sessions file `suggestion` messages with `box suggest` directly into the box.

### 9.2 Triage

`box triage` settles named pending messages, or all pending messages when no IDs are supplied, one at a time. When drain or serve holds the lock, it submits a request for the engine to run at its next idle point:

- `author`: run the Author stage to write a ticket.
- `tombstone`: the message is already covered by a merged or committed ticket. A third
  re-report reopens it. Retro recurrences use the same re-report rule.
- `declined`: record a decision in `tickets/decisions/<id>.md`.

The Triage prompt embeds a `neighbors` block of nearest indexed box messages, roadmap rows and decision records; `unavailable: ...` or `none` indicates no usable neighbor evidence, never a failure. A `majority-verdict` panel on the triage route runs N member calls per message and settles from the majority verdict, breaking ties in the order `declined`, `tombstone`, `author` so a tie never authors; a non-`ok` member leaves the message pending, while infrastructure failures are dropped as in diagnosis.

`box dismiss <id> ...` records operator decisions without a model call; unknown IDs refuse before any message is settled.

### 9.3 Author and starting state

A `retro_finding` naming a spec path the repository does not track is declined before the Author call, with a decision record naming the untracked paths and retro report for the owner to carry to clutch.

For a `roadmap_row` message, Author embeds the row and its plan, whole under 40,000 characters and otherwise the Target design and Where each piece lives sections. The ticket uses the row’s stem, kind, and priority; existing evidence under `tickets/<stem>/evidence/` is committed with it.

The Author prompt embeds the authoring guide, the skeletons, and the latest `estimate_calibration` table (`engine calibrate`, section 2.1; `none` before the first), and a `context_suggest` block of index-matched section selectors (`none` or `unavailable: ...` without a usable index, never a decline), a `neighbors` block of the nearest indexed box messages, roadmap rows and decision records (same `none` or `unavailable: ...` forms, never a decline), and each re-prompt carries the last parsed ticket in `previous_reply`. Each later review receives the previous review and the diff from the text it judged. The Author stage writes `tickets/<stem>/ticket.md` with `source: box:<class>`, has
`requisition_review` check it, and commits it. Its state is `draft` (needs `ticket confirm`) if the
message was reopened, the review baseline is not GO (except for `roadmap_row`), `engine_plane_safety_inventory` is empty or
touched by the ticket's fence, or the ticket carries a `gate_bypass`. Otherwise `box_policy`
decides per message class.

### 9.4 Host bug reports

When `report_inbox` is set, serve, drain, and triage ingest host bug reports (`*.json`, closed schema, bounded
replay and log evidence) into the Suggestion Box as `bug_report` messages, keeping the evidence
in custody for the authored bug ticket. Drain ingests between tickets.

### 9.5 Retro

Spike kinds count override invoices on merges, rework orders, gate-failure transitions,
integration-red conflict facts, reject queue routed transitions or reject arrivals,
premise-failed transitions, infra-error transitions (including provider drought), flake
detection signals, and escape signals for automatically reopened tombstones.

The retro reads the journal since the last report. Measurements include `conflict_paths`: the top ten paths with at least two journaled merge conflicts in the window, with resolving rungs. By default `retro.test_timing` includes each Check gate’s per-invoice counts and duration plus each slow test’s maximum duration and invoice count. `retro.coverage` includes the latest repository percentage and each file’s latest and minimum percentages and invoice count. Set either switch to false to omit its summary. Retros run only when an operator invokes `engine retro`. A requested retro runs between tickets in drain and at the next idle point in serve, then admission resumes. The `retro:` thresholds mark overdue reminders in `view status` and `host doctor`: by default 25 merges, 40 settled tickets, or 5 events of one spike kind. A settled ticket is a stem whose state goes to merged, already satisfied or rejected, counted once. Each nested `retro.merges`, `retro.settled`, and `retro.spikes` block has an `enabled` switch; their thresholds are `merges.every`, `settled.every`, and `spikes.count`. The nonempty `spikes.kinds` allowlist selects which kinds can mark a retro overdue, except that override cannot make a retro due. Overrides are measured and included in the report when a retro runs; measurements still report every kind. The master `retro.enabled: false` disables retro overdue reminders even if sub-triggers are enabled; run one on demand with `engine retro`. Config load refuses an enabled master with all three triggers disabled (enable a trigger or set `retro.enabled: false`) and duplicate spike kinds (list each kind once). It commits `tickets/retro/NNNNNN.md` (measurements,
scorecard, proposals) and files new proposals as `retro_finding` messages. It supplies prior findings to the model; a proposal matching an existing cause counts as a recurrence on that message. A recurrence after its ticket fix merged reopens the finding for a new fix. Proposals identify either prompt-spec paths or repository paths for a test repair. Proposals may instead name conflicted paths with `strategy` (add a `merge.strategies` entry) or `split`. Test repairs name one issue: `unit-io`, `slow`, `drift`, `flaky`, `coverage-hard`, `over-mocking`, `weak-assertion`, `shared-state`, `duplicate`, or `skip-rot`.

### 9.6 Scorecard and baseline

- The **scorecard** counts, per gate and review surface, catches, escapes, and bypasses, and flags
  a surface with 25+ evaluations and no catch and no escape as a prune candidate.
- The **panel scorecard** folds journaled review replies and costs by member slot, counting unique findings confirmed by a later merge per 100 reviews and the total cost relative to the lowest present slot. It also reads journaled `panel_facts` signals to separate distinct-model (`models`) from repeated-sample (`samples`) reviews. Its outcomes are `no_panel_reviews`, `no_cost_data`, and `measured`.
- The **review baseline** is a GO / NO_GO verdict recorded by the eval harness
  (`eval/harness.py`). GO counts only while the recorded review and author models and spec
  versions still match the config. It gates Author starting state only.
- The **visual baseline** records a `visual_baseline` GO / NO_GO verdict bound to the visual judge routing and spec major; GO requires at least 20 labelled cases and 0.85 overall agreement. Check reads it before selecting graphics candidates.

## 10. State on disk

Everything lives under `state_dir` (this repo: `.clutch/state`).

### 10.1 Files

| Path | Holds |
|---|---|
| `journal/NNNNNN-YYYYMMDD.jsonl` | The journal (section 10.2); a segment rolls at 64 MiB or 24 hours. |
| `cache/journal.duckdb` | Rebuildable journal projection; never authoritative. Delete it to force a rebuild. |
| `cache/journal.duckdb.lock` | Exclusive lock held while opening, loading, querying and closing the journal cache. |
| `engine.log` | Per-call events carry `call_key`. Diagnostics including `engine_start` and `engine_stop` for drain, serve and run, and `phase_start` and `phase_end` for preflight and retro checks, and stage start/end events for every stage, including Check and merge. Stages do not nest on one driver except for resolve and review inside merge admission and visual review and meta fill inside Check; a gate run inside a stage logs under that stage. Requisition reviews nested in author or rework have no stage events of their own; a standalone review logs them under the reviewed ticket's stem; redacted, rotated at 16 MiB with 3 backups, and never authoritative. |
| `dist/` | Wheel and sdist last built by `clutch release publish`; `uv build --clear` empties it on each publish. |
| `drain.out` | Output appended by `engine drain --detach`. |
| `coverage-map.json` | Written by `coverage map` and read by requisition review. |
| `queue.json` | Derived pick order, timestamp, `Runs before` hints, and idle free-slot reasons (`waiting`, `hold`) shown as row status in watch and the extension. |
| `scratch/` | Graphics render directories and retro window files read by agents by path, distinct from `evidence/scratch/`. |
| `evidence/` | Call records (section 10.4) in `calls/<escaped key>/` (`start.json` before spawn, `end.json` at exit; re-executions use a `#<n>` suffix; keyless calls have no record), attempt manifests in `attempts/<stem>/<run_seq>/<attempt>.json` (schema `clutch.evidence.attempt/1.0`), compressed redacted `blobs/`, and temporary stdin and index files in `scratch/`. Blobs are retained until an operator runs `evidence prune`; `evidence.warn_gb` sets the warning threshold. Per-attempt prompts, outputs, and command output are captures. Capture pointers to blobs live at `captures/<stem>/<attempt>/<escaped name>.json`. |
| `clutch.lock` | Engine lock held by `run`, `drain`, `serve` and the other verbs that still take it. Its JSON identity records the holder verb, used to decide whether it consumes control requests; the kernel frees the lock when the holder dies. |
| `commit.lock` | Serializes git index writes and commits, with a 60-second wait. |
| `journal.lock` | Short-held exclusive lock for every journal append, covering tail repair, segment roll, and the write. |
| `worktrees/` | Ticket worktrees; `.base/` and `.regression-base/` hold scratch merge-base worktrees for base-red reruns and the bug gate. |
| `rework/<stem>/<attempt>/<call>/` | Scratch worktree where Rework validates a proposal. |
| `box.seq/` | Suggestion Box id reservations. |
| `box/` | Suggestion Box messages and report custody. |
| `control/` | `active.json` and the control request inbox. |

### 10.2 The journal

The journal is the record of truth: append-only JSON lines, fsynced per event. A Journal instance parses each byte once and re-reads only appended lines during normal append-only operation. Event types:
`state_transition` (run states), `cap_consumed`, `signal` (a closed list of named signals),
`effect_intent` / `effect_completion`, `timer_armed` / `timer_fired`, and `checkpoint` (reserved: readers accept it but `Journal.append` refuses it). A `signal` body names exactly one member of `SIGNAL_NAMES` in `clutch/journal.py` under the key `signal` or `kind`; append refuses any other name.

An **Effect** is an action keyed so it happens once: a key with a recorded completion replays
the recorded result instead of acting again. Model calls, ticket-plane commits, merges, pushes,
and notifications are Effects, so a crash never repeats one.

Ticket-plane edits use a narrow critical section: `main_write` is acquired before
`commit.lock`, and the edit callback and exact-path commit run under both. Intake
holds the same locks across its status read, stray check, stamping, and commits;
merge squash also takes them in that order. Callbacks must not invoke a model,
run checks, or call a lock-taking Git writer. Model and check work run outside
this section; the commit lock is not held for a run lifetime.

### 10.3 `view status`

`view status` is a write-free projection of the journal, followed by an evidence size warning when over the threshold:

1. The merged count, and stems in flight, interrupted (last `running` with no live engine), or blocked (last state neither `running`, settled, nor rejected).
2. Intake and verdict refusals for stems not settled or rejected, and reopens for unresolved messages.
3. Total spend.
4. The Reject queue.
5. Every Suggestion Box message in arrival order, with its state and summary.
6. Tombstones and reopens.
7. The current retro window's scorecard and provenance.

### 10.4 Evidence records

Each keyed provider call leaves a record under `<state_dir>/evidence/` with redacted stdout and stderr and an envelope of call facts. `CliAdapter.invoke` writes call records; harvest reads their start records for attempt manifests and reads the provider event tail (section 6.2): `latest_stdout` takes stdout from the newest `end.json` by `clock.wall_end` whose key starts with `llm/<stem>/`. The journal, gates and dispatch do not read the store.

`invoke` writes a record only with a `CallCapture`. `ProviderLLM.admitted_call` builds it from the journal Effect key passed by `llm_call` (section 10.2): `llm/<group>/<run_seq>/<surface>/<attempt>/<call>`. The group is the ticket stem, or the surface name for a ticketless call. Panel member keys scope the run sequence as `m<k>-<run_seq>` while retaining six parts. Keyless calls leave no record: these include preflight's probe calls (section 8.1), calls made by the probe verb in section 2.1, and calls through the raw `ProviderLLM.call` seam. A key with a completed Effect replays its result without calling the provider or writing a record. Every call, keyed or not, writes its redacted prompt to a temporary file under `evidence/scratch/` as the CLI's stdin; the file and temporary index are removed when the call ends.

A record consists of `calls/<escaped key>/start.json` and `end.json`, with the key escaped by `urllib.parse.quote(key, safe="")`. If a key runs again, its existing directory causes the next record to use `<key>#2`, then `#3` and so on. Only a key without a journaled completion can run again; the record's `id` retains the unsuffixed key.

`start.json` is written after the tree id is taken and before the CLI is spawned, so a crash, hang or kill can leave it behind. The start record is rewritten once with `native_ids` when the stream first reports a session or thread id. A start without an end means the call never finished recording, for example when the engine died mid-call. Its fields are:

- `schema`: `clutch.evidence.call/1.0`.
- `id`, `group`, `run_seq`, `surface`, `attempt` and `call` come from the key; `stem` is null for a ticketless call.
- `engine`: `version` is the installed `clutchwork` package version, `spec` is `<surface>.md`, and `spec_version` is that spec's frontmatter version.
- `route`: `tier`, `effort`, provider-name `candidates` in route order, the `chosen` provider, `reason` (`first`, `spill` or `failover`), and `config_sha`, the SHA-256 of the config snapshot's `repr`.
- `provider`: `name`, adapter class `adapter`, `kind`, `package`, and `cli_version` read by preflight in this process, or null. `billing` is `local` for a `base_url` provider, `metered` for one with `auth`, otherwise `subscription`.
- `model.requested`: the requested model.
- `process`: redacted `argv`, sorted child environment names in `env_names` (never values), `cwd` (the ticket worktree for a writing call, otherwise the checkout), `timeout_s`, `writes` (true only for `implement`), `isolated` (always false today), and `conduct_file`, the file name returned by `conduct_file` for the provider (section 8.1).
- `repo`: `main_sha` and `base_sha` resolve `main` and `HEAD` in that directory. `tree_before` is its working-tree git tree id, made with `git add -A` and `write-tree` through a temporary index using `GIT_INDEX_FILE` in `evidence/scratch/`. The real index, branch and reflog are untouched.
- `prompt`: `blob`, `chars` and `bytes` of the redacted prompt.
- `clock`: `wall_start` and `mono_start_ns`.

Whenever a start was written, `end.json` is written when the call ends: at exit, nonzero exit, kill, timeout, spawn error or stream parse failure. It contains:

- `exit.status`: `ok` for exit 0, `nonzero` for an exit above 0, `killed` for a signal exit or another unwind before the process returned, `timeout`, or `spawn_error` when the CLI was not found. This is process status: exit 0 with a parse failure is `ok` with a `failure_class`. `code` is the exit code or null, `signal` the signal number for a signal exit, and `failure_class` the raised `ProviderCallError` class, or null.
- `clock`: `wall_end`, `mono_end_ns` and `wall_ms`. Both `mono_start_ns` and `mono_end_ns` are the engine clock seam's wall time as epoch nanoseconds, not a monotonic counter.
- `rusage`: from `os.wait4` when the exec seam reaps the provider process, including after kill or timeout; null if no process was reaped, as for `spawn_error`. `user_s` and `sys_s` are CPU seconds and `max_rss_kb` is the kernel's `ru_maxrss` in kilobytes. On Linux this is the larger of the provider's own peak and the engine's peak at spawn, because exec carries the spawning process's high-water mark into the child; it is the provider's own peak only if that exceeds the engine's.
- `raw`: `stdout` and `stderr` are blob refs to the redacted output returned by the exec seam, or, when a call raised, the output attached to the exception as `process_capture` (empty when none was attached). `stdout_times` is a blob containing a JSON list of integer nanosecond offsets from call start, one per stdout line as the seam delivered it. `lines` is the stdout line count; `non_json_lines` counts lines that are not JSON objects.
- `repo`: `tree_after` and `changed_paths` from `git diff --name-only` between the two trees for a writing call whose process returned; otherwise null.
- `model.served`: the first string `model` in the stream's JSON events, with `served_source` of `stream` or `none`. `native_ids.session_id` and `native_ids.thread_id` are the first such strings in the stream. `parsed` holds `text_chars`, `input_tokens`, `output_tokens` and `usd` returned by `CliAdapter.parse` from normalized events, or 0 and nulls when nothing parsed.

Blobs live at `blobs/<first two hex digits>/<sha256 hex>` and records refer to them as `sha256:<hex>`. `put_blob` redacts UTF-8 text with configured secrets before hashing, so a secret never reaches the store, even as a hash; non-UTF-8 bytes are stored as given. Blobs are compressed with `compression.zstd` and each digest is written once, so identical content such as a prompt re-sent on retry is stored once.

Nothing prunes automatically. The writer-locked `clutch evidence prune --to-gb N` explicitly prunes to N × 10^9 bytes. If the compressed blob files' on-disk size exceeds that bound, prune walks records with an `end.json` from oldest `clock.wall_end` first. It deletes blobs named by each end (stdout, stderr and arrival times), except those still named by a record not yet walked, including a newer record or one without an end. It stops when size is under the bound. Records are never deleted, and prune never removes a blob named only by a `start.json`, such as a prompt.

`write_record` validates records against the strict pydantic `Start` or `End` model (strict types, `extra="forbid"`). `read_record` accepts any `clutch.evidence.call/1.<minor>` record, drops fields unknown to the current model and returns `SKIP` for another major version. `json_schema` generates JSON Schema for `start`, `end` and `event` from the models; `clutch evidence schema` prints it.

Each normalizer is a pure `normalize(stdout, times_ns, put_blob)` function turning raw stdout bytes and arrival offsets into `clutch.evidence.events/1.0` events. Their `NORMALIZER_ID`s are `claude-stream/2`, `codex-stream/1` and `gemini-stream/1`. A normalizer does no I/O: large text, including assistant text, thinking and tool output, goes through `put_blob` and the event carries the ref. Each event's `kind` comes from the closed `Event.kind` list; tool events carry a `class` from the closed `Tool.class_` list and the native tool name. Unmapped lines or content blocks become `unknown` events with their native payload; a non-JSON line is kept as `{"line": ...}`. `t_ms` is the line's arrival offset in milliseconds, or 0 without offsets.

The Claude normalizer is verified only for `claude`, so qwen's Claude-shaped stream is unverified. Codex `input_tokens` includes cached tokens, so `input_uncached` is `input_tokens` minus `cached_input_tokens`. Each normalizer has a golden fixture under `tests/fixtures/evidence/<provider>/`. `CliAdapter.parse` and `CallMeter` read normalized events from the adapter’s normalizer. Claude assistant lines with usage also yield an `assistant/usage` event. The last `result` or `usage` event with a non-null status closes the call; it carries the outcome, final text blob, optional USD cost and optional model. Claude’s preceding usage event carries its tokens. `Event` provides optional `usd` and `model` fields. `clutch evidence renormalize` writes `normalized/<escaped normalizer id>.json` beside the record.

## 11. Config

One `config.yaml`, validated strictly: unknown keys, explicit nulls, and bad values are refused
with the fix. The full field inventory is in `clutch/docs/host-contract.md`. This repo’s own
`config.yaml` uses its Python host test setup.

`clutch config init` prints a suggestion built from the installed CLIs.

| Area | Controls |
|---|---|
| `schema_version`, `state_dir`, `worktree_root` | config version; where state and worktrees live |
| `providers`, `routing`, `routing_default_tier` (default `medium`) | models and which serves what (section 8); every `kind: cli` provider requires `package`, the pnpm package preflight reads |
| `snapshot_merged_limit` | Merged rows included by `view snapshot` (default 100), unless `--all-merged` is passed. |
| `roadmap.ahead` | Default window for `roadmap author --ahead` (default 2). |
| `evidence.warn_gb` | Evidence blob size warning threshold in GB; defaults to 20. |
| `meta.paths` | Roots and kinds for file metadata; defaults to an empty list. |
| `training_data` | Experimental training switch (off by default) and additional exclusion globs. |
| `release` | Upload authorization and PyPI token environment variable name; uploads default to off. |
| `review` | `coverage_map`, `gate_severity`, host `autofix` commands and `mechanical` checks |
| `merge` | `safety_checks`, conflict `strategies` (serve only) |
| `caps`, `circuit_breaker` | failure bounds (section 6.4, 8.3) |
| `retro` | `enabled`, `merges`, `settled`, `spikes` control overdue reminders; `test_timing` and `coverage` control measurement summaries (section 9.5) |
| `calibration` | `every` (default 100): the number of most recent completed Implement calls an `engine calibrate` table covers; status and doctor report overdue calibration once that many have completed since the last calibration (section 7) |
| `scheduler`, `drain` | `max_unmerged`; experimental serve-only `scheduler.parallel` with `enabled` (default false), `max_runs` (default 2), `shared_paths` (default []); `max_runtime_hours`, `max_ticket_minutes` |
| `engine_plane_safety_inventory`, `box_policy` | Author starting state (section 9.3) |
| `prompts_dir` | Optional directory of host prompt templates, relative to the config file. |
| `ask_notes` | Optional host guidance appended to operator prompts as a `host_notes` data block. |
| `notify`, `report_inbox`, `context_files` | notification command; host bug report folder; extra Implement context |

## 12. Host projects

See the [host run guide](../clutch/docs/host-running.md) for invocation and operation.

The block carries only process rules that hold for every host; codebase rules belong in the project-owned remainder. The block has four sections: `Ticket authoring` is for sessions writing tickets, `Diagnosis` is for sessions addressing failures, `Chat session conduct` is for interactive chat sessions, and `Engine conduct` is for ticket agents.

- `clutch host core` writes the managed block between `<!-- clutch:core begin -->` and
  `<!-- clutch:core end -->` in `CLAUDE.md` (for `claude` and `qwen`) or `AGENTS.md` (other CLIs), for each
  routed provider. On first adoption the block goes above the existing content; after that only
  the block is replaced. Project text outside the block is the host's, but a paragraph that
  tells clutch how to run (for example "clutch must ...") is refused.
- The `core_drift` gate fails a ticket when a routed conduct file's block is not current.
- `engine serve`, `engine drain` and `engine run` refuse to start when a committed routed conduct block is stale; `host doctor` reports this as a `core` row.
- `host doctor` checks a host's setup without changing anything and warns when evidence exceeds `evidence.warn_gb`.
- The `clutch.testreport` pytest plugin accepts `--clutch-results PATH` and writes JSON with
  `schema_version: 2`, a `tests` map from pytest node IDs to `passed`, `failed`, or `skipped`,
  and a matching `seconds` map of finite nonnegative floats. The reader accepts only schema 2 and refuses schema 1.
- The `clutch.testguard` unit-run pytest plugin blocks process and network IO during test phases
  and enforces the `test-gate.toml` unit time budget (60 seconds by default).
- A host provides `config.yaml`, its conduct files, and its tickets. `clutch/docs/host-contract.md` is
  the full host-facing contract; Python hosts can use its `## Python host test setup`.
- A clutch defect found in a host is named to the user in chat, never filed to the host Suggestion Box. Critical bugs and qualifying process gaps go upstream as a link `clutch box issue` prints for a person to review and submit; see [Reporting a clutch problem upstream](../clutch/docs/host-running.md#reporting-a-clutch-problem-upstream).


## 13. Eval report artifacts

The review-baseline report (`review-baseline-report.json`, written by `eval/harness.py`) is the only registered report artifact.

## 14. Project index

The project index at `<state_dir>/index.duckdb` is a rebuildable cache, never read by dispatch. Its five tables are `files` (tracked file metadata), `chunks` (sections and definitions), `embeddings` (vectors), `touches` (ticket changes), and `calls` (evidence records). With `index.embed` unset, there is no `embeddings` table. A merge refreshes an existing index file. With `index.implement_hint: true` the Implement prompt carries a `related_files` block of at most 10 lines and 3,000 characters, `none` or `unavailable: ...` when the index has nothing or cannot be read in 5 seconds, never failing or delaying Implement.

`clutch index build` creates or refreshes the index under the writer lock. Its outcomes are:

| Outcome | Exit | Meaning |
|---|---|---|
| `built` | 0 | Build completed without findings. |
| `built_with_findings` | 1 | Build completed with findings. |
| `not_built` | 2 | The database could not open or a finding is unrecognized. |
| `failed` | 2 | The build raised an exception. |
| `refused` | 2 | Config is invalid or the writer lock is held. |

Findings `git_failed`, `embed_failed`, `call_unreadable`, `box_unreadable`, `vss unavailable`, and `fts unavailable` exit 1; `db_open_failed` exits 2.

`clutch context suggest <stem>` reads a draft and the index without a lock, returning up to five co-changed files and five matching sections. It prints `context suggest: suggested` and lines `- <selector>  # <reason>`, or `context suggest: none` when empty (both exit 0 by default; `--require` makes an empty result exit 1). Invalid input or config is `refused`; a missing index is `no_index` (run `clutch index build`); an unreadable index is `index_unreadable` (retry after the running refresh finishes, or run `clutch index build` if a table is missing). These refusals exit 2 on stderr. Remove the reason tail before pasting a selector into Context.
