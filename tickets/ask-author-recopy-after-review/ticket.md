---
state: rejected
source: box:suggestion
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/integration/test_specs_json_reply_specs.py

## On-demand
- clutch/specs/ask/author.md

## Goal / Why
The ask author prompt (`clutch/specs/ask/author.md`) tells the author to edit a scratch copy and replace the ticket file in one write, but never to refresh that copy after `clutch ticket review`. Review's intake stamps a new stem `state: confirmed` on disk and never restamps an established stem. A repair write from the stale pre-intake copy therefore reverts `state: confirmed` to `state: draft`. Later intakes commit draft, and the drain does not dispatch a draft, so authored work stalls with nothing flagging it. Observed 2026-11-17 on projection-helpers-single-owner (commits 74060cd9, 384cc161, a3ea5885). After this ticket the prompt tells the author to re-copy the on-disk ticket into the scratch copy after every review before editing, so the on-disk `state:` is kept.

## Scope in / Scope out
In: edit the Limits bullet on scratch-copy editing in `clutch/specs/ask/author.md` to add the re-copy step: after every `clutch ticket review`, copy `tickets/<your stem>/ticket.md` over the scratch copy before editing, so the `state:` line intake wrote is kept. The bullet names the bare verb `clutch ticket review` and never `clutch ticket review ${stem}`, so the new, lint, review ordering assertion in `tests/integration/test_ask_plan_drain.py` keeps holding. Add a new test file that pins this wording.
Out: no intake or lint change (a refusal of a confirmed-to-draft edit is a separate, larger choice); no change to `clutch/docs/host-authoring.md`, whose workflow does not mention a scratch copy; no other spec edits; no version bump, since this spec carries none.

## Scope fence
- clutch/specs/ask/author.md
- tests/integration/test_ask_author_refresh.py

## Acceptance criteria
1. `clutch/specs/ask/author.md` contains the phrase `re-copy` together with `clutch ticket review` and `state:`, checked by `./dev.py test tests/integration/test_ask_author_refresh.py`. The test fails on the unchanged file, which has no `re-copy` phrase.
2. The pin test asserts the re-copy sentence sits in the same Limits bullet as `replace the ticket file in one write`, not elsewhere in the file, checked by `./dev.py test tests/integration/test_ask_author_refresh.py`. A test that only searched the whole file would also pass if the sentence were moved out of the bullet.
3. The existing prompt tests still pass, checked by `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_plan_drain.py tests/integration/test_specs_json_reply_specs.py`.

## Verification
```
./dev.py test tests/integration/test_ask_author_refresh.py tests/integration/test_ask.py tests/integration/test_ask_plan_drain.py tests/integration/test_specs_json_reply_specs.py
```

## Definition of rejected
The re-copy step is added anywhere other than the scratch-copy Limits bullet, any file outside the fence changes, or the pin test passes on the unchanged spec.

## Time budget
- expected: 10m
- stuck: 20m
