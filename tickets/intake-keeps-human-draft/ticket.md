---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/tickets.py::_intake_claims
- clutch/observe.py

## On-demand
- clutch/specs/ask/author.md
- clutch/specs/ask/drafts.md
- clutch/docs/host-authoring.md

## Goal / Why
After this ticket, intake of a new human ticket that carries an explicit `state: draft` line keeps it `draft` and stamps only `source: human`. Today `_intake_claims` ends with `stamp(stamp(text, "source", "human"), "state", "confirmed")`, which overwrites the authored `draft`. A hand ticket still being audited therefore becomes dispatchable as soon as any intake runs. The cli-group-box incident admitted a hand ticket mid-audit, which led to edits on a running ticket, and CLAUDE.md forbids those edits. The same on-disk restamp made a stale scratch copy revert `projection-helpers-single-owner` from `confirmed` to `draft` (box-000707). `clutch ticket new` writes `state: draft`, so a ticket made by the paved road stays draft until `clutch ticket confirm <stem>`. A new human ticket with no `state:` line is still stamped `confirmed`, as today. That keeps the many hand-written test tickets that carry no state line valid and avoids a repo-wide test rewrite. The ask author prompt cannot run `confirm` (it is on its forbidden list), so it must tell the author to name `clutch ticket confirm <stem>` for the owner once review prints approve. A committed hand draft also shows up in `clutch prompt drafts`, whose supervising loop resolves drafts the tick they appear; the drafts prompt must leave a `source: human` draft to its author, or that loop would confirm it mid-audit or reject work the owner asked for. `clutch/specs/ask/plan-ticket-drain.md` already confirms a hand-authored row after its audit.

## Scope in / Scope out
Scope in:
- `clutch/tickets.py::_intake_claims`: for a new stem with `source` human, stamp `source: human`; stamp `state: confirmed` only when the ticket has no `state:` line, and otherwise keep the authored `draft` or `confirmed`. Keep the refusal of states other than `draft` or `confirmed`, and reword its paved road and the docstring so neither says intake always confirms.
- `clutch/observe.py`: the status label `new: confirmed by next intake` becomes a label saying a new human ticket with `state: draft` stays draft until `clutch ticket confirm`, and one with no state line is confirmed by the next intake. The menu needs no change: it already judges a pending stem through `_intake_plan_stem`, so its `run` entry follows the new intake result.
- `clutch/specs/ask/author.md`: add one line saying a reviewed ticket stays `state: draft` and that the final reply names `clutch ticket confirm <stem>` for the owner to run. The line names the bare verbs and never `clutch ticket lint ${stem}` or `clutch ticket review ${stem}`, so the new, lint, review ordering assertion in `tests/integration/test_ask_plan_drain.py` keeps holding. This ask prompt carries no `version`.
- `clutch/specs/ask/drafts.md`: add one sentence to the paragraph that begins `For each draft, read its ticket`: a draft whose frontmatter `source` is `human` is a hand-written ticket its author confirms with `clutch ticket confirm` after the audit; list it as skipped and give it no confirm or reject step. No other line changes. This ask prompt carries no `version`.
- `clutch/docs/host-authoring.md`: in `## Workflow`, step 4 only: a new ticket authored `state: draft` (as `clutch ticket new` writes it) stays a draft after intake commits it; once review prints `approve` and any audit is done, its author runs `clutch ticket confirm <stem>` or names that command for the owner, and only then does a running `engine serve` or `clutch engine drain` pick it up. No other part of the guide changes. `author-slice-needs-follow-up-row` (the `Scope in / Scope out` bullet) and the confirmed `authoring-no-standing-document-content-tests` (`Keeping tickets apart`) edit other sections, so either merge order holds.
- Existing tests whose tickets carry an explicit `state: draft` and so flip; nothing else in these files changes:
  - `tests/integration/test_tickets.py`: only `test_new_skeleton_is_draft_until_intake`, whose committed `tickets/aaa-wip/ticket.md` now keeps `state: draft` and does not carry `state: confirmed`. The other intake tests there write `VALID`, whose frontmatter has no `state:` line, and keep expecting `state: confirmed`.
  - `tests/unit/test_intake_plan.py`: in `test_plan_decisions`, the stamped text for the `state: draft` input keeps `state: draft` (and still carries `source: human`). Add one case there whose input has no `state:` line and assert the stamped text carries `state: confirmed` and `source: human`, so a fenced unit test runs the new branch of the floored `clutch/tickets.py`.
  - `tests/integration/test_intake_scope.py`: in `test_named_verbs_leave_other_pending_ticket`, whose `alpha` is a new `state: draft` ticket, the expected exit code becomes 2 for `run` (intake commits `alpha` as a draft and dispatch refuses it) and 0 for `confirm` (it now confirms the new draft); `review` and `reject` stay 0 and the other assertions stay.
  - `tests/integration/test_menu_verb_parity.py`: the `new` and `staged-new` cases write `state: draft` and leave the ticket uncommitted, and the parametrize table (lines 100-101) expects `run` on. A new explicit draft now stays draft, so `run_admission` refuses it; flip the `run` expectation to False for `new` and `staged-new` and change nothing else there.
- Docs, only these lines: in `docs/how-clutch-works.md`, the `ticket new` row of the section 2 verb table (`... and lints it; intake confirms it.`), the `state` bullet (`intake stamps a new hand-written ticket `confirmed``) and the intake bullet (`intake stamps it `source: human`, `state: confirmed``) each say that intake keeps an authored `state: draft`, stamps `confirmed` only when the state line is absent, and that a draft is confirmed with `clutch ticket confirm`. In `clutch/docs/host-running.md`, the sentence `Drafts written by Author wait for `ticket confirm`.` becomes `Drafts, including a new hand-written ticket authored `state: draft`, wait for `ticket confirm`.`
- `tests/integration/test_intake_keeps_draft.py` (new) pins the intake behavior, the drain behavior of criterion 4, and the prompt and guide lines. For the drain case it reuses the rig `tests/integration/test_drain_admissions.py` uses (the `root` fixture and `pause_checkout` from `tests/integration/test_drain.py`, `NoChild` from `tests/integration/test_drain_reentry.py`) without adding anything to those files.
Scope out: `confirm` verb behavior, machine-source intake, established-stem handling, tickets with no `state:` line, the drain-loop and plan-ticket-drain prompts, `tests/integration/test_review_command.py` and `tests/integration/test_drain_admissions.py` (their tickets carry no `state:` line or are committed without intake, so they pass unchanged), and the `runner.py` confirm stamp.

## Scope fence
- clutch/tickets.py
- clutch/observe.py
- clutch/specs/ask/author.md
- clutch/specs/ask/drafts.md
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/integration/test_tickets.py
- tests/unit/test_intake_plan.py
- tests/integration/test_intake_scope.py
- tests/integration/test_menu_verb_parity.py
- tests/integration/test_intake_keeps_draft.py

## Acceptance criteria
1. Intake of a new human ticket written with `state: draft` commits text containing `state: draft` and `source: human`, not `state: confirmed`; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
2. Intake of a new human ticket with no `state:` line commits `state: confirmed`, not `draft` and not an absent line; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py tests/unit/test_intake_plan.py`.
3. A new human ticket authored `state: confirmed` keeps `confirmed` at intake; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
4. A new human ticket written uncommitted with `state: draft` (not through `commit_ticket`) is committed by a drain's intake still `state: draft` and is never handed to the drain's dispatch; after `clutch ticket confirm --yes <stem>`, a later drain dispatches it. A drain that dispatches the draft before the confirm fails the test; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
5. `clutch/specs/ask/author.md` contains the string `clutch ticket confirm` in a line that is not the forbidden-verbs list, and still lists `clutch ticket confirm` as forbidden for the author to run; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.
6. The existing tests pass with the flips named in Scope in, and the unchanged ones still pass; checked by `./dev.py test tests/integration/test_tickets.py tests/unit/test_intake_plan.py tests/integration/test_review_command.py tests/integration/test_drain_admissions.py tests/integration/test_intake_scope.py tests/integration/test_menu_verb_parity.py tests/unit/test_specs.py`.
7. `tests/integration/test_intake_keeps_draft.py` reads `clutch/docs/host-authoring.md` and asserts its `## Workflow` section contains `clutch ticket confirm`, and reads `clutch/specs/ask/drafts.md` and asserts one line contains both `source` and `human` and says such a draft is skipped; both assertions fail on the unchanged files, which say neither; checked by `./dev.py test tests/integration/test_intake_keeps_draft.py`.

## Verification
```
./dev.py test tests/integration/test_intake_keeps_draft.py tests/integration/test_tickets.py tests/unit/test_intake_plan.py tests/integration/test_review_command.py tests/integration/test_drain_admissions.py tests/integration/test_intake_scope.py tests/integration/test_menu_verb_parity.py tests/unit/test_specs.py tests/integration/test_ask_drafts.py tests/integration/test_ask_plan_drain.py tests/unit/test_host_authoring.py tests/integration/test_lint_guide_parity.py
```

## Definition of rejected
Intake still overwrites an explicit `state: draft` on a new human ticket with `confirmed`, or a new compat flag or second intake path is added, or a committed human draft is dispatched without `confirm`, or the drafts prompt still gives a confirm or reject step for a `source: human` draft.

## Time budget
- expected: 30m
- stuck: 60m
