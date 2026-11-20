---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- clutch/artifacts.py::Finding
- clutch/artifacts.py::ReviewVerdict
- clutch/artifacts.py::DiagnosisReply
- clutch/artifacts.py::FrozenModel
- clutch/triage.py::TriageReply
- docs/stage-panels-plan.md#Target design
- docs/stage-panels-plan.md#Risks

## Goal / Why
Roadmap row 65 (stage panels plan, ticket 1). Today no code can merge several independent model replies into one. After this ticket `clutch/panel.py` holds the three pure combiners the panels plan names and the `PanelFacts` model the later driver ticket (`review-panel`) journals as the `panel_facts` signal body. `findings-union` merges review replies, `majority-verdict` picks the verdict most members gave, and `best-of-n` picks the kept implementation candidate. They take and return the existing reply models (`ReviewVerdict`, `DiagnosisReply`, `TriageReply`), so every downstream gate is unchanged. Nothing calls them yet: no config key, no driver fan-out, no journal write. That keeps this the smallest ticket the later panel tickets, `doc-review-runner` and the graphics judge majority can stand on (roadmap decision 14: one panel mechanism).

Rules the code implements, all from the panels plan:
- `findings-union`: the verdict is the worst any member gave (`rma` over `snag` over `approve`). Findings merge on `(code, path, line)`; a finding with no line joins the earliest group with the same `(code, path)` and otherwise starts its own; a finding with a line that has no exact group joins an existing `(code, path, None)` group before starting its own. A merged finding keeps the first member's `paved_road`, keeps each distinct message once in member order joined by a newline, and records `agreement: k/N` and the member indexes that raised it in `PanelFacts`. The summary is each member's summary in member order. `ReviewVerdict` refuses an `rma` reply that carries a non-`ticket` finding, so the combined `rma` reply carries only the merged `ticket` findings; every merged group, `rma` or not, stays in `PanelFacts.merged`.
- `majority-verdict`: the verdict most members gave; the reply is the first member's in that majority. A tie goes to the verdict earliest in a caller-supplied safer-first order; a tied verdict absent from that order raises `ValueError`. The module exports the two orders the plan states, `("escalate", "retry")` for diagnosis and `("declined", "author")` for triage.
- `best-of-n`: over candidates carrying `check_passed`, `soft_findings` and `inserted_lines`, keep the candidate that passed Check, then fewest soft findings, then fewest inserted lines, then lowest index; with no passing candidate keep none. Every other candidate is retired.
- `PanelFacts`: the combiner, the member count, each member's provider, model and verdict, the verdict counts, the dropped members with their failure class, the merged-finding agreement, the kept index for `best-of-n`, and `agreement_kind` (`samples` when every surviving member has the same provider and model, else `models`; the plan's correlated-members risk).

## Boundary contract
### Panel combiners
- disposition: create
- owner: clutch/panel.py
- consumers: none in this ticket; `review-panel` (driver fan-out for review, requisition review, diagnosis, triage), `implement-best-of-n`, and `doc-review-runner` call the combiners, and `review-panel` journals `PanelFacts` as the `panel_facts` signal body
- observable change: new importable pure functions `findings_union`, `majority_verdict`, `best_of_n` and the model `PanelFacts`; no CLI, config, journal, or file change
- compatibility: nothing imports the module, so no existing behavior or artifact shape changes; `ReviewVerdict`, `DiagnosisReply` and `TriageReply` are used unchanged
- acceptance: each combiner's rule and tie-break is pinned by a unit test that fails on the wrong result; the combined review reply always validates as a `ReviewVerdict`
- tests: `tests/unit/test_panel_combiners.py`, `tests/integration/test_panel_purity.py`
- post-merge source of truth: clutch/panel.py
- closest existing: `clutch/artifacts.py::ReviewVerdict`, `clutch/artifacts.py::DiagnosisReply` and `clutch/triage.py::TriageReply` model one reply and merge nothing; `clutch/scorecard.py` counts catches for one reviewer and chooses no reply
- earning reason: several production consumers (review, requisition review, diagnosis, triage, `doc-review-runner`, `implement-best-of-n`, the graphics judge) need one merge rule; the roadmap decision 14 forbids a second fan-out in any plan

## Scope in / Scope out
Scope in: create `clutch/panel.py` with the three combiners, the two tie-break orders, and `PanelFacts` (with its member, dropped-member and merged-finding sub-models), built on `FrozenModel` and `NonBlank` imported from `clutch/artifacts.py`. The module is pure: no I/O, no clock, no logging, and no import of the driver, providers, config or journal. Create `tests/unit/test_panel_combiners.py` for behavior and `tests/integration/test_panel_purity.py` for the import-set check, which reads `clutch/panel.py` through a `Path(__file__)` anchor.

Scope out: the `Route.panel` key, config validation and the surface-fit refusal (`panel-routing-config`); the driver fan-out, member effect keys, the `panel_facts` journal write and any documentation of the signal (`review-panel`); the scorecard attribution (`panel-scorecard`); best-of-N worktrees, running Check on candidates and counting inserted lines (`implement-best-of-n`); the `review_visual` surface, which has no reply model yet. No documentation changes: the module has no caller, so nothing documented is false, and `review-panel` documents the mechanism when it wires it.

## Scope fence
- clutch/panel.py
- tests/unit/test_panel_combiners.py
- tests/integration/test_panel_purity.py

## Acceptance criteria
1. Two `ReviewVerdict` members, one `approve` and one `snag`, combine to verdict `snag`, not `approve`; with an `rma` member present the verdict is `rma`, not `snag`: `./dev.py test tests/unit/test_panel_combiners.py`.
2. Two members raising a finding with the same `(code, path, line)` yield one merged finding, not two, with `PanelFacts.merged` agreement `2/2` and both member indexes; two members citing the same `(code, path)` on different lines stay two findings; a lineless finding merges into the earliest same `(code, path)` group: `./dev.py test tests/unit/test_panel_combiners.py`.
3. A merged finding keeps both members' differing messages in member order and keeps a message two members share once; the summary lists each member's summary in member order: `./dev.py test tests/unit/test_panel_combiners.py`.
4. A combined `rma` reply carries only `ticket`-coded findings and validates as a `ReviewVerdict`, while `PanelFacts.merged` still lists a `snag` finding raised by another member: `./dev.py test tests/unit/test_panel_combiners.py`.
5. `majority_verdict` over three `DiagnosisReply` members with verdicts `retry`, `escalate`, `escalate` returns the first `escalate` member's reply, not the first member's; a 1-1 tie of `retry` and `escalate` with the diagnosis order returns `escalate`, not `retry`; the same tie shape for triage returns `declined`, not `author`; a tie containing a verdict absent from the order raises `ValueError`: `./dev.py test tests/unit/test_panel_combiners.py`.
6. `best_of_n` keeps the passing candidate with fewest soft findings, then fewest inserted lines, then lowest index; it keeps a passing candidate with more soft findings over a failing one with fewer; it keeps none, not candidate 0, when none passed; every non-kept index is listed as retired: `./dev.py test tests/unit/test_panel_combiners.py`.
7. `PanelFacts` reports `agreement_kind` `samples` when all surviving members share one provider and model and `models` otherwise, lists dropped members with their failure class, counts verdicts, and rejects an unknown combiner name or extra field: `./dev.py test tests/unit/test_panel_combiners.py`.
8. `clutch/panel.py` imports none of `clutch.driver`, `clutch.providers`, `clutch.config`, `clutch.journal`, `clutch.seams`, and performs no file or process access: the integration test parses the module with `ast` and asserts the import set: `./dev.py test tests/integration/test_panel_purity.py`.
9. The full suite and the closed-set scans still pass with the new module (`FrozenModel` and `NonBlank` are imported, not redefined): `./dev.py test tests/integration/test_closed_sets_single_owner.py tests/integration/test_closed_sets_remaining.py tests/integration/test_vocabularies.py`.

## Verification
```
./dev.py test tests/unit/test_panel_combiners.py
./dev.py test tests/integration/test_panel_purity.py
./dev.py test tests/integration/test_closed_sets_single_owner.py tests/integration/test_closed_sets_remaining.py tests/integration/test_vocabularies.py
```

## Definition of rejected
- A combiner that reads or writes a file, the journal, or the clock, or imports the driver, providers or config.
- A combined review reply that fails `ReviewVerdict` validation, or a downstream reply model changed to carry agreement.
- A duplicate definition of `FrozenModel`, `NonBlank`, or a verdict vocabulary already owned by `clutch/artifacts.py`.
- A config key, journal write, driver change, or documentation of a signal nothing emits yet.

## Time budget
- expected: 15m
- stuck: 30m
