# Roadmap driver: plan

Run `docs/roadmap.md` unattended. The driver authors the next few roadmap rows when their dependencies have merged, never further ahead than that, so every ticket is written against the source as it is. When an eligible ticket is held for a person, the driver's supervisor step (rows 89 and 96) reads the diagnosis, edits the ticket within the supervising rules, has the edit reviewed, and keeps the ticket, a bounded number of times; before that step the operator did this by hand. When a release's rows are all merged and its gate passes, the driver bumps and tags the version through `clutch/release.py::release`, uploads to PyPI only when `release.publish` is set, and keeps the VS Code package for the owner's Marketplace upload (decision 20, row 108). Nothing waits on a person; the only outside input is a missing provider credential (section 7).

## Status

The supervisor, roadmap authoring, release gates, publish, and driver loop have merged (roadmap rows 89–93); the idle-point supervisor hook and kept release packages have also merged (`supervise-at-idle-point` (row 114) and row 108). Written 2026-11-14 at commit `c2d1c2a7` for `docs/roadmap.md`.

## Roadmap

Release 0.3.0, as its last group (`docs/roadmap.md` rows 89-93), after the truth-and-hygiene rows, because the driver is what runs 0.4.0 onward. Needs from the roadmap: `release-verb` (row 3) for tags and version bumps; `docs-truth-sweep` (row 4) so the documents the driver reads are true; `contention-authoring-rules` (row 13) in effect before it authors anything. What needs this plan: every later release, since the driver is how they run. Shared budgets: one new config block `release`, one new cap `caps.supervise`, one new Suggestion Box message class `roadmap_row` with its `box_policy` row. No CORE_TEMPLATE text: the chat-session rules do not change; the driver is an engine process bounded by caps and reviews, not a session.

## Why this is viable

Measured from this repo's journal at `c2d1c2a7`:

- 506 tickets merged. The operator issued 142 verdicts along the way: 78 keeps on held tickets, 28 kills (3 of them the engine's own split retirements, which `clutch/runner.py::reject_ticket` journals as `actor: operator`; box-000471), 36 draft confirms. About one touch per 3.6 merged tickets. The engine made 94 machine keeps on its own.
- The owner reports that nearly every keep was the same sequence: read the diagnosis, apply its suggested ticket edit, lint, review, confirm. That sequence is three existing engine pieces (Diagnose, Rework-update, machine keep) that are not wired together for this case.
- The kills the owner remembers as necessary were split parents, and the journal shows two kinds. The three stems whose split published (`chupa-ruff-config`, `split-test-serve`, `menu-mirrors-verb-admission`) were retired by the engine, not by a person: `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed`, so `clutch/status.py::reject_queue` never holds it, and retires it through `reject_ticket` within half a second of the `supersedes` signal (box-000471). The parents a person killed (`specs-in-package`, `vscode-help`, `vscode-help-registry`) were Rework splits that did not publish: the diagnosis said `split`, Rework failed, and the parent was routed to the Reject queue with no `supersedes` signal (box-000473). A Rework split that publishes, or the supervisor's reviewed retry (section 2), is what would have released them.
- Authoring from a plan already exists: the Author stage writes a ticket from a Suggestion Box message with a buildability review (`clutch/author.py::author`), and 44 of 442 box messages became tickets that way. A roadmap row is a message with a different shape.
- A drain of about 30 tickets ran unattended in about 4 hours (`README.md`); the self-upgrade handoff already lets a run continue across engine merges.

What this plan cannot remove is a missing provider credential. A prerequisite once run by a person becomes an agent-run capture; a GO baseline is measured against an AI label panel; a ticket with a wrong goal or scope goes through the diagnose path; and a publish waits on `release.publish` (`docs/roadmap.md` §6, decision 19).

## Current state

- **Rework-update and supervision handle terminal cases.** `runner.drive` requests Rework when the diagnosis verdict is `split` or the render was over bound (`clutch/runner.py:301-305`). Rework's `update` action rewrites a ticket, has `requisition_review` judge it, and commits it as `clutch(<stem>): rework` (`docs/how-clutch-works.md` §6.5). Since rows 89 and 96, `failure_terminal` also runs `supervise_step` for a `premise_failed` or spent-cap terminal routed to the Reject queue, from `runner.drive` and `TicketWriter.consume_result`; row 114 runs it at the idle point through `supervise_idle`.
- **A machine keep never resets caps.** The lineage a cap counts over starts at the last operator or supervisor keep (`clutch/caps.py::lineage`); `caps.supervise` bounds supervisor keeps (`clutch/caps.py::supervise_draws`, row 89). `record_reoffer` journals `actor: machine` keeps (`clutch/drain.py:106`), which re-offer a stem with budget left but cannot release one whose cap is spent. `awaiting_operator` (`drain.py:92-95`) holds any stem with a spent cap or a `ticket_changed` reason; an operator keep releases the hold, and a supervisor keep also releases a spent-cap hold by starting a new lineage.
- **A published split retires its parent.** `record_supersedes` journals the map (`clutch/rework.py::record_supersedes`); dispatch skips superseded stems and dependents wait on the successors. `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed`, so `clutch/status.py::reject_queue` never holds it, then retires it through `clutch/runner.py::reject_ticket`: `state: rejected`, a `clutch(<stem>): rejected` commit, and a `reject_verdict kill` journaled with `actor: operator` although no person acted (box-000471). `tests/integration/test_ladder.py::test_split_dispatches_reviewed_rework` pins that order. A Rework split that does not publish turns the verdict into `reject`, and the parent is routed to the Reject queue like any other reject.
- **Author takes a box message.** `author(checkout, driver, box, message, pass_no)` chooses its policy row from the message class (`clutch/author.py:210`), embeds the authoring guide and skeletons, and runs the requisition review. Triage invokes it (`clutch/triage.py:272,328`). There is no other way in.
- **Release tooling is merged.** `clutch release --minor|--patch` (`clutch/release.py::release`, merged in `release-verb`) bumps the version with `uv version`, commits `pyproject.toml` and `uv.lock` as `release: <version>`, and tags `v<version>` at that commit; it journals a release signal. `clutch publish` builds the version whose `v<version>` tag is on HEAD and uploads it to PyPI only when `release.publish` is enabled; it never bumps the version (row 92, box-000480). The VSIX is a configured release package that `clutch/release.py::run_packages` builds and keeps at ship (row 108).
- **The supervising prompt is a chat.** `clutch prompt drain-loop` renders the babysitting instructions for a Claude Code chat (`clutch/specs/ask/drain-loop.md`), whose allowed edits are the CORE_TEMPLATE supervising list: lint and format fixes, a missing fence or Context entry, a stale path, or a wording update. The supervising session may confirm or reject and edit any ticket only as a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation names (decision 19, row 103).
- **serve has idle hooks.** Retros run at the next idle point after a settle (`clutch/serve.py::check_retro`, `run_retro`), and `upgrade_idle` gates the self-upgrade. The driver's steps attach at the same points.
- **The roadmap is readable by machine.** Its master table rows carry stem, owner, kind, priority, depends, runs-before, and content; the release sections give the order; §9 says a row links its stem when authored and is struck when merged.

## Departures from the design record

| Record says | This plan | Why |
|---|---|---|
| §18.1 refuses "multiple authoring modes" | A second input to the one Author stage: a `roadmap_row` box message | The Author stage, its guide, its skeletons, and its review are unchanged; only the message shape differs. One authoring process, as `CLAUDE.md` requires |
| `docs/how-clutch-works.md` §6.4: "Editing `ticket.md` never resets a cap; only an operator `confirm` does" | A supervisor keep resets the lineage like an operator keep, at most `caps.supervise` times per lineage, and only after a reviewed Rework-update changed the ticket | The owner asked for it on 2026-11-14 after doing this by hand 78 times. The bound and the review are what make it safe; a supervisor keep on unchanged text is refused |
| CORE_TEMPLATE: a supervising session may not confirm or reject | The supervisor is an engine stage under a cap and a review, journaled with its own actor. The supervising agent loop confirms or rejects only by executing a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation (open decision 5) | The owner delegated those verdicts on 2026-11-15 (`docs/roadmap.md` §6, decision 19). box-000508 was declined; row 103 (`core-template-supervisor-verdicts`) owns the change and has merged |

`CLUTCH_PLAN.md` stays frozen. The tickets update `docs/how-clutch-works.md` §6.4-6.7, §7.2, §9.3, and a new "Roadmap driver" section.

## Target design

### 1. ~~Superseded is settled (`superseded-settles`)~~

Struck: the premise is false (see Current state). A published split already retires its parent, which never enters the Reject queue, and the split parents a person killed carry no `supersedes` signal, so a `superseded` state would release none of them (box-000471, box-000473).

### 2. The supervisor step (`supervisor-rework`)

Runs in the shared terminal handling used by `runner.drive` (after Diagnosis) and merge-route `TicketWriter.consume_result`, for a `premise_failed` terminal routed to the Reject queue or a routed `gate_failed` with a spent cap. Every attempt journals one `supervisor_attempt` signal naming the stem in its body before Rework and before the terminal, whether approved, refused, or escalated:

1. **Propose.** Rework-update with the diagnosis lessons and findings as input, exactly as today's Rework. `clutch/specs/rework.md` gains the supervising rules as the allowed-edit list for this trigger: fix lint and format, add a missing fence or Context entry, correct a stale path, reword; never change `Goal / Why`, remove an acceptance criterion, or widen scope. A proposal that touches `Goal / Why` or drops a criterion is refused by a gate before review, with the road "the proposal escalates (step 4)".
2. **Review.** `requisition_review` judges the proposal as it judges every Rework proposal, with the prior review's findings and the diff since (how-clutch-works §6.7).
3. **Keep.** On approve, the engine commits the proposal (`clutch(<stem>): rework`) and journals `reject_verdict keep actor: supervisor`. A supervisor keep starts a new lineage, like an operator keep, when and only when the committed ticket text changed. `caps.supervise` (default 2) bounds supervisor keeps per operator lineage; the draw is a `cap_consumed` event.
4. **Escalate.** A refused or snagged proposal, a spent `supervise` cap, or a proposal the gate refused leaves the stem in the Reject queue with the proposal attached (`tickets/<stem>/rework.md`). The supervising agent loop releases or retires it (open decision 5), starting from the engine's best attempt.

`ticket_changed` holds are not supervised by this step; the supervising agent loop releases them (open decision 5). Premise parks at the requisition stage already release on a ticket edit; the supervisor's edit releases them the same way, with the same review.

### 3. Roadmap authoring (`roadmap-author`)

- A new Suggestion Box message class `roadmap_row` (`clutch/box.py:18`), with a `box_policy` row (`clutch/config.py`) defaulting to `confirmed` regardless of the review baseline (open decision 5; `roadmap-row-message` builds it). The other draft conditions in `docs/how-clutch-works.md` §9.3 still apply; a draft they make is released like every Author draft (open decision 5).
- `clutch roadmap author [--ahead N]` reads the master table, finds rows with no linked stem whose `Depends on` stems are all merged (or empty), in release order, and files one `roadmap_row` message per row until `N` (default 2) rows are open beyond the confirmed or running set. Each message carries the row's fields and the owning plan's path.
- Author handles a `roadmap_row` message with one new data block, `<<clutch-data:roadmap_row>>` (the row) and `<<clutch-data:plan>>` (the owning plan's Target design and Where-each-piece-lives sections, or the whole plan when under 40,000 characters), beside the guide and skeletons it already embeds. The stem is the row's stem; `requisition_review` runs as for every authored ticket; a capture prerequisite refuses a row whose content says "after its agent capture" until the evidence file it names exists under `tickets/<stem>/evidence/`. A row needing a credential this machine lacks is skipped (section 7).
- On commit, the driver edits the roadmap row to link the stem (`clutch(roadmap): author <stem>`), a ticket-plane commit like a lift. When the ticket merges, the row is struck. The roadmap stays true because the driver, not a person, keeps it so.
- `--ahead` is the whole point: two rows, not twenty. A row authored against source that later rows change is a row authored too early.

### 4. Gates as commands (`release-gates-as-commands`)

- Every gate is a command; no gate is a judgment a person makes. Each release section in `docs/roadmap.md` gains a fenced `gate` block with argv commands over recorded facts, including the suite, a `status` query, a `training export` count, the count of tickets merged under parallel serve without a conflict-rerun cap hit, and the recorded `visual_baseline` GO.
- `clutch roadmap status` reports rows blocked on a capture or a missing credential, rows merged, authored and open, the gate's last result, and the next rows to author. Read-only; the extension draws it later.

### 5. Release and publish (`release-publish`)

- `clutch release --minor|--patch` exists (`release-verb`; see Current state). This ticket adds its `release` journal signal. Hosts use the same verb for their own versions.
- `clutch publish`: never bumps the version. It uploads the version in `pyproject.toml` only when its `v<version>` tag is on HEAD, and refuses otherwise (box-000480). It builds and uploads to PyPI through the exec seam, with the token's env name in config (`release.pypi_token: UV_PUBLISH_TOKEN`), passed only to that child, like a provider key. The owner publishes the kept VS Code package to the Marketplace by hand (roadmap decision 20).
- **Authorization.** Publishing is a remote mutation. `release.publish: true` in config is the owner's standing "push"; with it absent or false, the driver tags and bumps locally and does not publish. The conduct rule for chat sessions ("never push unless the user says push this turn") is untouched: the engine acts on config, sessions act on words.

### 6. The loop (`driver-loop`)

At serve's idle point after each settle, in this order:

1. If any Reject-queue stem is unsupervised, the supervisor step runs for it (section 2) before new work. The step also runs in `runner.drive` and merge-route `TicketWriter.consume_result`; the idle-point hook uses `supervisor_attempt` to identify attempted stems and the key scope from `supervisor-effect-scope`.
2. `roadmap author --ahead N` tops up the open rows (section 3).
3. If the current release's rows are all merged and its gate passes (section 4), `release` runs, then `publish` only when `release.publish` is true (section 5); the next release becomes current.
4. A digest notification through `config.notify` (exists): rows merged since the last digest, held stems and why, the next rows to be authored, spend.

`drain` runs steps 1 and 2 between tickets; serve runs them at its idle point. `run` gets none of these idle-point steps, but its `runner.drive` terminal handling runs the supervisor step. `clutch prompt drain-loop` describes what the driver does by itself and what the supervising agent loop it starts does for a held stem or an Author draft (open decision 5); no step waits on a person.

### 7. What still comes from outside

Escalations go through the supervisor (section 2) and the diagnose path (`docs/how-clutch-works.md` §6.3-6.5). A stem the supervisor escalates, a `ticket_changed` hold, a Diagnose `reject` or `abandon-human` stem, and an Author draft are released by the supervising agent loop executing a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation (open decision 5). The only external input is a missing credential. Gemini has none on this machine, so rows needing it are skipped while an agent finds a route through the authenticated providers. Publishing follows `release.publish` and never a per-release person.

## Where each piece lives

| Piece | Home |
|---|---|
| Supervisor trigger, keep, cap | `clutch/runner.py` (terminal handling), `clutch/caps.py` (`supervise`, lineage), `clutch/config.py` |
| Allowed-edit list and gate | `clutch/specs/rework.md`, `clutch/rework.py` |
| `roadmap_row` message and policy row | `clutch/box.py`, `clutch/config.py`, `clutch/policy.py` |
| Roadmap table parser, `roadmap author`, `roadmap status`, row linking | new `clutch/roadmap.py`, `clutch/__main__.py` |
| Author data blocks | `clutch/author.py`, `clutch/specs/author.md` |
| Gate blocks | `docs/roadmap.md` (format), `clutch/roadmap.py` (runner) |
| `publish`, `release` config, `release` signal | `clutch/__main__.py`, `clutch/release.py`, `clutch/config.py`; `dev.py` (`vscode-package`) |
| Loop | `clutch/serve.py` (idle hooks), `clutch/drain.py` (between tickets), `clutch/notify.py` (digest) |
| Docs | `docs/how-clutch-works.md` §6.4-6.7, §7.1-7.2, §9.3, new "Roadmap driver"; `clutch/docs/host-running.md`; `clutch/specs/ask/drain-loop.md` |

## Ticket breakdown

Each ticket puts its tests in new files (`docs/parallel-tickets-plan.md` §7). Release 0.3.0, last group.

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| 1 | ~~`superseded-settles`~~ | bug | P1 | | Struck: premise false (Target design section 1). |
| 2 | `supervisor-rework` | feature | P1 | | Section 2: the trigger, the allowed-edit gate, `caps.supervise`, the supervisor keep and lineage, `rework.md` lift on escalation; `rework.md` spec bump. |
| 3 | `roadmap-author` | feature | P1 | | Section 3: `roadmap_row` message and policy row, `clutch/roadmap.py` parser, `roadmap author --ahead`, Author data blocks, row linking and striking, capture refusal. |
| 4 | `release-gates-as-commands` | chore | P2 | | Section 4: gate blocks in `docs/roadmap.md`, `roadmap status`. |
| 5 | `release-publish` | feature | P2 | `release-verb` | Section 5: the `release` signal, `clutch publish`, `release` config, publish only under `release.publish`; decision 20 made Marketplace publishing manual. |
| 6 | `driver-loop` | feature | P1 | 2, 3, 4, 5 | Section 6: the idle-point sequence in serve and drain, the digest, the rewritten `drain-loop` prompt, how-clutch-works "Roadmap driver". |

`Runs before`: `docs-truth-sweep` (roadmap row 4) and `contention-authoring-rules` (row 13) before every ticket here.

## Risks

- **Ticket text oscillation.** A supervisor edit that the next run undoes, twice. `caps.supervise` (2) ends it and escalates with both proposals on record.
- **Authoring from a stale design.** A plan section written before 0.3.0's dedup can describe code that no longer exists. `--ahead 2` keeps the window short; the requisition review reads merged code; a row whose plan section is stale snags and escalates, which is the right outcome.
- **Publishing by mistake.** Only on `release.publish: true` and only after a gate passes; tags and bumps are local until then, and `git revert` plus a tag delete recovers a bad local release.
- **The driver edits `docs/roadmap.md`.** A ticket-plane commit on `main`, like lifts; a chat editing the same file at the same time trips `commit.lock`, which is what it is for.
- **A wrong ticket runs to its cap.** Nothing new: caps, Check, Review, and the requisition review stand. The driver adds attempts to fix the ticket, never a way around a gate.

## Open decisions

Decided 2026-11-16 (`docs/roadmap.md` §6, decision 19): items 1-4 take their Proposed option and item 5 records the owner’s delegation.

1. **`caps.supervise` default.** Proposed 2. One is the owner's "diagnose, apply, confirm" done once; two allows one retry on a bad proposal.
2. **Which terminals the supervisor takes.** Proposed: `premise_failed` and spent-cap routes only. `ticket_changed` and `abandoned` are not supervised; open decision 5 covers `ticket_changed`, and an `abandoned` stem stays eligible (`docs/how-clutch-works.md` §6.7).
3. **Row linking as a ticket-plane commit vs a journal-only record.** Proposed: the commit, so the roadmap file is true without running clutch. The alternative keeps `docs/roadmap.md` hand-edited and shows authored rows only in `roadmap status`.
4. **Digest cadence.** Decided: after every settle.

5. **Holds that ended with a person.** Decided 2026-11-16 (owner delegation of 2026-11-15). (a) A stem the supervisor escalates, a `ticket_changed` hold, and a stem a Diagnose `reject` or `abandon-human` verdict routes to the Reject queue are released by the supervising agent loop. It runs `clutch prompt diagnose <stem>` and executes its Recommendation: a ticket edit, then `clutch lint` until it exits 0 and `clutch review` until it approves, then `clutch confirm --yes <stem>`; or `clutch reject --yes <stem>`. A cause fix the diagnosis names goes to `clutch suggest` and is never authored. (b) An Author draft from triage is released the same way, through `clutch prompt drafts` and its Recommendation. (c) A `roadmap_row` ticket starts `confirmed` regardless of the review baseline (`roadmap-row-message`), so no `roadmap_row` draft waits on the baseline. One that another draft condition makes is an Author draft under (b).
