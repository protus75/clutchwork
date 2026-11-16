---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- tickets/plan-drain-prompts/evidence/large-automated-effort.md
- tickets/plan-drain-prompts/evidence/roadmap-loop.md
- tickets/plan-drain-prompts/evidence/author-brief.md
- tickets/plan-drain-prompts/evidence/author-roadmap-rows.js
- clutch/ask.py
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/review.md
- clutch/specs/ask/diagnose.md
- clutch/docs/host-authoring.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- clutch/roadmap.py::author_ahead
- clutch/roadmap.py::ship
- clutch/roadmap.py::drive
- clutch/doctor.py::check
- tests/integration/test_ask.py
- tests/unit/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop.py

## On-demand
- clutch/__main__.py

## Goal / Why
The owner asked on 2026-11-16: "I want the prompts used in this run to be in a commitable, easy recovered/regenerated as other clutch prompt types. Hosts will need to be able to run this kind of agent/process!!!!!" and "this is a 'plan ticket/drain', future will be a 'plan ticket/serve' process." They also asked that the run's prompt keep its end-of-phase acceptance step. Roadmap row 107 (`plan-drain-prompts`) records the request.

The run that took release 0.3.0 from plan to merged tickets used four session files that live only in one chat's untracked `.claude/` directory. Copies, with machine paths, another host, credential names, and shell launch commands removed, are this ticket's evidence:
- `tickets/plan-drain-prompts/evidence/large-automated-effort.md`: the kickoff prompt (section 3), the owner's corrections (section 2), and why each exists (section 4), including the "Closing each phase" acceptance step.
- `tickets/plan-drain-prompts/evidence/roadmap-loop.md`: the supervising loop. Its "Since drain-loop-agent merged" section lists what the session added on top of `clutch prompt drain-loop`: an exact engine-process match, the driver-wedge watch, and `clutch stop` at a ticket boundary for an urgent box message.
- `tickets/plan-drain-prompts/evidence/author-brief.md`: the hand-authoring brief.
- `tickets/plan-drain-prompts/evidence/author-roadmap-rows.js`: `COMMON`, `authorPrompt`, and `auditPrompt`. The adversarial audit found blocking defects in 6 of 8 tickets that `clutch review` had approved.

After this change any host renders that process from its installed clutch:
- `clutch prompt plan-ticket-drain` (no stem) prints the kickoff that runs the host's roadmap to completion unattended by authoring tickets and draining them. It covers the environment and credential checks, the owner's delegation, no person in the loop, gates counted in runs, the drift-sized authoring window, authoring that never holds the drain, the per-ticket audit, letting the engine's driver author, supervising each tick through `clutch prompt drain-loop`, and the phase-closing acceptance step whose gaps become roadmap rows.
- `clutch prompt author <stem>` prints the hand-authoring prompt for one ticket from its roadmap row or a request. The ticket need not exist yet; the prompt has the agent run `clutch new` itself.
- `clutch prompt review <stem>` becomes the adversarial audit of one ticket against the merged code and every confirmed, unmerged ticket that shares a file or an interface with it.

The prompts name `clutch` verbs, never argv copies, and carry no session-only fact: no machine shell, process path, other host, provider name, or `./dev.py` (which exists only in clutch's own repo).

Three design choices:
- **The audit is the `review` prompt, not a new kind.** `clutch/specs/ask/review.md` already asks for a review of one ticket against the merged code, listing what would stop it from passing Implement, Check, and Review. A separate `audit` kind would be a second prompt for the same job, which drifts (CLAUDE.md "No dual-path code"). So `review` gains the audit's checks and keeps its report-to-a-person format and "Recommendation" section. The kickoff's agent executes that Recommendation the way `clutch prompt drain-loop` executes diagnose Recommendations.
- **The session's additions to the drain-loop prompt go into the kickoff, not into `clutch/specs/ask/drain-loop.md`.** Ask prompts carry no `version`, so neither choice bumps a version. Editing the drain-loop prompt would add it and the two test files that pin its text (`tests/integration/test_ask_drain_loop.py`, `tests/integration/test_ask_drain_loop_agent.py`) to the fence. It would also change the loop for every host that runs it without a plan. The kickoff is a new file already in the fence, and every addition concerns a plan run whose driver keeps the drain busy.
- **The author prompt states procedure and limits only.** Section content rules live only in `clutch/docs/host-authoring.md` (CLAUDE.md "One authoring process"). So the prompt has the agent read that guide, whose path `clutch new` and `clutch docs` print, and never restates it. One content rule the run used is missing from the guide: cite code by symbol, never by line number. It is filed as box-000586, not copied into the prompt.

## Scope in / Scope out
In:
- `clutch/ask.py`: `KINDS` becomes `("diagnose", "running", "review", "box", "drafts", "drain-loop", "plan-ticket-drain", "author")`. The `drain-loop` branch of `render` also serves `plan-ticket-drain`: it reads `SPECS_DIR / "ask" / f"{kind}.md"` and substitutes only `state_dir`. `author` renders through the final branch unchanged (`stem`, `ticket`, `state_dir`). Nothing else in the file changes.
- `clutch/__main__.py`, inside `main`'s `handle_prompt` only:
  - The `drain-loop` branch also serves `plan-ticket-drain`. It refuses any stem with `runner.Refusal(f"{args.kind} takes no stem", f"run clutch prompt {args.kind} with no stems")` and prints `ask.render(args.kind, "", config, repo)`. The drain-loop refusal text stays byte-identical.
  - The "does not exist" refusal is skipped when `args.kind == "author"`. The one-stem rule and the `stem_findings` refusal still apply to `author`.
  - Nothing else in the file changes. The `prompt` parser already takes its choices from `ask.KINDS`.
- New `clutch/specs/ask/plan-ticket-drain.md`. Its only placeholder is `${state_dir}`, and it holds no other `$`. It does not start with `/loop `, because a loop would rerun the start-up checks every tick, and `clutch doctor` fails while an engine holds the lock. In this order it says:
  1. Role. Run the plan in the roadmap that `clutch roadmap status` reads, named by its path, to completion. Work unattended, authoring its rows as tickets and draining them, starting where `clutch roadmap status` says. Read every document under `docs/` first. Running this prompt is the owner's `standing delegation` of the operator role for the run; nothing waits for a person. Use only clutch verbs. A host with no roadmap file has no plan to run: say so and stop.
  2. Before you start:
     - `clutch doctor` exits 0. Run it before any engine starts, because its lock probe fails while one runs. If the clutch command itself does not start (for example after the checkout moved), repair the install first.
     - `clutch probe` reaches every declared provider. Start every engine from an environment where it passed: a credential set only in some shells fails the engine later.
     - List every credential, hand test, and owner decision the plan's prerequisites name. A missing credential is reported to the owner once, up front. Skip only the rows that need it and keep going.
     - `clutch release --minor` bumps and tags a release. The driver runs it itself when the current release's gate passes, and that is the bump before the next phase. So bump by hand only before the first phase, when the version does not yet name it, and `never twice` for one phase.
  3. Delegation:
     - Supervise through `clutch prompt drain-loop`, which carries the owner's delegation of the `clutch prompt diagnose`, `clutch prompt drafts`, `clutch prompt box`, and `clutch prompt running` Recommendations, `clutch confirm --yes` and `clutch reject --yes` included.
     - Every cause fix goes to `clutch suggest` and is never authored. Triage's verdict is final.
     - `No person is in the loop`:
       - a hand test is an agent-run capture committed as ticket evidence;
       - an open plan decision takes the plan's `Proposed` option; where there is none, three independent agents each propose one and a fourth judges, and a ticket records the choice in the plan;
       - calibration and baseline labels come from an AI panel of a `different model family` than the judge;
       - every gate is a command `counted in runs`, never wall-clock time, so "a week" or "daily" in a plan reads as a count of merged tickets.
     - `Never push`; publishing happens only through the driver under `release.publish: true`. Never run a tree-wide destructive git verb. Never edit code, docs, specs, config, or conduct files on main: tickets do that. The one exception is the roadmap rows of step 6, which this prompt authorizes.
  4. Authoring:
     - The engine's roadmap driver authors rows itself: drain and serve run it at start and after every settle. `Let the driver author`.
     - Between drains, top up with `clutch roadmap author --ahead <window>` (it takes the writer lock). Keep at most 4 roadmap tickets confirmed and unrun, or 2 after any `drift failure`: a premise park, or a requisition or review snag citing code an earlier merge changed. A drain with no drift failure returns the window to 4. Never author a row before every stem in its `Depends on` has merged.
     - Hand-author a row only when the driver cannot, and record why. That is when its author message was declined (the driver's `declined` line names the decision record), or when the driver authored nothing for two consecutive idle ticks while `clutch roadmap status` listed `next:` rows. When a decline shows the row itself is wrong (a false premise, or work already merged), reword or replace the row in step 6 instead.
     - Give each such row to its own agent with the output of `clutch prompt author <stem>`, the decline record if there is one, and this run's rules from step 3.
     - After `clutch review` approves a hand-authored ticket, give it to a separate agent with `clutch prompt review <stem>`, the adversarial audit. Carry out the ticket edits its Recommendation names, then run `clutch lint` until it exits 0 and `clutch review` until it approves. Stop editing a stem the moment it is dispatched.
     - Authoring overlaps the running drain: `never hold` or stop a drain for it.
  5. Supervising:
     - Each tick, render `clutch prompt drain-loop` and follow it. Its limits bind you except for this prompt's steps 4 and 6.
     - Match this checkout's engine exactly: `clutch status` and the writer lock say whether it runs. Another checkout on the machine may run its own `clutch drain`, so never match a bare process name.
     - Watch merges, holds, the Reject queue, the driver's `roadmap_drive` lines in `${state_dir}/engine.log`, and the engine exiting.
     - On any failure, name the root cause in one sentence from the stem's artifacts before acting. Classify it as drift or not, which sets the window, and file the class-prevention change with `clutch suggest`.
     - A drain can exit right after starting, before running any ticket, with an error from the roadmap driver step (a traceback in `${state_dir}/drain.out`). Nothing unattended can recover from that. Stop starting drains, and report the error and the roadmap row to the owner.
     - With the driver authoring ahead, a drain rarely quiesces, so the drain-loop prompt's between-drains Suggestion Box step can wait indefinitely. For a pending message whose cause wedges the engine or wastes runs, run `clutch stop` (the running ticket finishes first), take the message through that step, then restart the drain.
     - Keep a log that the next tick reads, recording every action, verdict, and filing. End each reply with a `Still open:` list.
  6. Closing each phase. Do this once `clutch roadmap status` shows no ready row left in the current release, and before its gate can pass:
     - A read-only agent reviews the release's merged rows, taken together, against its theme and ship gate and the owning plans' target design.
     - Every partial or unmet promise becomes a `P1 row` in that release's table, and a deferred one becomes a row in the next release's table. A gap is `never a Suggestion Box message`, so the gate waits on it.
     - A stuck row (its author message declined, or its stem rejected) gets a reworded or replacement row.
     - Write those rows into the roadmap and commit that one file by explicit path.
     - This step names no verb, because no merged verb runs the review yet.
  7. Final report, terse:
     - merged this run, and releases tagged;
     - tickets hand-authored and why;
     - verdicts executed;
     - fixes made;
     - suggestions filed;
     - roadmap rows added or reworded;
     - reports to the owner;
     - a `Still open:` list.
- New `clutch/specs/ask/author.md`. Its placeholders are `${stem}` and `${ticket}`, and it holds no other `$`. In this order it says:
  1. Author the clutch ticket `` `${stem}` `` at `${ticket}` from its request: the roadmap row whose stem is `${stem}` when the roadmap has one, else the request given with this prompt. Decisions given with this prompt or recorded in the roadmap override the plans. Other agents may author other tickets in this checkout, and a drain may be running.
  2. Limits:
     - Write only under `tickets/<your stems>/` and a scratch directory of your own outside the checkout. Never edit code, docs, specs, config, conduct files, or another ticket.
     - Run no git verb that writes. Never run `clutch drain`, `clutch run`, `clutch serve`, `clutch confirm`, `clutch reject`, `clutch triage`, `clutch dismiss`, `clutch stop`, or `clutch kill`.
     - `clutch review` commits your ticket through intake; that is the only commit you cause.
     - A running drain's intake commits any edited ticket it sees. So edit a copy in your scratch directory and replace the ticket file with it in `one write`. Before each write, once every stem in its `Depends on` has merged, run `clutch status` and stop if the stem is in flight.
     - Second problems go to `clutch suggest`, never into the ticket. A cause fix is always filed, never authored.
     - If `clutch review` fails with a provider error, drought, or rate limit (not a verdict), wait about two minutes and retry, up to 3 times.
  3. Procedure:
     1. Read the request's owning design and every code and doc location it cites, at HEAD. Search the git log and `tickets/` for merged work that covers part of it. If it is fully covered, create nothing and report `skipped` with the evidence. If it is partly covered, author only the rest and list what you dropped and why.
     2. Run `clutch new ${stem} --kind <kind>`, with the row's kind, else the kind the request implies. For a bug, first save real observed output to a file and pass it with `--evidence <file>`. If `clutch new` refuses because the ticket exists, stop and report `failed` with its message. Read the ticket authoring guide whose path it prints (`clutch docs` also names it) in full; it owns what goes in every section, and this prompt does not restate it. Then read the skeleton and one recently merged ticket for shape.
     3. Fill every section as the guide says:
        - Author the smallest change that satisfies the request, and nothing it does not ask for.
        - `Fence closure` is where tickets fail. Apply the guide's `## Scope fence` rules to every name, value, verb, path, state, and set member the ticket adds or changes. Grep tests, docs, source, and any extension or client code, in-code registries and closed sets included.
        - Read every `confirmed, unmerged` ticket that fences a file yours fences. In `## Context` or the criteria, state what either merge order changes, so neither breaks.
        - Write test commands the way the host's conduct file says.
        - `Depends on` names only tickets whose merged code this one needs. Order the rest with priority and `Runs before`, omitting a stem that has no ticket directory yet.
        - Give a realistic time budget. When the request cannot fit one run, split it into `at most 3` tickets: keep `${stem}` as one and name the others `${stem}-<part>`.
     4. Run `clutch lint ${stem}` until it exits 0.
     5. Make the guide's pre-review checks.
     6. Run `clutch review ${stem}`. Repair every finding, re-lint, and re-review until it prints approve. After `6 rounds` without approve, stop and report `review_stuck` with the last findings verbatim.
  4. Report:
     - status: `approved`, `skipped`, `review_stuck`, or `failed`;
     - per ticket: its stem, kind, priority, review rounds, final fence, `Depends on`, `Runs before`, and expected and stuck minutes;
     - what you dropped from the request and why;
     - the suggestions you filed, by id;
     - anything whoever launched you must know.
- `clutch/specs/ask/review.md`: the text before "Write the report to me in plain English" is replaced. From that sentence to the end, the text stays verbatim. The placeholders stay `${stem}` and `${ticket}`, with no other `$`. The new opening says:
  - Audit clutch ticket `` `${stem}` `` against the merged code and the other open tickets.
  - Read `${ticket}`, the ticket authoring guide that `clutch docs` names, every file the ticket names, and every `confirmed, unmerged` ticket under `tickets/` that fences a file this ticket fences or shares an interface with it (`clutch status` lists the queue).
  - The ticket may already pass `clutch lint` and `clutch review`. Find what they missed: anything that would make its run park, fail Check, waste a run, or deliver the wrong thing.
  - Report only problems you verified, each with its evidence (a `path::Name`, a heading, or command output). Do not praise.
  - Check:
    - premise: every fact the ticket states about current code is true at HEAD;
    - fence closure: for every name, value, verb, path, state, or set member the change adds or alters, grep tests, docs, source, and any extension or client code. That covers in-code registries and closed sets, CLI choices, help entries, snapshot vocabularies, parity tests, spec version pins, and coverage floors that force a unit-test path. Name every forced file missing from `## Scope fence`;
    - criteria: each is runnable or readable and names the wrong result it rules out. All can hold together, none contradicts merged behavior or a test outside the fence, and every `## Verification` command exists and would exit 0 on a correct implementation;
    - fidelity: the ticket delivers everything its request asks, or drops it with a true reason, and nothing beyond it;
    - budget and kind: `expected` and `stuck` are realistic, and a bug has real evidence and a valid `## Regression`;
    - collisions: check each of those tickets in `either merge order` for an edit to the same section, a fake or fixture config missing a field the other adds, a value or spec version the other changes, and a criterion the other's merge breaks.
  - Mark each problem `blocking` (the run will park, fail, or deliver the wrong thing) or `minor`.
- `clutch/docs/host-running.md`: the `prompt` row's description becomes "Render an operator prompt for a ticket, a new ticket stem (`author`), named box IDs, all committed drafts, the drain loop, or the plan-ticket-drain kickoff without writing state." Nothing else in the file changes.
- `docs/how-clutch-works.md` section 2.1 only:
  - The `` `prompt <diagnose\|running\|review> <stem>` `` row's description gains "; `review` audits the ticket against merged code and every confirmed, unmerged ticket".
  - Two rows are added directly after the `` `prompt drafts` `` row:
    - `` | `prompt author <stem>` | no | Print the hand-authoring prompt for one ticket from its roadmap row or a request; the ticket need not exist yet. | ``
    - `` | `prompt plan-ticket-drain` | no | Print the kickoff prompt that runs the roadmap to completion unattended, authoring its rows as tickets and draining them, without writing state. | ``
- `tests/integration/test_ask.py`: the skip set in the `test_each_kind_renders_stem_ticket_and_state_dir` parametrize becomes `{"box", "drafts", "drain-loop", "plan-ticket-drain", "author"}`. Neither new kind renders that test's state-directory and "Recommendation" text. Nothing else in the file changes.
- New tests in two new files: `tests/unit/test_ask_plan_drain.py` and `tests/integration/test_ask_plan_drain.py`. The unit file follows `tests/unit/test_ask_drain_loop.py`: it uses a `SimpleNamespace` config whose `state_dir` is under `tmp_path`, a monkeypatched `load_config` and `child_env`, and a monkeypatched `Path.read_text` that returns a template naming `self.name`. It reads and writes disk only under `tmp_path`, and it runs every line this ticket changes in `clutch/ask.py` and `clutch/__main__.py`.

Out:
- `clutch/specs/ask/drain-loop.md` and its tests: the kickoff carries the session's additions (see `## Goal / Why`). `diagnose.md`, `drafts.md`, `box.md`, and `running.md` are also out.
- `clutch/help.py`, `clutch/observe.py`, and the extension. The new kinds are CLI prompts for agents, and no extension surface opens them, so they need no help entry or snapshot argv. The `review` command's help ("Open a prompt to review the selected ticket.") stays true.
- `clutch/docs/host-authoring.md`. Its missing rule (cite code by symbol, never by line number) is box-000586. CORE_TEMPLATE, `CLAUDE.md`, and `AGENTS.md` are also out: none lists prompt kinds.
- A plan-ticket-serve prompt, and any kickoff parameter or kind for one: that process comes later.
- Naming `clutch roadmap accept` in step 6. `roadmap-accept` is not merged at this ticket's base, so the step states the review without a verb. If `roadmap-accept` merges first, the step is still correct but no longer the only way to run the review. `release-acceptance-review` puts `roadmap accept` in every gate block, and the follow-up box-000587 names the verb.
- Merge order with the confirmed, unmerged tickets that fence the same files. Either order merges cleanly:
  - `roadmap-accept` edits the `roadmap` parser and handler in `clutch/__main__.py`, the how-clutch-works section 2.1 row after `roadmap gate <release>`, the section 8.4 table, and the `roadmap` row of `clutch/docs/host-running.md`. This ticket edits only `handle_prompt`, the section 2.1 `prompt` rows, and the `prompt` row of `clutch/docs/host-running.md`. No hunk is adjacent to the other's.
  - `release-acceptance-review` edits how-clutch-works section 7.5 and `docs/roadmap.md`, which this ticket does not touch.
  - `evidence-envelope` edits the `probe` handler in `clutch/__main__.py` and how-clutch-works sections 8.5 and 10.1, also untouched here.
  - The draft `closed-sets-single-owner` edits the tier, priority, and kind tuples in `clutch/__main__.py`, also untouched here.
  - `tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs` passes on either base, because no prompt names `roadmap accept`.

## Scope fence
- clutch/ask.py
- clutch/__main__.py
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/author.md
- clutch/specs/ask/review.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_ask.py
- tests/unit/test_ask_plan_drain.py
- tests/integration/test_ask_plan_drain.py

## Acceptance criteria
1. `tests/unit/test_ask_plan_drain.py::test_render_plan_ticket_drain_unit` uses a config whose `state_dir` is `tmp_path / "custom"` and a `Path.read_text` patched to return `self.name + " ${state_dir}"`. It asserts that `ask.render("plan-ticket-drain", "", config, tmp_path)` equals `"plan-ticket-drain.md custom"`. Ruled out: reading `drain-loop.md` for the new kind, an absolute or fixed state path, and a kind missing from `KINDS` (which raises `ValueError`).
2. `tests/unit/test_ask_plan_drain.py::test_prompt_verb_plan_ticket_drain_unit` asserts the following with the same patches. `entry.main(["prompt", "plan-ticket-drain"], cwd=tmp_path)` returns 0 and prints exactly `plan-ticket-drain.md custom`. `entry.main(["prompt", "plan-ticket-drain", "x"], cwd=tmp_path)` returns 2, and stderr contains `plan-ticket-drain takes no stem`. Ruled out: argparse refusing the kind, the kickoff treated as a ticket prompt that demands a stem, and a stem silently ignored.
3. `tests/unit/test_ask_plan_drain.py::test_prompt_verb_author_without_ticket_unit` patches `Path.read_text` to return `self.name + " ${stem} ${ticket}"`, with no `tickets/` directory under `tmp_path`. It asserts:
   - `entry.main(["prompt", "author", "new-stem"], cwd=tmp_path)` returns 0 and prints exactly `author.md new-stem tickets/new-stem/ticket.md`;
   - `entry.main(["prompt", "author", "Bad_Stem"], cwd=tmp_path)` returns 2 with `kebab-case` in stderr;
   - `entry.main(["prompt", "review", "new-stem"], cwd=tmp_path)` returns 2 with `tickets/new-stem/ticket.md does not exist` in stderr.

   Ruled out: `author` refusing the missing ticket that a new stem always has, `author` accepting an invalid stem, and the existence check dropped for the ticket kinds.
4. `tests/integration/test_ask_plan_drain.py::test_plan_ticket_drain_prompt_content` renders `ask.render("plan-ticket-drain", "", config, tmp_path)`. The config is `tests/integration/test_config.py::VALID` with `state_dir: .clutch` replaced by `state_dir: custom/state`. The text contains each of these:
   - `docs/roadmap.md`, `standing delegation`;
   - `clutch doctor`, `clutch probe`, `clutch release --minor`, `never twice`;
   - `clutch prompt drain-loop`, `clutch prompt diagnose`, `clutch prompt drafts`, `clutch prompt box`, `clutch prompt running`;
   - `clutch confirm --yes`, `clutch reject --yes`, `clutch suggest`;
   - `No person is in the loop`, `Proposed`, `different model family`, `counted in runs`, `Never push`;
   - `Let the driver author`, `clutch roadmap author --ahead`, `drift failure`, `clutch prompt author`, `clutch prompt review`, `never hold`;
   - `clutch roadmap status`, `clutch stop`, `roadmap_drive`, `custom/state/engine.log`, `custom/state/drain.out`;
   - `P1 row`, `never a Suggestion Box message`, `Still open:`.

   The first `clutch doctor` comes before the first `clutch probe`, which comes before the first `clutch prompt drain-loop`. `standing delegation` comes before the first `clutch confirm --yes`. The text does not start with `/loop`. Ruled out: a kickoff that drops the environment or credential checks or puts them after supervising starts, omits the delegation, the no-person rules, the drift window, the audit, or the phase-closing step, or sends acceptance gaps to the Suggestion Box.
5. `tests/integration/test_ask_plan_drain.py::test_author_prompt_content` renders `ask.render("author", "unique-stem", config, tmp_path)`. The text contains each of these:
   - `` `unique-stem` ``, `tickets/unique-stem/ticket.md`;
   - `clutch new unique-stem --kind`, `--evidence`, `clutch docs`;
   - `clutch lint unique-stem`, `clutch review unique-stem`, `clutch status`, `clutch suggest`;
   - `one write`, `Fence closure`, `confirmed, unmerged`, `Depends on`, `Runs before`, `at most 3`, `6 rounds`;
   - `approved`, `skipped`, `review_stuck`, `failed`.

   `clutch new unique-stem` comes before `clutch lint unique-stem`, which comes before `clutch review unique-stem`. Ruled out: an unrendered stem, a procedure that reviews before linting or authors without `clutch new`, and a prompt missing the atomic write, the fence-closure step, the cross-ticket read, or the report statuses.
6. `tests/integration/test_ask_plan_drain.py::test_review_prompt_is_audit` renders `ask.render("review", "unique-stem", config, tmp_path)`. The text contains each of these:
   - `` `unique-stem` ``, `tickets/unique-stem/ticket.md`;
   - `clutch docs`, `clutch status`;
   - `confirmed, unmerged`, `either merge order`, `blocking`, `minor`, `Scope fence`, `Verification`;
   - `"Recommendation"`, `wait for me to say go`.

   Ruled out: a review that ignores the queued tickets it can collide with, drops the fence and verification checks, or loses its report format.
7. `tests/integration/test_ask_plan_drain.py::test_prompts_carry_no_session_facts` asserts the three texts from criteria 4-6. None contains `${`, `./dev.py`, `uv run`, `/home/`, or `.claude`. Lowercased, none contains `bash`, `fungo`, or `gemini`. Ruled out: an unrendered placeholder, clutch's own dev command, an argv prefix, a machine path, a shell name, another host, a provider name, or a session file reaching every host.
8. `tests/integration/test_ask_plan_drain.py::test_prompts_name_only_existing_verbs` checks the three texts with a regex that matches a backtick, then `clutch `, then a first word `([a-z-]+)`, then optionally a space and a second word `([a-z-]+)`; as a Python literal, ``r"`clutch ([a-z-]+)(?: ([a-z-]+))?"``. In each text it matches at least once. Every match's first group is a subcommand of `clutch.__main__._parser()`. When the first group is `prompt` and the second matched, the second is in `ask.KINDS`. When the first group is `roadmap` and the second matched, the second is a subcommand of the `roadmap` sub-parser. Ruled out: a prompt naming a verb, prompt kind, or roadmap subcommand that does not exist at the base, such as `clutch roadmap accept` before `roadmap-accept` merges.
9. `tests/integration/test_ask_plan_drain.py::test_docs_list_new_prompt_kinds` checks two files:
   - The `` | `prompt` | `` row of `clutch/docs/host-running.md` contains `plan-ticket-drain` and `author`.
   - `docs/how-clutch-works.md` has a line starting with `` | `prompt author <stem>` | ``, a line starting with `` | `prompt plan-ticket-drain` | ``, and a `prompt <diagnose` row containing `audits`.

   Ruled out: new kinds the operator docs do not list.
10. `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/unit/test_ask_drain_loop.py tests/unit/test_host_running.py` exits 0. In `tests/integration/test_ask.py`, only the skip set changes, as `## Scope in / Scope out` says.
11. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_ask_plan_drain.py tests/integration/test_ask_plan_drain.py
./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/unit/test_ask_drain_loop.py tests/unit/test_host_running.py
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- a new or changed prompt names a `clutch` verb, prompt kind, or roadmap subcommand that does not exist at the base, or carries an argv copy (`uv run`, `./dev.py`, or a shell command line);
- a prompt carries a machine path, a shell name, another host, a provider name, a credential name, or a session file;
- the author prompt restates the authoring guide's section rules instead of having the agent read the guide;
- the kickoff sends acceptance gaps to the Suggestion Box, lets the session author a cause fix, or puts a person in the loop for anything but a missing credential or an unrecoverable driver error;
- it adds a plan-ticket-serve prompt, or a parameter or kind for one;
- it edits the drain-loop, diagnose, drafts, box, or running prompts, `clutch/help.py`, `clutch/observe.py`, the extension, CORE_TEMPLATE, `CLAUDE.md`, or `AGENTS.md`;
- an existing test other than the `tests/integration/test_ask.py` skip set changes;
- a file outside `## Scope fence` changes.

## Time budget
- expected: 75m
- stuck: 160m
