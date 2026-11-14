# Roadmap driver: plan

Run `docs/roadmap.md` unattended. The driver authors the next few roadmap rows when their dependencies have merged, never further ahead than that, so every ticket is written against the source as it is. When a ticket is held for a person, the driver does what the operator does today by hand: reads the diagnosis, edits the ticket within the supervising rules, has the edit reviewed, and keeps the ticket, a bounded number of times. When a split lands, the parent settles by itself. When a release's rows are all merged and its gate passes, the driver tags, bumps the version, and publishes to PyPI and the Marketplace under a standing authorization. What stays with a person is named, short, and the same for every release.

## Status

Draft plan. Nothing in it is in effect and no ticket is authored. Written 2026-11-14 at commit `c2d1c2a7` for `docs/roadmap.md`.

## Roadmap

Release 0.2.0, as its last group (`docs/roadmap.md` rows 88-93), after the truth-and-hygiene rows, because the driver is what runs 0.3.0 onward. Needs from the roadmap: `release-verb` (row 3) for tags and version bumps; `docs-truth-sweep` (row 4) so the documents the driver reads are true; `contention-authoring-rules` (row 13) in effect before it authors anything. What needs this plan: every later release, since the driver is how they run. Shared budgets: one new config block `release`, one new cap `caps.supervise`, one new Suggestion Box message class `roadmap_row` with its `box_policy` row. No CORE_TEMPLATE text: the chat-session rules do not change; the driver is an engine process bounded by caps and reviews, not a session.

## Why this is viable

Measured from this repo's journal at `c2d1c2a7`:

- 506 tickets merged. The operator issued 142 verdicts along the way: 78 keeps on held tickets, 28 kills, 36 draft confirms. About one touch per 3.6 merged tickets. The engine made 94 machine keeps on its own.
- The owner reports that nearly every keep was the same sequence: read the diagnosis, apply its suggested ticket edit, lint, review, confirm. That sequence is three existing engine pieces (Diagnose, Rework-update, machine keep) that are not wired together for this case.
- Every one of the 28 kills the owner remembers as necessary was a split's parent. The journal agrees: the three stems that were ever split (`chupa-ruff-config`, `split-test-serve`, `menu-mirrors-verb-admission`) all ended `rejected` by hand, because a `supersedes` signal neither settles the parent nor removes it from the Reject queue (`chupa/status.py::reject_queue`).
- Authoring from a plan already exists: the Author stage writes a ticket from a Suggestion Box message with a buildability review (`chupa/author.py::author`), and 44 of 442 box messages became tickets that way. A roadmap row is a message with a different shape.
- A drain of about 30 tickets ran unattended in about 4 hours (`README.md`); the self-upgrade handoff already lets a run continue across engine merges.

What this plan cannot remove: hand tests that need a person at a real CLI or browser (the Gemini image facts, GitHub prefill limits), the GO baseline judgment for a new reviewer model, a ticket whose goal or scope is wrong, and the first publish of a release when no standing authorization is configured.

## Current state

- **Rework-update exists but fires only on `split`.** `runner.drive` requests Rework when the diagnosis verdict is `split` or the render was over bound (`chupa/runner.py:301-305`). Rework's `update` action rewrites a ticket, has `requisition_review` judge it, and commits it as `chupa(<stem>): rework` (`docs/how-chupa-works.md` §6.5). Nothing runs it for `premise_failed` or a spent cap, which are the terminals that reach the Reject queue.
- **A machine keep never resets caps.** The lineage a cap counts over starts at the last `reject_verdict keep actor: operator` (`chupa/caps.py:28`). `record_reoffer` journals `actor: machine` keeps (`chupa/drain.py:106`), which re-offer a stem with budget left but cannot release one whose cap is spent. `awaiting_operator` (`drain.py:92-95`) holds any stem with a spent cap or a `ticket_changed` reason for a person.
- **A split's parent lingers.** `record_supersedes` journals the map (`chupa/rework.py:260`); dispatch skips superseded stems (`chupa/scheduler.py:58`) and dependents wait on the successors, but `reject_queue()` (`chupa/status.py:38-55`) pops a stem only on a `reject_verdict`, and `SETTLED` is `{merged, already_satisfied}` (`status.py:17`). The parent sits in the Reject queue until a person rejects it.
- **Author takes a box message.** `author(checkout, driver, box, message, pass_no)` chooses its policy row from the message class (`chupa/author.py:210`), embeds the authoring guide and skeletons, and runs the requisition review. Triage invokes it (`chupa/triage.py:272,328`). There is no other way in.
- **Release tooling is partial and manual.** `./dev.py publish` bumps only the patch version and uploads to PyPI with `UV_PUBLISH_TOKEN` (`dev.py:121-127`); nothing tags; `./dev.py vscode-package` builds a `.vsix` and prints the Marketplace upload page for a hand upload (`dev.py:128-152`). `release-verb` (roadmap row 3) adds the minor bump and tag.
- **The supervising prompt is a chat.** `chupa prompt drain-loop` renders the babysitting instructions for a Claude Code chat (`chupa/specs/ask/drain-loop.md`), whose allowed edits are the CORE_TEMPLATE supervising list: lint and format fixes, a missing fence or Context entry, a stale path, a wording update; never a goal or scope change, never a confirm or reject.
- **serve has idle hooks.** Retros run at the next idle point after a settle (`chupa/serve.py::check_retro`, `run_retro`), and `upgrade_idle` gates the self-upgrade. The driver's steps attach at the same points.
- **The roadmap is readable by machine.** Its master table rows carry stem, owner, kind, priority, depends, runs-before, and content; the release sections give the order; §9 says a row links its stem when authored and is struck when merged.

## Departures from the design record

| Record says | This plan | Why |
|---|---|---|
| §18.1 refuses "multiple authoring modes" | A second input to the one Author stage: a `roadmap_row` box message | The Author stage, its guide, its skeletons, and its review are unchanged; only the message shape differs. One authoring process, as `CLAUDE.md` requires |
| `docs/how-chupa-works.md` §6.4: "Editing `ticket.md` never resets a cap; only an operator `confirm` does" | A supervisor keep resets the lineage like an operator keep, at most `caps.supervise` times per lineage, and only after a reviewed Rework-update changed the ticket | The owner asked for it on 2026-11-14 after doing this by hand 78 times. The bound and the review are what make it safe; a supervisor keep on unchanged text is refused |
| CORE_TEMPLATE: a supervising session may not confirm or reject | Unchanged for sessions. The supervisor is an engine stage under a cap and a review, journaled with its own actor | The rule exists because a chat session has no bound and no review; the stage has both |

`CHUPA_PLAN.md` stays frozen. The tickets update `docs/how-chupa-works.md` §6.4-6.7, §7.2, §9.3, and a new "Roadmap driver" section.

## Target design

### 1. Superseded is settled (`superseded-settles`)

- A stem with a `supersedes` signal is in a new settled state `superseded`: `record_supersedes` journals a `state_transition` to `superseded` for the parent after the map; `SETTLED` gains it; `reject_queue()` pops it; `reject` refuses it as settled; `status` lists it beside `already_satisfied`; the extension's lifecycle diagram gains the state.
- The three historical parents are already `rejected`; the fold treats a `supersedes` on a `rejected` stem as the same thing and leaves history alone.

### 2. The supervisor step (`supervisor-rework`)

Runs inside `runner.drive`'s terminal handling, after Diagnosis, for a terminal that would be routed to the Reject queue with reason `premise_failed` or a spent cap:

1. **Propose.** Rework-update with the diagnosis lessons and findings as input, exactly as today's Rework. `chupa/specs/rework.md` gains the supervising rules as the allowed-edit list for this trigger: fix lint and format, add a missing fence or Context entry, correct a stale path, reword; never change `Goal / Why`, remove an acceptance criterion, or widen scope. A proposal that touches `Goal / Why` or drops a criterion is refused by a gate before review, with the road "escalate to the operator".
2. **Review.** `requisition_review` judges the proposal as it judges every Rework proposal, with the prior review's findings and the diff since (how-chupa-works §6.7).
3. **Keep.** On approve, the engine commits the proposal (`chupa(<stem>): rework`) and journals `reject_verdict keep actor: supervisor`. A supervisor keep starts a new lineage, like an operator keep, when and only when the committed ticket text changed. `caps.supervise` (default 2) bounds supervisor keeps per operator lineage; the draw is a `cap_consumed` event.
4. **Escalate.** A refused or snagged proposal, a spent `supervise` cap, or a proposal the gate refused leaves the stem in the Reject queue for the operator with the proposal attached (`tickets/<stem>/rework.md`, lifted like a review) so the person starts from the engine's best attempt, not from nothing.

`ticket_changed` holds are not supervised: a person edited the ticket mid-run and the person decides. Premise parks at the requisition stage already release on a ticket edit; the supervisor's edit releases them the same way, with the same review.

### 3. Roadmap authoring (`roadmap-author`)

- A new Suggestion Box message class `roadmap_row` (`chupa/box.py:18`), with a `box_policy` row (`chupa/config.py`) defaulting to `confirmed` when the review baseline is GO and `draft` otherwise, the rule every other row follows (how-chupa-works §9.3).
- `chupa roadmap author [--ahead N]` reads the master table, finds rows with no linked stem whose `Depends on` stems are all merged (or empty), in release order, and files one `roadmap_row` message per row until `N` (default 2) rows are open beyond the confirmed or running set. Each message carries the row's fields and the owning plan's path.
- Author handles a `roadmap_row` message with one new data block, `<<chupa-data:roadmap_row>>` (the row) and `<<chupa-data:plan>>` (the owning plan's Target design and Where-each-piece-lives sections, or the whole plan when under 40,000 characters), beside the guide and skeletons it already embeds. The stem is the row's stem; `requisition_review` runs as for every authored ticket; the row's hand-test prerequisites (a row whose content says "after the hand test") are refused until an evidence file the row names exists under `tickets/<stem>/evidence/`.
- On commit, the driver edits the roadmap row to link the stem (`chupa(roadmap): author <stem>`), a ticket-plane commit like a lift. When the ticket merges, the row is struck. The roadmap stays true because the driver, not a person, keeps it so.
- `--ahead` is the whole point: two rows, not twenty. A row authored against source that later rows change is a row authored too early.

### 4. Gates as commands (`release-gates-as-commands`)

- Each release section in `docs/roadmap.md` gains a fenced `gate` block: one or more argv commands that exit 0 when the release may ship, or `gate: operator` for a judgment a person makes. The prose gates become commands where a command exists (the suite, a `status` query, a `training export` count) and `operator` where not (a week of parallel runs, a GO verdict).
- `chupa roadmap status` prints, per release: rows merged, authored, open, blocked on a hand test; the gate's last result; the next rows the driver will author. Read-only; the extension draws it later.

### 5. Release and publish (`release-publish`)

- `chupa release --minor|--patch` (the engine verb behind `release-verb`'s `./dev.py release`): bumps `pyproject.toml`, commits, tags `v<version>`, journals a `release` signal. Hosts use the same verb for their own versions.
- `chupa publish`: builds and uploads to PyPI through the exec seam, with the token's env name in config (`release.pypi_token: UV_PUBLISH_TOKEN`), passed only to that child, like a provider key. `./dev.py vscode-publish`: bumps the extension's patch version, packages, and publishes with `vsce publish` under `release.vsce_token`; this repo only, since no host ships the extension.
- **Authorization.** Publishing is a remote mutation. `release.publish: true` in config is the owner's standing "push"; with it absent or false, the driver tags and bumps locally and parks the publish for `confirm` with the built artifacts listed. The conduct rule for chat sessions ("never push unless the user says push this turn") is untouched: the engine acts on config, sessions act on words.

### 6. The loop (`driver-loop`)

At serve's idle point after each settle, in this order:

1. If any Reject-queue stem is unsupervised, the supervisor step runs for it (section 2) before new work.
2. `roadmap author --ahead N` tops up the open rows (section 3).
3. If the current release's rows are all merged and its gate passes (section 4), `release` runs, then `publish` or the park (section 5); the next release becomes current.
4. A digest notification through `config.notify` (exists): rows merged since the last digest, stems waiting for the operator and why, the next rows to be authored, spend.

`drain` gets steps 1 and 2 between tickets; `run` gets none. `chupa prompt drain-loop` is rewritten to describe what the driver does by itself and what the chat should still look at: escalations with a `rework.md`, hand tests, and `gate: operator` releases.

### 7. What the operator still does

- Answers escalations: a stem with a spent `supervise` cap or a proposal the supervisor could not make. The engine's best proposal is attached.
- Runs hand tests and drops their evidence files where a row names them.
- Judges `gate: operator` releases and records GO baselines for new reviewer models.
- Says "push" once, in config, or confirms each publish.

## Where each piece lives

| Piece | Home |
|---|---|
| `superseded` state, projection, verdict refusal | `chupa/journal.py` (state), `chupa/status.py`, `chupa/rework.py` (`record_supersedes`), `chupa/observe.py`, `vscode-chupa/media/ticket-lifecycle.svg` |
| Supervisor trigger, keep, cap | `chupa/runner.py` (terminal handling), `chupa/caps.py` (`supervise`, lineage), `chupa/config.py` |
| Allowed-edit list and gate | `chupa/specs/rework.md`, `chupa/rework.py` |
| `roadmap_row` message and policy row | `chupa/box.py`, `chupa/config.py`, `chupa/policy.py` |
| Roadmap table parser, `roadmap author`, `roadmap status`, row linking | new `chupa/roadmap.py`, `chupa/__main__.py` |
| Author data blocks | `chupa/author.py`, `chupa/specs/author.md` |
| Gate blocks | `docs/roadmap.md` (format), `chupa/roadmap.py` (runner) |
| `release`, `publish`, `release` config | `chupa/__main__.py`, new `chupa/release.py`, `chupa/config.py`; `dev.py` (`release`, `vscode-publish`) |
| Loop | `chupa/serve.py` (idle hooks), `chupa/drain.py` (between tickets), `chupa/notify.py` (digest) |
| Docs | `docs/how-chupa-works.md` §6.4-6.7, §7.1-7.2, §9.3, new "Roadmap driver"; `chupa/docs/host-running.md`; `chupa/specs/ask/drain-loop.md` |

## Ticket breakdown

Each ticket puts its tests in new files (`docs/parallel-tickets-plan.md` §7). Release 0.2.0, last group.

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| 1 | `superseded-settles` | bug | P1 | | Section 1. Evidence: the three split parents' journal histories ending `rejected` by hand. |
| 2 | `supervisor-rework` | feature | P1 | | Section 2: the trigger, the allowed-edit gate, `caps.supervise`, the supervisor keep and lineage, `rework.md` lift on escalation; `rework.md` spec bump. |
| 3 | `roadmap-author` | feature | P1 | | Section 3: `roadmap_row` message and policy row, `chupa/roadmap.py` parser, `roadmap author --ahead`, Author data blocks, row linking and striking, hand-test refusal. |
| 4 | `release-gates-as-commands` | chore | P2 | | Section 4: gate blocks in `docs/roadmap.md`, `roadmap status`. |
| 5 | `release-publish` | feature | P2 | `release-verb` | Section 5: `chupa release`, `chupa publish`, `./dev.py vscode-publish`, `release` config, the publish park. |
| 6 | `driver-loop` | feature | P1 | 1, 2, 3, 4, 5 | Section 6: the idle-point sequence in serve and drain, the digest, the rewritten `drain-loop` prompt, how-chupa-works "Roadmap driver". |

`Runs before`: `docs-truth-sweep` (roadmap row 4) and `contention-authoring-rules` (row 13) before every ticket here. Ticket 1 before 2 (the supervisor must not supervise a superseded parent).

## Risks

- **Ticket text oscillation.** A supervisor edit that the next run undoes, twice. `caps.supervise` (2) ends it and escalates with both proposals on record.
- **Authoring from a stale design.** A plan section written before 0.2.0's dedup can describe code that no longer exists. `--ahead 2` keeps the window short; the requisition review reads merged code; a row whose plan section is stale snags and escalates, which is the right outcome.
- **Publishing by mistake.** Only on `release.publish: true` and only after a gate passes; tags and bumps are local until then, and `git revert` plus a tag delete recovers a bad local release.
- **The driver edits `docs/roadmap.md`.** A ticket-plane commit on `main`, like lifts; a chat editing the same file at the same time trips `commit.lock`, which is what it is for.
- **A wrong ticket runs to its cap.** Nothing new: caps, Check, Review, and the requisition review stand. The driver adds attempts to fix the ticket, never a way around a gate.

## Open decisions

1. **`caps.supervise` default.** Proposed 2. One is the owner's "diagnose, apply, confirm" done once; two allows one retry on a bad proposal.
2. **Which terminals the supervisor takes.** Proposed: `premise_failed` and spent-cap routes only. `ticket_changed` and `abandoned` stay with the person.
3. **Row linking as a ticket-plane commit vs a journal-only record.** Proposed: the commit, so the roadmap file is true without running chupa. The alternative keeps `docs/roadmap.md` hand-edited and shows authored rows only in `roadmap status`.
4. **Digest cadence.** Proposed: after every settle while the operator's last verdict is older than a day, else daily.
