---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- panel-combiners
- panel-routing-config

## Context
- clutch/panel.py
- clutch/config.py::Route
- docs/stage-panels-plan.md

## On-demand
- clutch/driver.py
- clutch/stages.py
- clutch/requisition.py
- clutch/runner.py
- clutch/triage.py
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 67, ticket 3 of `docs/stage-panels-plan.md`. Today every stage is one model call. After this ticket, a routing row with `panel: {size: N, combine: ...}` makes the driver fan out N independent calls with `asyncio.gather`. Each member has its own effect key (`.../<call>/m<k>`), spool, evidence record and re-prompt loop. The `clutch/panel.py` combiner for the row then merges the member results into one artifact. Review (`review.md`), requisition review, diagnosis (`diagnosis.json`) and triage use the combined result, and one `panel_facts` signal is recorded per combined stage. A row without `panel` (or with size 1) behaves exactly as today. Why: the plan needs a second reviewer or a majority diagnosis to be measurable per row, and the document-agent and graphics plans consume this mechanism.

## Boundary contract
### Driver panel fan-out
- disposition: extend
- owner: clutch/driver.py
- consumers: clutch/stages.py (review), clutch/requisition.py, clutch/runner.py (diagnosis), clutch/triage.py
- observable change: a paneled row runs `size` member calls concurrently; member effect keys gain a `/m<k>` suffix; a member failing with `ProviderCallError` is dropped while at least one member survives; all members failing yields the same `infra_error` result as one failed call today; one `panel_facts` signal is journaled per combined stage (member provider and model, verdicts, agreement counts, dropped members and failure class); the combined artifact replaces the single-call artifact
- compatibility: rows with no `panel` key or size 1 keep today's effect keys, artifacts and journal records unchanged; downstream gates see the same artifact models
- acceptance: fan-out, member keys, drop and all-fail behavior and crash-replay are covered by unit tests with fake providers
- tests: new tests/unit/test_driver_panel_fanout.py and tests/unit/test_panel_stage_use.py
- post-merge source of truth: clutch/driver.py, with combiner rules in clutch/panel.py

### Combined artifacts
- disposition: reuse
- owner: clutch/panel.py
- consumers: stages, requisition, runner and triage call sites
- observable change: none to the combiner contract; call sites pass member artifacts to the existing combiners and write the result as `review.md` / `diagnosis.json` / the triage verdict
- compatibility: combiners and `Route.panel` from the depended tickets are used unchanged
- acceptance: a two-member review with one finding raised by both yields one finding with agreement 2/2, not two
- tests: tests/unit/test_panel_stage_use.py
- post-merge source of truth: clutch/panel.py

## Scope in / Scope out
Scope in: in `clutch/driver.py`, a fan-out path that reads the resolved route's `panel`; member assignment as section 1 of the plan in Context defines it (distinct candidates in row order when the row has at least `size` candidates, otherwise the first candidate repeats, recorded in `panel_facts`); drop-on-failure; the `panel_facts` signal. In `clutch/stages.py`, `clutch/requisition.py`, `clutch/runner.py` and `clutch/triage.py`, use of the combined result for review, requisition review, diagnosis and triage. In `docs/how-clutch-works.md`, update only the sections describing the driver call, review, diagnosis and triage to say a paneled row fans out and combines. Edit existing tests only where an assertion is forced to change.

Scope out: `implement` best-of-N (`implement-best-of-n`), scorecard attribution (`panel-scorecard`), `review_visual` and graphics judge use, and any change to `clutch/panel.py` or `Route` (owned by the depended tickets). Panels stay off by default; no config is edited.

## Scope fence
- clutch/driver.py
- clutch/stages.py
- clutch/requisition.py
- clutch/runner.py
- clutch/triage.py
- docs/how-clutch-works.md
- tests/unit/test_driver_panel_fanout.py
- tests/unit/test_panel_stage_use.py

## Acceptance criteria
1. With a fake provider and `panel: {size: 2, combine: findings-union}`, `./dev.py test tests/unit/test_driver_panel_fanout.py` shows two provider calls whose effect keys end in `/m0` and `/m1`, not a single call.
2. A row with no `panel` key makes exactly one call with the unsuffixed effect key; `test_driver_panel_fanout.py` asserts the key has no `/m` suffix.
3. When one member raises `ProviderCallError` and one succeeds, the stage returns the survivor's result and `panel_facts` lists the dropped member with its failure class; the test rules out `infra_error`.
4. When every member raises `ProviderCallError`, the stage result is `infra_error`, not a combined artifact.
5. Replaying after a crash with one member recorded makes only the missing member's call; `test_driver_panel_fanout.py` asserts the recorded member's fake provider is called zero times.
6. In `tests/unit/test_panel_stage_use.py`, two review members whose findings share `(code, path, line)` produce one finding with agreement `2/2`, and the written `review.md` verdict is the worst member verdict, not the first member's.
7. Diagnosis and triage with `majority-verdict` and a 1-1 tie return `escalate` and `declined` respectively, checked by `test_panel_stage_use.py`.
8. Exactly one `panel_facts` signal is journaled per combined stage, and none for a size 1 row, checked in `test_driver_panel_fanout.py`.
9. `./dev.py test tests/unit tests/integration/test_driver.py tests/integration/test_review_command.py` passes, showing unpaneled behavior is unchanged.

## Verification
```
./dev.py test tests/unit tests/integration/test_driver.py tests/integration/test_review_command.py
```

## Definition of rejected
- A panel runs by default or for a row without `panel`.
- Any change to unpaneled effect keys, artifacts or journal records.
- A combiner or `Route` edit, or an `implement` panel, in this diff.
- Two findings reported for one finding raised by two members.

## Time budget
- expected: 30m
- stuck: 60m
