---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
none

## Context
- clutch/driver.py::PanelResult
- clutch/driver.py::Driver.run_panel
- clutch/stages.py::review
- tests/unit/test_review_panel_use.py
- tests/unit/test_driver_panel_fanout.py

## Goal / Why
When a review panel drops a member, the member's findings (for example `quota_exhausted`) must survive. Today `Driver.run_panel` records only `DroppedMember(index, failure_class)` and discards the failed `StageResult.findings`. When every member is dropped, `stages.review` returns `StageResult(outcome="infra_error", findings=[])`. `runner.drive` stops for quota only when a result's findings carry `quota_exhausted`, so a size-1 review stops the run but a size-N review draws an infra cap unit and retries. After this ticket the all-dropped review result carries the dropped members' findings, so the same provider failure is handled the same way with or without a panel route.

This is the review-surface instance of the loss that `review-panel-stage-use-requisition` notes for requisition. That ticket avoids it in requisition by re-raising, and does not fix `review`.

## Boundary contract
### Panel result
- disposition: extend
- owner: clutch/driver.py (`PanelResult`, `Driver.run_panel`)
- consumers: `clutch/stages.py::review`; tests that build `PanelResult` positionally with two arguments
- observable change: `PanelResult` gains `dropped_findings: list[Finding]`, defaulting to empty, holding the findings of every dropped member in member order. `DroppedMember` and `PanelFacts` are unchanged, so the journaled `panel_facts` event is byte-identical.
- compatibility: existing two-argument `PanelResult(members, dropped)` construction stays valid; the partial-drop path (some members ok) is unchanged
- acceptance: a size-2 panel where both members return `infra_error`, one carrying a `quota_exhausted` finding, yields a review `StageResult` containing that finding
- tests: new unit test file for the panel and the review stage
- post-merge source of truth: clutch/driver.py

### Review stage all-dropped result
- disposition: extend
- owner: clutch/stages.py::review
- consumers: `clutch/runner.py::drive` (reads `result.findings` for `quota_exhausted`; unchanged)
- observable change: when `panel.members` is empty, the returned `StageResult` is `infra_error` with `findings=panel.dropped_findings` instead of `[]`. A quota failure on a panel member reaches `failure_terminal` the way it does for a single reviewer.
- compatibility: with no dropped findings the result is `StageResult("infra_error", None, [], Cost())` as before
- acceptance: see criteria 1 and 2
- tests: new unit test file
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in: in `clutch/driver.py`, add the defaulted `dropped_findings` field to `PanelResult` and fill it in `run_panel` where a member is dropped (`result.findings` of the `infra_error` result). Import `Finding` there only if not already imported. In `clutch/stages.py::review`, return those findings in the all-dropped `StageResult`. Add `tests/unit/test_review_panel_dropped_findings.py`.

Scope out: `clutch/panel.py` (`DroppedMember`, `PanelFacts`, combiners); `clutch/runner.py` (already routes on findings); requisition review (see `review-panel-stage-use-requisition`); the partial-drop path, which keeps the surviving members' verdict.

## Scope fence
- clutch/driver.py
- clutch/stages.py
- tests/unit/test_review_panel_dropped_findings.py

## Acceptance criteria
1. `Driver.run_panel` with size 2, where both runs return `infra_error` and the first carries a `quota_exhausted` Finding, returns a `PanelResult` whose `dropped_findings` contains that Finding, not `[]` (`./dev.py test tests/unit/test_review_panel_dropped_findings.py`).
2. `stages.review` with a size-2 panel whose `PanelResult` has no members and a `quota_exhausted` dropped finding returns outcome `infra_error` with that finding in `findings`, not `[]`; with no dropped findings it still equals `StageResult("infra_error", None, [], Cost())` (`./dev.py test tests/unit/test_review_panel_dropped_findings.py`).
3. The partial-drop case is unchanged: one member dropped, one ok yields the surviving verdict and the `panel_facts` event `dropped` list still equals `[{"index": 0, "failure_class": "infra_error"}]` (`./dev.py test tests/unit/test_review_panel_use.py tests/unit/test_driver_panel_fanout.py`).
4. A result carrying the `quota_exhausted` finding from criterion 2 satisfies the `runner.drive` quota test (`any(f.code == "quota_exhausted" for f in result.findings)`), so it takes `failure_terminal` and not the infra cap draw; the test asserts this on the returned findings (`./dev.py test tests/unit/test_review_panel_dropped_findings.py`).

## Verification
```
./dev.py test tests/unit/test_review_panel_dropped_findings.py tests/unit/test_review_panel_use.py tests/unit/test_driver_panel_fanout.py
```

## Definition of rejected
The branch changes `DroppedMember`, `PanelFacts` or the journaled `panel_facts` payload, edits `runner.py`, or turns a partial drop into a failure.

## Time budget
- expected: 20m
- stuck: 40m
