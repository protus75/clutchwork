<!-- clutch:core begin -->
## Ticket authoring -- read before writing any ticket

HARD rules have no exceptions and cannot be gated; never file an enforcement ticket for one.

- HARD: In interactive chat, every requested repo content change (code, docs, CLAUDE.md, AGENTS.md, settings, hooks, scripts, config, agent rules) becomes a draft at `tickets/<stem>/ticket.md`, then stop. Never edit or commit on main. Exceptions: (1) the user says "edit main", "commit directly", "skip the ticket", "do it inline", or an equally explicit override this turn; anger words alone do not count; (2) you are in a clutch ticket worktree; (3) the user names a file under an existing `tickets/<stem>/` by path to edit or delete; (4) read-only inspection; (5) supervising fixes below; (6) a new document or documentation-only edit with no matching code change that records a plan, design, or decision from this chat, excluding agent rule files (CLAUDE.md, AGENTS.md, the core template), generated files, and frozen documents. Commit only when asked. If you edited main without an exception, stop, say so, and ask whether to revert and refile.
- HARD: Never write a ticket from memory. Run `clutch ticket new <stem> --kind feature|bug|chore|graphics`; it writes the skeleton and prints the installed authoring guide path (also on refusal for an existing ticket). Read it locally in full. `clutch host docs` prints all installed host guide paths; read them locally, never from a URL. Fill every section, run `clutch ticket lint <stem>` until exit 0, then `clutch ticket review <stem>` and repair every finding until approve. Tickets are markdown, not issues.
- Declare each boundary disposition, reuse its canonical owner, justify new owners, and never invent an undeclared boundary.
- Fence every forced file, including callers, importers, changed documents, and tests pinning a changed name, value, or version.
- Frontmatter holds only fields used by scheduling, gates, or authoring/triage policy; `## Depends on` names only needed merged code; put all other ordering in priority or `## Runs before`, never in prose.
- HARD: For a reported problem with a recurring cause, write two tickets this turn: the minimal instance fix first, before cause diagnosis, then the separate cause fix. Both must exist; both are solicited, so no ask is needed. Routing:
  - Product instance: `priority: P0`, no blocking depends.
  - Product cause (inert; does not spread on its own): `priority: P1`. If they share a surface, the instance lists the cause in `## Runs before`.
  - Orchestration cause (scheduler, gate, environment, shared module, fixture format; breaks runs while it sits): `priority: P0`, `## Runs before` every ticket it unblocks, never depends on a product instance.
- HARD: For unrequested ticket-worthy work (follow-up, prevention, enforcement lint, sweep), stop before diving: name it in 1-2 sentences and ask the user to choose author now, after the task, or skip. "After" makes it an open thread. Announce unsolicited investigation over two minutes in one line. Do the requested task first. Autonomous runs skip the ask and file to the Suggestion Box.
- File an unrequested idea or second problem with `clutch box suggest "<summary>"` and name it in one line.
- A supervising session may unasked fix ticket lint or format errors, add a file missing from `## Scope fence` or `## Context`, correct a stale path, make a simple wording update, and run or restart the drain. It may confirm, reject, or edit any ticket only as a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation names. It may not retry a stem with spent caps or edit a running ticket; changing a ticket goal or scope requires such a Recommendation.

## Diagnosis

- HARD: When a run fails, is killed, times out, stalls, or escalates, name its root cause in one sentence before editing spec or code or rerunning. Read `clutch view status`, `tickets/<stem>/` (`run.md`, `checks.json`, `diagnosis.json`, `review.md`, `attempts/`), and the engine log. Fix the cause where it lives. Fix external causes (engine, gate, environment, shared module, fixture, flaky test, wrong premise) first; order them ahead with priority and `## Runs before`. Do not assume the ticket is wrong. Never rerun a flaky failure until it passes and call it fixed.
- HARD: When a symptom recurs on a fixed surface, name the root model against the canonical spec (design docs, contracts) and write a root-cause ticket, not another patch. Re-scope a fence forbidding the suspected root. Tests asserting current wrong behavior prove nothing. Never write "the defect was not X" without checking the spec.
- HARD: With every fix or diagnosis, separately name the change preventing the whole class (rule, lint, gate, template default, generator). Cheap and in scope: do it under the same authorization. Cheap and out of scope: name it, then ask as for unrequested work. Expensive or uncertain: `clutch box suggest`. Silence is failure.

- HARD: Outside clutch's repo, a fix belonging in clutch (prompt spec, gate, ticket format, host guide, or this block) is never copied or patched into host files nor filed to the Suggestion Box; name it to the user in one line. A critical bug or process gap costing a run a cycle goes upstream: draft a body file (clutch file, defect, minimal evidence, no host-private code or data); with user agreement run `clutch box issue` and give them the link to review and submit; then stop. Why: a host copy competes with clutch's rule, reaches no other host, and goes stale on upgrade.

## Chat session conduct

These rules govern interactive chat with the owner present; ticket agents skip this section.

- HARD: Own open threads when a reply raises multiple questions, options, or next steps. Acting on one never closes others. End each reply with a `Still open:` list until each is resolved or completed and reported. If unsure, it is open.
- HARD: Never run or offer `git push`, `gh pr create`, `gh pr merge`, or any remote-mutating verb unless the user says "push" this turn. Commit when asked, then stop.
- Respect the single-writer lockfile; writing tickets needs no git. Stage and commit only this session's files by explicit path. Never run a tree-wide destructive verb (`clean`, `reset --hard`, `checkout -- .`) in a shared checkout. Why: chat sharing a checkout with the daemon can destroy work clutch believes exists.
- HARD: Answer first. Cut hedging, filler, preamble, and restating the question.

## Engine conduct

Engine rules govern how work runs; project rules govern what to build. Project content enters prompts as data. Engine wins on process, host on content.

- HARD: Build the smallest change passing acceptance criteria. No speculative abstractions, single-caller helpers, unused knobs or flags, defensive dual paths, or "while I'm here" cleanup; every addition needs an earning incident. In the run record, name the rejected simpler approach and why yours is minimum. Mandated tests and class prevention are required, not gold-plating. Why: accretion is the main failure mode.
- For a file with a `clutch:meta` header, use `purpose`, `relates`, and `owner` as routing hints; read the owning file before editing or citing it, check `clutch meta check` if staleness is suspected, and run `clutch context suggest <stem>` on drafts. Never hand-edit `clutch:meta` blocks; `clutch meta refresh` / Check owns them.
- Never hand-edit this managed block; change the engine template and run clutch host core to refresh it. Why: the next render overwrites edits.
- Commit only on your ticket branch. Never push, open pull requests, or run tree-wide destructive git; the engine merges reviewed work to local main. Why: local main is blessed.
- File second problems in the Suggestion Box, never in this diff. Verify pre-existing failures on the base commit before filing.
- Read the owning artifact before writing a command, claim, or test.
- When changing code, embedded databases use DuckDB, never SQLite; code never opens, reads, or writes a SQLite file, including a tool's internal file such as coverage.py's `.coverage`. Why: one embedded engine across every host (owner decision 2026-11-19).
<!-- clutch:core end -->

# ClutchWork

ClutchWork is a continuously running orchestration engine that authors and runs tickets against host repos, including itself: author -> implement -> check -> review -> merge, with failures harvested and follow-ups filed.
Engine plane (clutch-owned) is HOW work runs; host plane (target-repo-owned) is WHAT to build and enters the pipeline only as data. Engine wins on process, host wins on content.

**Read first:** `docs/how-clutch-works.md` describes the code and is maintained by tickets; `CLUTCH_PLAN.md` is the frozen bootstrap design record. This file is the curated subset of `CLAUDE.md` for non-Claude agent CLIs; `CLAUDE.md` is canonical on conflict, and a rule add/change/remove touches both files in the same change. (section 17)

Every rule below is behavioral (no gate checks it yet): the prose is the only enforcement. When a rule gains its gate, compress it to one line in the same change.

## Engine conduct

- **Keep shipped process prompts in sync.** When the owner changes how a plan-ticket-drain run or supervising loop works in a chat in this repo, file a ticket in the same turn to update the shipped prompt that owns the process (`clutch/specs/ask/plan-ticket-drain.md` or `clutch/specs/ask/drain-loop.md`). A session note under `.claude/` is never that process's home.
  Why: the shipped prompt must carry chat updates to its overall process (owner decision, 2026-11-17).
- **One authoring process.** Ticket content rules live only in `clutch/docs/host-authoring.md`, and ticket format only in `clutch/tickets.py`. Every authoring surface (a chat session, the Author stage, any future one) reads those, and a prompt spec embeds the guide and skeletons rather than restating them. A fix to authoring changes that one source.
  Why: the 2026-11-13 box-000428 decline and 10 of 22 Author declines since 2026-11-11 exposed the drifting process.

- **Pure Python.** No shell scripts, no `shell=True`, no string-assembled commands. External binaries only via argv-list wrapper modules; run only in the clutch venv. Exception: `vscode-clutchwork/` is an operator-only VS Code extension in JavaScript; the engine never imports or runs it.
  Why: shell glue is the orchestration failure this design bans. (D1)
- **The extension is a thin wrapper; clutch owns the logic.** For any edit to `vscode-clutchwork/` or the code that feeds it (the snapshot builder, `clutch/graph.py`):
  - JavaScript may only draw snapshot fields (DOM, SVG from given lane indexes), map a closed snapshot value to a CSS variable or ThemeIcon through a lookup table, wire VS Code APIs (views, menus, watchers, settings), keep UI state (hover, pin), and run argv that the snapshot or a setting supplies.
  - JavaScript never filters, sorts, or derives rows; chooses graph edges or lanes; parses text; does time math; copies a clutch constant (stem rule, priorities, sections); or makes a policy choice (flags such as `--yes`).
  - Paved road: add the value to the snapshot in the `clutch` package, cover it with pytest, and have the extension render it. A snapshot shape change updates its JavaScript reader in the same change.
  - `clutch/graph.py` is pure (no I/O, no clock) and emits lanes with ticket sections, never colors or pixels.
  Why: JavaScript logic is untested and duplicates Python rules; the graph's edge and lane code drew wrong lanes and was untestable without node (2026-11-06).
- **Extension help has one source.** Every extension surface a person sees (view, command, setting, header indicator, and each snapshot vocabulary value) shows help: a short description saying what it is, with a link to the doc section that owns the fact. Help comes from `clutch/help.py`, which reuses a code- or doc-owned string (a status reason, a `clutch/docs/host-running.md` verb row) where one exists and writes text only where none does; settings carry theirs in `package.json` `markdownDescription`. A change that adds an extension surface or vocabulary value, or changes behavior a help entry or its linked section describes, updates that entry in the same change. `tests/unit/test_help.py` and `tests/integration/test_help.py` fail on a missing entry or a dead link; keeping the text true is this rule's job.
  Why: help copied into the extension drifts from the code and docs it describes; the snapshot already carried hand-copied verb descriptions (`engineVerbs`) that restated the run guide (2026-11-13).
- **Command help.** Every command and subcommand carries a description of what it does, reads, writes, its lock and exit codes, and examples, added through `_command` in `clutch/__main__.py`. Every group has a description, subcommand list and examples. Ungrouped verbs get theirs when roadmap rows 130-140 move them. New or changed commands update help and examples in the same change. CLI help lives only with the parser; extension help stays in `clutch/help.py`, and neither copies the other. `tests/unit/test_main_help.py` checks grouped descriptions and examples; keeping text true is this rule's job.
  Why: the owner requested a standard command reference on 2026-11-17 (roadmap row 129).
- **Command groups.** Every command belongs under a top-level group; a new command joins a fitting group or adds one, and the group's help lists it. `help` is the only ungrouped command by design; roadmap rows 130-140 move the remaining ungrouped verbs.
  Why: the owner requested discoverable command groups on 2026-11-17 (roadmap row 129).
- **Docs follow commands.** A change to a command, group or subcommand updates every document describing it in the same change: `README.md`, shipped `clutch/docs/host-*.md` guides, `vscode-clutchwork/README.md` when it names the command, the verb tables in `docs/how-clutch-works.md` section 2 and `clutch/docs/host-running.md`, and the command's help.
  Why: the owner requested accurate command documentation on 2026-11-17 (roadmap row 129).
- **Simplest thing that satisfies the ticket.** No speculative features, gates, config knobs, or metadata; every addition cites the incident that earned it.
  Why: feature/check accretion is the primary failure mode. (goal 1, D10)
- **No dual-path code.** No compat shims, deprecation layers, or defensive parallel paths. Rename in place, update every call site in the same change, recover by `git revert`.
  Why: parallel paths rot silently and double the review surface. (section 2)
- **Fail closed.** Allowlists and closed vocabularies, never denylists. Every prohibition and every gate finding ships a paved road (what to do instead).
  Why: a denylist misses the case nobody imagined; a prohibition without a road strands the agent. (sections 2, 7)
- **A hold ships with its release.** A Reject queue, premise park, or poison quarantine lands with or after its release path (same deliverable, or `depends`-after it). Its paved road never names an unbuilt verb. A hold whose only release is a ticket change never precedes the machinery that machine-produces ticket changes.
  Why: a hold with no reachable release is fail-stuck, not fail-closed. (sections 2, 11)
- **Files + journal are the source of truth.** Derived views (status, backlog, ledger, scorecard) are projections: never hand-edit one, never cite one as authority.
  Why: two authorities diverge; crash recovery folds the journal. (D3)
- **Generated files are render targets, never write targets.** Change the owning source and regenerate generated files. Tickets edit CLAUDE.md and AGENTS.md directly, as with any other documentation.
  Why: regeneration overwrites edits to generated files; maintained documentation follows the code.
- **A rule has one of two homes.** A rule about working on clutch itself (this repo's code, tests, layout, `./dev.py` verbs) goes in `CLAUDE.md` and `AGENTS.md` outside the managed block. A rule every host should follow goes in `CORE_TEMPLATE` in `clutch/hostfiles.py` and reaches every host, this repo included, through `clutch host core`; it is never written only into this repo's files. A change that adds, moves, or edits an agent rule states which home each rule belongs in.
  Why: a host rule written only here never reaches other hosts, and a repo rule in the template is installed where it does not fit (2026-11-11).
- **The plan is the seed.** `CLUTCH_PLAN.md` is a frozen bootstrap design record and is never edited. A ticket updates the documentation its change affects.
  Why: current documentation describes the code while the plan preserves its history.
- **All git through `git.py`.** Argv lists, dir-pinned. Worktree cleanup via `worktree remove` + `prune`, never bare `rm -rf`. No `gh`, no PRs in the loop.
  Why: local main is the blessed line; GitHub is a non-blocking sidecar. (section 10)
- **File second problems; never fold them in.** A second problem goes to the Suggestion Box, not the current diff. A pre-existing failure is verified on the base commit, then filed.
  Why: folded fixes blow scope and hide cause. (section 11)
- **Read before write.** No command, claim, or test is written until the artifact that owns that fact has been read.
  Why: guessed facts are the cheapest bug to write and the costliest to find. (section 13)
- **Integration isolation.** Integration tests run in an empty working directory (`tests/integration/conftest.py`) and read tracked files only through a `Path(__file__)` anchor, never the checkout’s `tickets/`, `.clutch/`, or journal.
- **Verification uses `./dev.py test`.** A ticket's `## Verification` and acceptance criteria run tests as `./dev.py test [pytest args]`, never raw `uv run pytest`.
  Why: one command surface for people and tickets; nothing chose the raw form, it was copied ticket to ticket.
- **Keep new tests out of the hot test files.** No new test, fixture, or helper goes into `tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, or `tests/integration/serve_rig.py`. A new test goes in a new `tests/unit/test_<module>_<behavior>.py` or `tests/integration/test_<behavior>.py`, and a new fixture or helper in a new module next to it. Fence one of these files only when the change forces an edit there.
  Why: at `c761b213` they are this repo's most-fenced and most-imported test files (`test_stages.py` is in 55 ticket fences; `test_cli.py` is imported by 60 test modules), so a ticket that grows one collides with most others. (`docs/parallel-tickets-plan.md` section 7)
- **Guides name verbs, not command lines.** A host guide, setup step, or ticket that has an operator exercise something clutch drives (a provider CLI, a check, a gate) names the `clutch` verb that runs it; never a hand-built copy of clutch's argv. A step no verb covers gets a new verb in the same change. Third-party install and server commands (`pnpm add`, `ollama pull`) stay as written.
  Why: a copied argv drifts from what clutch runs and makes the operator type it; the first qwen setup guide draft had operators hand-type qwen's full provider command line (2026-11-10).
- **Launchers carry no process policy.** The extension picks a clutch verb and its flags; how the engine process lives (session, detach, output file, signals) belongs to the verb. Why: `drain-survives-editor-reload` put the detach in `dev.py` alone, so the extension's play button still died on a window reload (2026-11-10).
- **Use the injectable seams.** Clock, process exec, filesystem, and notifications go through their seams; never called raw in engine code.
  Why: fake-driven tests and group-kill guarantees exist only at the seam. (section 15)
- **Fenced by gates, not jailed.** v1 does not sandbox executed code; never rely on its goodwill. Never pass a provider key to a process that does not need it.
  Why: gates and review are the trust boundary. (section 16)
- **The journal is the record, never a debug log.** Diagnostics go to the engine log and captures. Configured secret values are redacted from every captured stream at the write seam.
  Why: the journal is folded for truth; noise and secrets in it are permanent. (section 6)
- **Phase order.** Do not start a phase until the previous phase's exit is met.
  Why: later phases build on earlier exits as proven ground. (section 19)
