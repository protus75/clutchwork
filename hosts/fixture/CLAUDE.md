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

# Score game

Host content lives in app.py and settings.json.
