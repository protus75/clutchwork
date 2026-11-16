---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Runs before
- release-gates-as-commands

## Context
- docs/how-clutch-works.md#6.3 Diagnosis
- docs/how-clutch-works.md#6.4 Caps and escalation
- docs/how-clutch-works.md#6.6 The Reject queue, keep and kill
- docs/how-clutch-works.md#6.7 Other holds
- docs/how-clutch-works.md#9.3 Author and starting state
- clutch/hostfiles.py::CORE_TEMPLATE

## On-demand
- docs/roadmap.md
- docs/roadmap-driver-plan.md
- docs/gemini-graphics-refactor-plan.md
- docs/upstream-issue-plan.md
- docs/journal-sql-refactor-plan.md
- docs/stage-panels-plan.md
- docs/annotations-index-plan.md
- docs/evidence-trail-plan.md

## Goal / Why
The owner decided on 2026-11-16 how the roadmap runs, and those decisions override the plans:

- (a) Gates and cadences count runs, never wall-clock time.
- (b) No person is in the loop. Every gate is a command. A prerequisite that a person used to run at a CLI or browser (a "hand test") becomes an agent-run capture, committed as the dependent ticket's evidence. Escalations go through the supervisor and the diagnose path. The only external input is a missing credential. Gemini has none on this machine, so the rows that need it are skipped while an agent looks for a route through the authenticated providers.
- (c) The visual judge is calibrated against labels from an AI label panel of a different model family than the judge (`docs/roadmap.md` §5, decision 13), not against 20-50 hand labels.
- (d) A plan's open decision takes the plan's Proposed option. Where there is none, a recorded AI design panel settles it: three independent proposals and one judge, before the dependent row is authored.

One open item is decided outright. The owner delegated the holds a person's `confirm` or `reject` used to release on 2026-11-15, and the orchestrator applied that on 2026-11-16 as driver plan open decision 5. The supervising agent loop releases them by running `clutch prompt diagnose <stem>` or `clutch prompt drafts` and executing its Recommendation. `supervisor-rework` and `roadmap-author` are authored against that, so the plan must not leave it open.

`docs/roadmap.md` and its plans still say the opposite in many places:

- The parallel-runs release ships after "one week" of parallel serve, and the training/panels release after a review panel "has run this repo's queue for a week".
- Roadmap section 8 ends with "Operator actions (not tickets)".
- Rows 32 and 34 wait "after the hand test". Rows 36 (`journal-query-layer`) and 46 (`merge-model-resolve`) need the captures that section 8's operator list names (the row 35 re-measurement and the 13 conflict-facts events), but their Content does not say so. `roadmap-table-parser`'s capture refusal holds a row only on its Content's phrase or a named evidence path, so the driver would file both rows before their captures exist.
- Decision 18 and row 55 calibrate on "20-50 hand labels".
- `docs/roadmap-driver-plan.md` section 4 allows `gate: operator` for "a week of parallel runs, a GO verdict". Its section 7 is "What the operator still does". Section 5 parks a publish "for `confirm`". Open decision 4 sends a digest "daily".
- `docs/gemini-graphics-refactor-plan.md` parks undecided images "for a person" and grows its calibration set from "the operator's decisions".

The roadmap driver (`roadmap-author`, `release-gates-as-commands`, `driver-loop`) parses and acts on these documents. If they are left as they are, it would author tickets that wait on a clock or a person.

After this change, roadmap section 6 records the decisions as one new entry. The release table, the master table, and section 8 apply them. The driver, Gemini, upstream-issue, journal, stage-panels, annotations, and evidence plans no longer name a wall-clock gate, a hand test, hand labels, or a person who releases a hold. Every open decision takes its Proposed option, names the AI design panel and the row it must precede, or (driver open decision 5) records the delegated decision.

The `visual_baseline` GO threshold is 0.85 agreement. The Gemini plan's B7 states no number. It cites the review-baseline precedent, whose catch-rate floor is `MIN_CATCH_RATE = 0.85` in `eval/harness.py`.

Releases are named by theme or by section here, because `roadmap-plan-corrections` renumbers them. This ticket keeps every version number and release name as it stands at the base commit.

## Scope in / Scope out
Scope in. "Decision N" below means the new roadmap section 6 entry. Its number is one above the highest-numbered entry in section 6 at the base commit, which is 19 unless another ticket added an entry first. Wherever a plan cites it, write `docs/roadmap.md` §6, decision N. Each item says what the changed text must say. The quoted phrases, the code spans, and the terms "supervising agent loop" and "regardless of the review baseline" are required verbatim because Verification greps for them. Nothing in these documents may say "week", "weekly", "daily", "overnight", "hand test", "hand-test", "hand label", or `gate: operator` after the change, and that includes the new entry.

`docs/roadmap.md`:
1. Section 6: add the line `Decided 2026-11-16:` after decision 18. If a `Decided 2026-11-16` line already exists, reuse it. Under that line, add decision N, titled `**No human in the loop.**`. It must cover all four of these:
   - (a) every gate and cadence counts runs or merged tickets, never wall-clock time.
   - (b) every gate is a command, and no gate is a judgment a person makes. A prerequisite a person once ran is an agent-run capture, committed under the dependent row's `tickets/<stem>/evidence/`, and its plan says which agent action captures which facts. Escalations go through the supervisor and the diagnose path. A held stem or an Author draft is released by the supervising agent loop executing the Recommendation of `clutch prompt diagnose <stem>` or `clutch prompt drafts` (`docs/roadmap-driver-plan.md` open decision 5). The only external input is a missing credential: a row that needs one is skipped while an agent finds a route through the authenticated providers, and Gemini has no credential on this machine.
   - (c) calibration and GO baselines use labels from an AI label panel of a different model family than the judge (§5, decision 13), never labels a person made. The `visual_baseline` GO gate is the judge's agreement with the panel's labels at 0.85 or above.
   - (d) a plan's open decision takes the plan's Proposed option. The journal and upstream plans write that option as "Recommendation", and it counts as Proposed. Where no option is proposed, a recorded AI design panel settles the decision before the dependent row is authored: three independent proposals and one judge, with the record committed as that row's evidence. A decision the owner or the owner's delegate already settled needs no panel, as for driver plan open decision 5.
2. Section 6, decision 14: "this week's plans" becomes "the plans written 2026-11-13".
3. Section 6, decision 15: journal plan items 3-7 take that plan's recommendations (decision N). The words "stay open until" leave.
4. Section 6, decision 17: an undecidable result parks, and Gemini plan open decision 4 settles its release. The words "for a person" leave.
5. Section 6, decision 18: the third layer is best-of-N where only unsure cases park, and no person is named. Calibration is against labels from an AI label panel of a model family other than the judge's (§5, decision 13), with GO at 0.85 agreement. Mark the entry "amended 2026-11-16 by decision N".
6. Section 5, decision 16:
   - "or an operator confirm" leaves. The driver publishes only under `release.publish: true`.
   - Its last sentence ("The chat-session rules in CORE_TEMPLATE do not change: sessions still never confirm, reject, or push on their own.") becomes: sessions never push on their own. The supervising agent loop confirms or rejects only by executing a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation (driver plan open decision 5). CORE_TEMPLATE's supervising-session rule still forbids a session to confirm or reject, and its change waits in the Suggestion Box as box-000508.
7. Section 1, release table:
   - The parallel-runs release's ship gate replaces the one-week clause with "parallel serve has merged the next 10 tickets with no conflict-rerun cap hit".
   - That release's start gate replaces "Gemini hand test A0 fact 7 answered" with the Gemini agent capture A0 committed (fact 7 still decides `api-provider-client`), and says decision N's credential rule applies while this machine has no Gemini credential.
   - The training/panels release's ship gate replaces the one-week clause with "a two-member review panel has reviewed the next 10 tickets with its unique-catch count in the retro report".
   - The "Independent of release" paragraph says `gemini-provider` and `upstream-issue-verb` wait on an agent-run capture committed as their evidence, and that their plans say which agent action captures which facts.
8. Section 8:
   - Intro: "(by hand today; ...)" becomes "(by the authoring agent today; ...)".
   - Rows 32 (`gemini-provider`) and 34 (`upstream-issue-verb`): "after the hand test A0" and "after its hand test" become "after its agent capture". Row 32 also says it is skipped while this machine has no Gemini credential (decision N).
   - Rows 36 (`journal-query-layer`) and 46 (`merge-model-resolve`): each Content says "after its agent capture" and names, in backticks, the one capture file its Agent tasks bullet (item 9) commits: `tickets/journal-query-layer/evidence/re-measure.md` (the row 35 re-measurement) and `tickets/merge-model-resolve/evidence/merge-conflict-facts.md` (the 13 `merge_conflict_facts` events, replacing row 46's "After reading the 13 `merge_conflict_facts` events"). The rest of each Content stays. A file, not the directory, is named because `roadmap-table-parser` holds a row until every evidence path its Content names is a file in the checkout.
   - Row 54: "`confirm --select`" becomes "its release (Gemini plan open decision 4)".
   - Row 55: the fixtures are labelled by an AI label panel of a model family other than the judge's (§5, decision 13), and the `visual_baseline` GO gate is the judge's agreement with the panel's labels at 0.85 or above.
   - Row 90: "hand-test refusal" becomes "capture refusal".
   - Row 91: "(`operator` where no command exists)" leaves, and the row says every gate is a command.
   - Row 92: "else a park for `confirm`" becomes "else nothing publishes".
9. Section 8, the subsection `### Operator actions (not tickets)` becomes `### Agent tasks (not tickets)`:
   - Drop the `vscode-help` bullet (rejected at `328d07d9`) and the box-triage bullet (`box-000324`, `box-000440`, `box-000441` and `box-000442` are resolved, per `clutch status`).
   - Keep one bullet per capture. Each bullet names the agent action, the facts it captures, and where the evidence is committed:
     - The Gemini A0 capture, nine facts, goes to `tickets/gemini-provider/evidence/`. Name the two agent actions given in Gemini plan item 1 below. It is skipped while the credential is missing.
     - The GitHub prefill capture, three facts, goes to `tickets/upstream-issue-verb/evidence/`.
     - The parallel plan's A0 is an agent reading the 13 `merge_conflict_facts` events from the journal. It is committed as `tickets/merge-model-resolve/evidence/merge-conflict-facts.md`.
     - The row 35 re-measurement is an agent profiling a drain start and `clutch status` at the end of the truth release and recording the share of wall time spent in journal reads. It is committed as `tickets/journal-query-layer/evidence/re-measure.md`.
10. Section 9: "until then a person does" becomes "until then the agent that authors the row does".

`docs/roadmap-driver-plan.md`:
1. The intro's last sentence ("What stays with a person ...") becomes: nothing waits on a person, and the only outside input is a missing provider credential (section 7).
2. "What this plan cannot remove: ..." now names only a missing provider credential. It also says what replaced each old item (decision N):
   - a prerequisite a person once ran is an agent-run capture;
   - a GO baseline is measured against an AI label panel;
   - a ticket with a wrong goal or scope goes through the diagnose path;
   - a publish waits on `release.publish`.
3. Section 2:
   - In step 1, the road "escalate to the operator" becomes "the proposal escalates (step 4)".
   - In step 4, the stem stays in the Reject queue with the proposal attached, and no person is asked. The supervising agent loop releases or retires it (open decision 5), starting from the engine's best attempt.
   - "`ticket_changed` holds are not supervised: a person edited the ticket mid-run and the person decides." becomes: `ticket_changed` holds are not supervised by this step, and the supervising agent loop releases them (open decision 5).
4. Section 3:
   - The prerequisite becomes a capture prerequisite. A row whose content says "after its agent capture" is refused until the evidence file the row names exists under `tickets/<stem>/evidence/`.
   - A row that needs a credential this machine lacks is skipped (section 7).
   - The `roadmap_row` policy row defaults to `confirmed` regardless of the review baseline (open decision 5; `roadmap-row-message` builds it). "when the review baseline is GO and `draft` otherwise, the rule every other row follows" leaves. The other draft conditions in `docs/how-clutch-works.md` §9.3 still apply, and a `roadmap_row` draft one of them makes is released as every Author draft is (open decision 5).
5. Section 4:
   - The section says "every gate is a command", and no gate is a judgment a person makes.
   - The two gates that were `operator` become commands over recorded facts: a count of tickets merged under parallel serve with no conflict-rerun cap hit, and the recorded `visual_baseline` GO.
   - `roadmap status` reports rows blocked on a capture or a missing credential.
   - The word "operator" leaves the section.
6. Section 5: with `release.publish` absent or false (the default), the driver tags and bumps locally and does not publish, and nothing parks for `confirm`.
7. Section 6:
   - Step 3 publishes only when `release.publish` is true.
   - Step 4's digest lists held stems and why, not "stems waiting for the operator".
   - The `drain-loop` sentence says the prompt describes what the driver does by itself and what the supervising agent loop it starts does for a held stem or an Author draft (open decision 5), and that no step waits on a person.
   - The word "operator" leaves the section.
8. Section 7: rename it so the heading no longer says "operator", for example `### 7. What still comes from outside`. Rewrite it to state:
   - escalations go through the supervisor (section 2) and the diagnose path (`docs/how-clutch-works.md` §6.3-6.5). A stem the supervisor escalates, a `ticket_changed` hold, a Diagnose `reject` or `abandon-human` stem, and an Author draft are released by the supervising agent loop executing a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation (open decision 5);
   - the only external input is a missing credential;
   - Gemini has none on this machine, so the rows that need it are skipped while an agent finds a route through the authenticated providers;
   - publishing follows the `release.publish` config value and never a per-release person.
9. Ticket breakdown: in row 3, "hand-test refusal" becomes "capture refusal". In row 5, "the publish park" becomes "publish only under `release.publish`".
10. Open decisions:
    - A lead line, `Decided 2026-11-16` (roadmap §6, decision N), says items 1-4 take their Proposed option and item 5 records the owner's delegation.
    - Item 2's "stay with the person" becomes: `ticket_changed` and `abandoned` are not supervised; open decision 5 covers `ticket_changed`, and an `abandoned` stem stays eligible (`docs/how-clutch-works.md` §6.7).
    - Item 4 reads "Decided: after every settle." "older than a day" and "daily" leave.
    - New item 5, **Holds that ended with a person.** It is the last item and opens with "Decided 2026-11-16 (owner delegation of 2026-11-15)." It then states these three parts, which are required verbatim except that the text may run over several lines:
      - (a) A stem the supervisor escalates, a `ticket_changed` hold, and a stem a Diagnose `reject` or `abandon-human` verdict routes to the Reject queue are released by the supervising agent loop. It runs `clutch prompt diagnose <stem>` and executes its Recommendation: a ticket edit, then `clutch lint` until it exits 0 and `clutch review` until it approves, then `clutch confirm --yes <stem>`; or `clutch reject --yes <stem>`. A cause fix the diagnosis names goes to `clutch suggest` and is never authored.
      - (b) An Author draft from triage is released the same way, through `clutch prompt drafts` and its Recommendation.
      - (c) A `roadmap_row` ticket starts `confirmed` regardless of the review baseline (`roadmap-row-message`), so no `roadmap_row` draft waits on the baseline. One that another draft condition makes is an Author draft under (b).
11. "Departures from the design record", the CORE_TEMPLATE row ("a supervising session may not confirm or reject"):
    - The middle cell drops "Unchanged for sessions." and keeps its sentence on the supervisor stage. It gains: the supervising agent loop confirms or rejects only by executing a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation (open decision 5).
    - The Why cell becomes: the owner delegated those verdicts on 2026-11-15 (roadmap §6, decision N). CORE_TEMPLATE's rule still forbids them, and its change waits in the Suggestion Box as box-000508.

`docs/gemini-graphics-refactor-plan.md`:
1. "### Prerequisite: hand test (A0)" becomes `### Prerequisite: agent capture (A0)`.
   - The qwen sentence says that a run with an empty `HOME` established the facts.
   - An agent captures the nine facts and commits them under `tickets/gemini-provider/evidence/`, which is also the normalizer's golden fixture.
   - Agent action one is a headless `gemini` run per settings file with an empty `HOME`, saving stdout, stderr, exit code, and the live process argv. It captures facts 1-8 and needs the Gemini credential.
   - Agent action two resolves the `images` and `images-embed` extras on Python 3.14 in a scratch venv and saves the resolver output. It captures fact 9 and needs no credential.
   - Until a Gemini credential exists, `gemini-provider` and the rows that depend on it are skipped while an agent looks for a route to image generation and judging through the authenticated providers (decision N).
   - The closing "until that test runs" becomes "until that capture is committed".
   - The Roadmap paragraph, the "Risk the hand test must retire first" heading, and the A0 row of the ticket table use "agent capture" in place of "hand test".
2. Part A config: "stays an operator edit after setup, as it was for qwen" becomes: routing Gemini in this repo's `config.yaml` is a ticket's change after setup. In B3, "once the operator sets models" becomes "once its models are set". The `OPERATOR-SETS-THIS` placeholder row and line 69's home-directory sentence stay, because they describe host setup.
3. In the summary paragraph and in B1, the phrases naming "a person" become wording in which only the undecided cases park. The B6 heading drops "and the person", for example "candidates, selection, and the undecided park".
4. In B6, "**Park for a person.**" becomes "**Park.**":
   - The `visual_undecided` park keeps its triggers and artifacts.
   - No person releases it (decision N); open decision 4 settles what does, and `image-candidates-select` builds that release.
   - `confirm <stem> --select <k>`, `--select`, and "so the operator can decide in seconds" leave.
   - In the "Where each rule lives" table, the Layer 3 row's `confirm --select` becomes "release: open decision 4".
   - In the ticket table, row B6's `confirm --select` becomes "its release (open decision 4)".
5. B7:
   - The fixtures are 20 to 50 outputs, each labelled `accept` or `reject` by an AI label panel whose members are all from a model family other than the judge's (`docs/roadmap.md` §5, decision 13).
   - `./dev.py visual-baseline` reports the judge's agreement with the panel's labels.
   - The `visual_baseline` verdict is GO at 0.85 or above overall agreement, the review baseline's catch floor (`eval/harness.py`, `MIN_CATCH_RATE`), and NO_GO below. No person approves it.
   - Until GO, every graphics ticket parks at B6, and the label panel's verdicts on the parked candidates grow the fixture set.
   - Tightening continues until agreement reaches 0.85.
   - Row B7 of the ticket table says the fixtures are labelled by the AI label panel and gives the 0.85 GO gate.
6. Open decisions: add a `Decided 2026-11-16` (roadmap §6, decision N) line.
   - Items 2 and 3 take their Proposed option.
   - Item 1 has none, and a recorded AI design panel settles it before `graphics-kind` is authored.
   - New item 4, **Releasing a `visual_undecided` park.** It was a person's `confirm --select` or `reject`. It has no Proposed option, and a recorded AI design panel settles it before `image-candidates-select` is authored. Write it without the literal `--select`.

`docs/upstream-issue-plan.md`:
1. "## Prerequisite: hand test" becomes `## Prerequisite: agent capture`, and before authoring an agent commits the output under `tickets/upstream-issue-verb/evidence/`:
   - Facts 1 and 2: an agent opens prefilled `issues/new` links of increasing body length in a headless browser and saves each response status and the rendered title and body fields.
   - Fact 3: an agent builds clutch's wheel, installs it non-editable into a scratch venv, and saves the `importlib.metadata` output.
2. The Roadmap line ("waits on its hand test") and ticket row 0 ("(hand test)") say "agent capture".
3. Open decisions: a `Decided 2026-11-16` (roadmap §6, decision N) line says items 2-4 take the option each item states.

`docs/journal-sql-refactor-plan.md`:
1. Release protocol step 1: "the owner declares the feature set complete and" leaves, so the window opens when the re-measured cost is still there.
2. Step 2: "operator discipline plus the roadmap" becomes "the roadmap's schedule".
3. Open decisions lead: "The rest are decided at the checkpoint, before authoring ticket 1." becomes a `Decided 2026-11-16` (roadmap §6, decision N) sentence saying items 3-7 take their Recommendation.

`docs/stage-panels-plan.md`:
1. Section 5: "the number is what the owner decides on" becomes: whether a panel row stays on is settled from that number by a recorded AI design panel (decision N).
2. Open decisions: a `Decided 2026-11-16` (roadmap §6, decision N) line says items 1-3 take their Proposed option. Item 1's "Decide when ticket 1 is authored." leaves.

`docs/annotations-index-plan.md`, Open decisions:
1. A `Decided 2026-11-16` (roadmap §6, decision N) line says items 1 and 2 take their Proposed option. Item 3 has none, and a recorded AI design panel settles it before any row that builds it is authored.
2. Item 2's "the operator by hand" becomes "an agent task".

`docs/evidence-trail-plan.md`: in ticket row 5, "the hand-test capture" becomes "the agent capture".

Scope out:
- All code, tests, specs, config, `CLAUDE.md`, `AGENTS.md`, and `docs/how-clutch-works.md`.
  - `how-clutch-works.md` describes shipped code, so its time-based items stay. These are `retro.days` and the checkpoint push "after 5 merges or 24 hours" (the journal roll and log rotation are size bounds, not cadences).
  - The review baseline's operator `--record-go` approval in `eval/harness.py` is code and also stays.
  - CORE_TEMPLATE's supervising-session rule in `clutch/hostfiles.py`, and `clutch/specs/ask/drain-loop.md`, which defers to it, still forbid a session to confirm or reject. Driver open decision 5 needs that changed, and the change is filed as box-000508.
  - Those code changes go to the Suggestion Box, not into this ticket.
- `tickets/upstream-issue-verb/evidence/README.md` keeps its citation of the section "Prerequisite: hand test". It records the section's name when the capture ran.
- Version numbers, release names, row 88, and the stale audit facts in roadmap sections 2-4 and Status. `roadmap-plan-corrections` and the audit re-run own them.
- Historical facts and figurative uses. These stay:
  - in the driver plan, "about 30 tickets ran unattended in about 4 hours", the 142 operator verdicts, "after doing this by hand 78 times", the summary's account of today's holds ("held for a person", "what the operator does today by hand"), the Current state's "hand upload", and any "rejected by hand" that `roadmap-plan-corrections` leaves;
  - "53 commits in the 13 days";
  - "useful on day one", "from the day they land", and the "merges per day" example query;
  - "the owner's earlier manual runs".
- Product behavior in which a person may act on purpose. These stay:
  - a host operator's provider setup (`OPERATOR-SETS-THIS`);
  - viewing render artifacts;
  - running `index build` by hand;
  - any author using `context suggest`;
  - the `clutch issue` link a person reviews and submits, and the clutch owner's reading of upstream issues (upstream open decision 3);
  - the document agent's owner promotion step;
  - the annotations plan's risk line about a commit a person reviews.
  None of these is a gate, a cadence, a prerequisite, a calibration label, or an escalation step.
- `docs/parallel-tickets-plan.md`, `docs/training-data-plan.md`, and `docs/document-agent-plan.md`. None of their gates, cadences, prerequisites, or open decisions waits on a person or a clock: parallel A0 is already an agent read, and their open decisions are all decided.
- Answering any decision this ticket records as open. That includes the release of a `visual_undecided` park in Gemini open decision 4 and the threshold grammar in Gemini item 1. The AI design panel decides those later.
- Designing past driver open decision 5. The plan records the delegated decision as Scope in gives it, and names no engine stage, verb, or config field that runs the supervising agent loop.

## Scope fence
- docs/roadmap.md
- docs/roadmap-driver-plan.md
- docs/gemini-graphics-refactor-plan.md
- docs/upstream-issue-plan.md
- docs/journal-sql-refactor-plan.md
- docs/stage-panels-plan.md
- docs/annotations-index-plan.md
- docs/evidence-trail-plan.md

## Acceptance criteria
1. The first `## Verification` command exits 0. In all eight fenced documents it finds no `week`, `weeks`, `weekly`, `daily`, `overnight`, `hand test`, `hand-test`, `hand label`, `hand-labelled`, or `gate: operator`. Ruled out: today's text, which has 35 such hits across `docs/roadmap.md`, `docs/roadmap-driver-plan.md`, `docs/gemini-graphics-refactor-plan.md`, `docs/upstream-issue-plan.md`, and `docs/evidence-trail-plan.md`.
2. The second `## Verification` command exits 0 on `docs/roadmap.md`:
   - The release-table rows for the parallel-runs and training/panels themes carry the two run-count ship gates verbatim.
   - The text after `Decided 2026-11-16` in section 6 contains the decision's key phrases (`no human in the loop`, `wall-clock`, `every gate is a command`, `agent-run capture`, `missing credential`, `Gemini`, `diagnose path`, `clutch prompt diagnose`, `AI label panel`, `decision 13`, `0.85`, `AI design panel`, `three independent proposals`, `one judge`, `Proposed`).
   - Decision 14 has `the plans written 2026-11-13`, and `stay open until` is gone.
   - Decision 16 has `clutch prompt diagnose`, `open decision 5`, and `box-000508`, and has neither `never confirm, reject` nor `or an operator confirm`.
   - Decision 18 and row 55 have `AI label panel` and `0.85`.
   - Rows 32 and 34 have `after its agent capture`. Rows 36 and 46 have `after its agent capture` and name their capture files in backticks, `tickets/journal-query-layer/evidence/re-measure.md` and `tickets/merge-model-resolve/evidence/merge-conflict-facts.md`, which the `### Agent tasks` subsection also names.
   - Row 91 has no `operator`, and row 92 has no `confirm`.
   - Section 8 has an `### Agent tasks` subsection that names the four evidence paths and does not mention `vscode-help` or the box ids.
   - The document no longer has `for a person`, `a person does`, `by hand today`, `or an operator confirm`, or `--select`.
   Ruled out: today's text, a ship gate that keeps a time window, and a decision 16 that still says sessions never confirm or reject.
3. The third `## Verification` command exits 0 on `docs/roadmap-driver-plan.md`:
   - The departures section has `clutch prompt diagnose` and `box-000508`, and no `Unchanged for sessions`.
   - Section 2 has `supervising agent loop` and `open decision 5`.
   - Section 3 has `after its agent capture` and `regardless of the review baseline`, and no `when the review baseline is GO`.
   - Section 4 has `every gate is a command` and no `operator`.
   - Section 5 has `release.publish` and no `parks the publish`.
   - Section 6 has `supervising agent loop` and no `operator`.
   - Section 7 has `supervisor`, `diagnose path`, `supervising agent loop`, `clutch prompt diagnose`, `missing credential`, `Gemini`, `authenticated provider`, and `open decision 5`.
   - None of the old person or clock phrases remain, and no text says open decision 5 settles a release later (`open decision 5 settles`).
   - The open decisions have `Decided 2026-11-16`, and item 4 has `after every settle`.
   - Item 5, read from its number to the end of the file, has `Decided 2026-11-16`, `owner delegation of 2026-11-15`, `supervising agent loop`, `clutch prompt diagnose`, `clutch lint`, `clutch review`, `clutch confirm --yes`, `clutch reject --yes`, `clutch suggest`, `clutch prompt drafts`, `ticket_changed`, `abandon-human`, `roadmap_row`, `regardless of the review baseline`, and `roadmap-row-message`, and no `AI design panel`.
   Ruled out: today's section 7 heading `What the operator still does`, a digest cadence still tied to a day, an item 5 left open for an AI design panel, and a section 3 that keeps a `roadmap_row` default tied to the review baseline.
4. The fourth `## Verification` command exits 0 on `docs/gemini-graphics-refactor-plan.md`:
   - B7 has `AI label panel`, `decision 13`, and `0.85`.
   - The A0 section, now headed `### Prerequisite: agent capture (A0)`, has `tickets/gemini-provider/evidence/`, `credential`, and `authenticated provider`.
   - The plan no longer has `for a person`, `--select`, `stays an operator edit`, `the operator sets models`, or `selection, and the person`.
   - The open decisions have `Decided 2026-11-16`, an item 4 about `visual_undecided`, and an `AI design panel` tied to `graphics-kind` and `image-candidates-select`.
   Ruled out: today's B6 park for a person and B7's hand-labelled fixtures.
5. The fifth `## Verification` command exits 0. It checks the four smaller plans and the evidence plan:
   - The upstream plan's `## Prerequisite: agent capture` names `tickets/upstream-issue-verb/evidence/`.
   - The journal plan has no `the owner declares`, `operator discipline`, or `decided at the checkpoint`.
   - The stage-panels plan has no `what the owner decides on` and does have an `AI design panel`.
   - The annotations plan has no `operator by hand` and has an `AI design panel` in its open decisions.
   - Each of the upstream, journal, stage-panels, and annotations plans has `Decided 2026-11-16` in its open decisions.
   - The evidence plan says `agent capture`.
   Ruled out: today's text, on which the first check of this command fails with an `IndexError` because no `## Prerequisite: agent capture` heading exists.

## Verification
```
uv run python -c "import pathlib, re; names = ('roadmap', 'roadmap-driver-plan', 'gemini-graphics-refactor-plan', 'upstream-issue-plan', 'journal-sql-refactor-plan', 'stage-panels-plan', 'annotations-index-plan', 'evidence-trail-plan'); docs = {n: pathlib.Path('docs/' + n + '.md').read_text() for n in names}; bad = [(n, m.group(0)) for n, t in docs.items() for m in re.finditer(r'\b(weeks?|weekly|daily|overnight)\b|hand[- ]?(test|label)|gate: operator', t, re.I)]; assert not bad, bad"
uv run python -c "import pathlib; t = pathlib.Path('docs/roadmap.md').read_text(); sec = lambda a, b: t.split(a, 1)[1].split(b, 1)[0]; s1 = sec('## 1. ', '## 2. '); row = lambda k: next(l for l in s1.splitlines() if l.startswith('|') and k in l); assert 'parallel serve has merged the next 10 tickets with no conflict-rerun cap hit' in row('Parallel runs'); assert 'a two-member review panel has reviewed the next 10 tickets with its unique-catch count in the retro report' in row('Training flywheel'); s6 = sec('## 6. ', '## 7. '); new = s6.split('Decided 2026-11-16', 1)[1].lower(); missing = [p for p in ('no human in the loop', 'wall-clock', 'every gate is a command', 'agent-run capture', 'missing credential', 'gemini', 'diagnose path', 'clutch prompt diagnose', 'ai label panel', 'decision 13', '0.85', 'ai design panel', 'three independent proposals', 'one judge', 'proposed') if p not in new]; assert not missing, missing; assert 'the plans written 2026-11-13' in s6 and 'stay open until' not in s6; d16 = next(l for l in sec('## 5. ', '## 6. ').splitlines() if l.startswith('16. ')); assert all(p in d16 for p in ('clutch prompt diagnose', 'open decision 5', 'box-000508')) and 'never confirm, reject' not in d16 and 'or an operator confirm' not in d16; d18 = next(l for l in s6.splitlines() if l.startswith('18. ')); assert 'AI label panel' in d18 and '0.85' in d18; r = lambda n: next(l for l in t.splitlines() if l.startswith('| ' + n + ' |')); assert 'after its agent capture' in r('32') and 'credential' in r('32') and 'after its agent capture' in r('34'); q = chr(96); caps = {'36': 'tickets/journal-query-layer/evidence/re-measure.md', '46': 'tickets/merge-model-resolve/evidence/merge-conflict-facts.md'}; assert all('after its agent capture' in r(n) and q + c + q in r(n) for n, c in caps.items()); assert 'AI label panel' in r('55') and '0.85' in r('55'); assert 'operator' not in r('91') and 'confirm' not in r('92'); s8 = sec('## 8. ', '## 9. '); assert 'Operator actions' not in s8; a = s8.split('### Agent tasks', 1)[1]; assert not any(p in a for p in ('vscode-help', 'box-0003', 'box-0004')); assert all(p in a for p in ('tickets/gemini-provider/evidence/', 'tickets/upstream-issue-verb/evidence/', *caps.values())); assert not any(p in t for p in ('for a person', 'a person does', 'by hand today', 'or an operator confirm', '--select'))"
uv run python -c "import pathlib, re; t = pathlib.Path('docs/roadmap-driver-plan.md').read_text(); sec = lambda a, b: t.split(a, 1)[1].split(b, 1)[0]; dep = sec('## Departures from the design record', '## Target design'); assert 'Unchanged for sessions' not in dep and all(p in dep for p in ('clutch prompt diagnose', 'box-000508')); s2 = sec('### 2. ', '### 3. '); assert all(p in s2 for p in ('supervising agent loop', 'open decision 5')); s3 = sec('### 3. ', '### 4. '); assert all(p in s3 for p in ('after its agent capture', 'regardless of the review baseline')) and 'when the review baseline is GO' not in s3; s4 = sec('### 4. ', '### 5. '); assert 'operator' not in s4 and 'every gate is a command' in s4.lower(); s5 = sec('### 5. ', '### 6. '); assert 'parks the publish' not in s5 and 'release.publish' in s5; s6 = sec('### 6. ', '### 7. '); assert 'operator' not in s6 and 'what the chat should still look at' not in s6 and 'supervising agent loop' in s6; s7 = sec('### 7. ', '## Where each piece lives').lower(); assert all(p in s7 for p in ('supervisor', 'diagnose path', 'supervising agent loop', 'clutch prompt diagnose', 'missing credential', 'gemini', 'authenticated provider', 'open decision 5')); assert not any(p in t for p in ('What the operator still does', 'What stays with a person', 'escalate to the operator', 'for the operator', 'the person decides', 'stay with the person', 'older than a day', 'open decision 5 settles')); od = t.split('## Open decisions', 1)[1]; i = dict(re.findall(r'^(\d+)\. (.*)$', od, re.M)); assert 'Decided 2026-11-16' in od and 'after every settle' in i['4']; i5 = od.split(chr(10) + '5. ', 1)[1]; missing = [p for p in ('Decided 2026-11-16', 'owner delegation of 2026-11-15', 'supervising agent loop', 'clutch prompt diagnose', 'clutch lint', 'clutch review', 'clutch confirm --yes', 'clutch reject --yes', 'clutch suggest', 'clutch prompt drafts', 'ticket_changed', 'abandon-human', 'roadmap_row', 'regardless of the review baseline', 'roadmap-row-message') if p not in i5]; assert not missing, missing; assert 'AI design panel' not in i5"
uv run python -c "import pathlib, re; t = pathlib.Path('docs/gemini-graphics-refactor-plan.md').read_text(); sec = lambda a, b: t.split(a, 1)[1].split(b, 1)[0]; b7 = sec('#### B7.', '#### B8.'); assert all(p in b7 for p in ('AI label panel', 'decision 13', '0.85')); a0 = sec('### Prerequisite: agent capture (A0)', '### Fence'); assert all(p in a0 for p in ('tickets/gemini-provider/evidence/', 'credential', 'authenticated provider')); assert not any(p in t for p in ('for a person', '--select', 'stays an operator edit', 'the operator sets models', 'selection, and the person')); od = sec('## Open decisions', '## Sources'); i = dict(re.findall(r'^(\d+)\. (.*)$', od, re.M)); assert 'Decided 2026-11-16' in od and 'visual_undecided' in i['4'] and 'AI design panel' in od and 'graphics-kind' in od and 'image-candidates-select' in od"
uv run python -c "import pathlib; rd = lambda n: pathlib.Path('docs/' + n + '.md').read_text(); od = lambda t: t.split('## Open decisions', 1)[1]; u = rd('upstream-issue-plan'); assert 'tickets/upstream-issue-verb/evidence/' in u.split('## Prerequisite: agent capture', 1)[1].split('## Ticket breakdown', 1)[0] and 'Decided 2026-11-16' in od(u); j = rd('journal-sql-refactor-plan'); assert not any(p in j for p in ('the owner declares', 'operator discipline', 'decided at the checkpoint')) and 'Decided 2026-11-16' in od(j); s = rd('stage-panels-plan'); assert 'what the owner decides on' not in s and 'AI design panel' in s and 'Decided 2026-11-16' in od(s); a = rd('annotations-index-plan'); assert 'operator by hand' not in a and 'Decided 2026-11-16' in od(a) and 'AI design panel' in od(a); assert 'agent capture' in rd('evidence-trail-plan')"
```

## Definition of rejected
The branch is rejected if it:
- changes any file outside the fence, or any code, test, spec, config, `CLAUDE.md`, `AGENTS.md`, or `docs/how-clutch-works.md`;
- changes a version number or a release name, renumbers a master-table row, or renumbers an existing section 5 or section 6 entry;
- answers a decision this ticket records as open, for example by designing how a `visual_undecided` park is released, or by choosing the threshold grammar;
- records driver open decision 5 as open, or gives it a release other than the one Scope in states;
- removes a historical fact or product behavior that Scope out keeps;
- states a `visual_baseline` GO threshold other than 0.85, or lets a person approve or record GO;
- leaves or adds a gate, cadence, prerequisite, calibration label, publish step, or escalation that waits on a person or on wall-clock time anywhere in the fenced documents.

## Time budget
- expected: 75m
- stuck: 150m
