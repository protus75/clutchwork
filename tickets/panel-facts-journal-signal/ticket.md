---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- panel-scorecard
- review-panel-stage-use

## Context
- docs/stage-panels-plan.md#3. Execution
- docs/stage-panels-plan.md#Risks
- clutch/panel.py::PanelFacts
- clutch/panel.py::PanelMember
- clutch/scorecard.py::project_scorecard
- clutch/scorecard.py::panel_lines
- clutch/scorecard.py::PanelScorecard
- clutch/journal.py::SIGNAL_NAMES
- clutch/stages.py::review
- clutch/stages.py::diagnose
- clutch/triage.py::_settle_pass
- tests/fakes.py::FakeJournal
- docs/how-clutch-works.md#9.6 Scorecard and baseline

## Goal / Why
Row 217 of the roadmap. The panels plan (Target design sections 1 and 3) calls for one journaled `panel_facts` signal per combined stage, carrying each member's provider and model and saying whether its agreement is between distinct models or repeated samples of one model. Today `review` (`clutch/stages.py`), `diagnose` (`clutch/stages.py`) and triage (`clutch/triage.py::_settle_pass`) write `panel_facts` only through `driver.log.event`, the engine log, which rotates, is not in the journal window, and is diagnostics. The scorecard, a pure fold of the journal window, therefore cannot see provider or model: `project_scorecard` builds every `PanelMember` with provider and model `"unknown"`, and a panel of two samples of one model scores the same as a panel of two models, though the plan's Risks section says the two kinds of agreement differ and must be kept apart.

After this ticket each paneled review, diagnose and triage pass appends one journal `signal` event named `panel_facts` and no longer writes the engine-log line (one record, no dual path; the journal is the record, the engine log is not). `project_scorecard` reads the review signals: slot rows are unchanged, and a new per-agreement-kind breakdown separates panel reviews whose members were distinct models (`models`) from those whose members were repeated samples (`samples`), each with its reviews, findings two or more members raised (agreed findings) and confirmed unique catches. `panel_lines` prints that breakdown after the slot table when at least one review in the window carries a signal. A window with no `panel_facts` signal, such as a journal written before this change, projects and prints exactly as today.

Signal shape. `Journal.append(EventType.SIGNAL, body, ticket=<stem or None>, key=None)` with `body = {"signal": "panel_facts", "surface": "review" | "diagnose" | "triage", "attempt": <int>, **PanelFacts.model_dump()}`; so the body carries `combiner`, `member_count`, `members` (each `provider`, `model`, `verdict`), `verdict_counts`, `dropped`, `merged`, `kept_index` and `agreement_kind` exactly as the old log line did. Review and diagnose set `ticket=stem`; triage has no ticket, sets `ticket=None` and adds `"box_id": message.id` and `"attempt": pass_no`, as the log line did. `PanelFacts` itself is unchanged. `"panel_facts"` joins `SIGNAL_NAMES`.

How the scorecard pairs signal and group. The signal is appended after the member calls complete, in the same attempt. For each review panel group `(stem, run, attempt)` the scorecard takes the latest `panel_facts` signal with `surface == "review"`, the group's `stem` as `event.ticket` and the group's `attempt`, whose journal index is after the group's last completion and before the next group of the same `(stem, attempt)`; no run number is added to the signal. The signal is usable only when its `members` validate as `PanelMember` and `len(members)` equals the number of present slots (the slots whose reply validated); then `members[i]` belongs to the i-th present slot in ascending slot order, matching `findings_union`'s reply order. Otherwise the group folds exactly as today with the `"unknown"` placeholder members and joins no kind row.

Definitions for the new rows, over the same panel reviews as the slot rows: agreed findings = the count of `MergedFinding` from `findings_union` whose `members` has two or more entries; unique catches = the confirmed unique findings already counted per slot, summed over the kind's reviews; reviews = panel reviews with a usable signal of that `agreement_kind`. Worked example: two signaled panel reviews of ticket `a`, attempt 0 with `agreement_kind "models"` where F1 is raised by both slots and F2 by slot 1 only, and attempt 1 with `agreement_kind "samples"` where both approve with no findings; `a` merges later. The `models` row is reviews 1, agreed 1, unique catches 1; the `samples` row is reviews 1, agreed 0, unique catches 0.

Rejected simpler approach: keep the engine-log line and read it from the scorecard. That needs a log reader inside a pure journal fold and loses data at rotation, and the CLAUDE.md rule that the journal is the record, never a debug log, puts a record the scorecard folds in the journal.

## Boundary contract
### panel_facts signal
- disposition: replace
- owner: clutch/stages.py (`review`, `diagnose`) and clutch/triage.py (`_settle_pass`) write it; clutch/journal.py owns the signal name
- consumers: `project_scorecard` in clutch/scorecard.py; operators reading the journal
- observable change: the `panel_facts` record moves from the engine log to a journal `signal` event with the body in Goal / Why; the engine-log event named `panel_facts` is no longer written; `SIGNAL_NAMES` gains `panel_facts`
- compatibility: the body fields are the old log line's fields plus the `signal` name; `PanelFacts`, the combiners and every artifact (`review.md`, `diagnosis.json`) are unchanged; no code reads the old engine-log line; a single-member (size 1) stage still writes no signal; requisition review is not a panel surface and writes none
- acceptance: the new and updated unit tests assert the journaled body for each of the three surfaces and that no engine-log `panel_facts` event is written
- tests: tests/unit/test_review_panel_use.py, tests/unit/test_diagnosis_panel_use.py, tests/unit/test_triage_panel_use.py, tests/integration/test_closed_sets.py
- post-merge source of truth: clutch/journal.py (`SIGNAL_NAMES`), clutch/stages.py and clutch/triage.py (the append sites)

### Panel scorecard agreement kinds
- disposition: extend
- owner: clutch/scorecard.py
- consumers: `render_report` in clutch/retro.py and `render` in clutch/status.py, through `panel_lines`
- observable change: `PanelScorecard` gains a last field `kinds: tuple[PanelKindRow, ...]` (`PanelKindRow(kind: str, reviews: int, agreed_findings: int, unique_catches: int)`, rows ordered `models` then `samples`, a kind absent from the window has no row); `panel_lines` appends a second table when `kinds` is nonempty
- compatibility: `PanelSlotRow`, `PANEL_OUTCOMES`, the outcomes, slot rows, cost multiplier and the existing `panel_lines` output are unchanged for a window with no usable signal, and `kinds` is `()` there
- acceptance: the new scorecard unit test asserts the worked example's rows and rendering, and that unsignaled windows are byte-identical to today
- tests: tests/unit/test_panel_scorecard_kinds.py; tests/unit/test_panel_scorecard.py and tests/integration/test_scorecard.py pass unchanged
- post-merge source of truth: clutch/scorecard.py and docs/how-clutch-works.md section 9.6

## Scope in / Scope out
Scope in:
- `clutch/journal.py`: add `"panel_facts"` to `SIGNAL_NAMES`; nothing else changes there.
- `clutch/stages.py`: in `review` and `diagnose`, replace each `ctx.driver.log.event("panel_facts", ...)` with `ctx.driver.journal.append(EventType.SIGNAL, {"signal": "panel_facts", "surface": ..., "attempt": attempt, **facts.model_dump()}, ticket=<stem>)` (the review site passes `stem`, the diagnose site `ticket.stem`). `EventType` is already imported there; nothing else changes.
- `clutch/triage.py`: in `_settle_pass`, replace `driver.log.event("panel_facts", ...)` with `driver.journal.append(EventType.SIGNAL, {"signal": "panel_facts", "box_id": message.id, "attempt": pass_no, "surface": "triage", **facts.model_dump()})`. `EventType` is already imported there.
- `clutch/scorecard.py`: `PanelKindRow`, the `kinds` field on `PanelScorecard`, the signal pairing and fold described in Goal / Why inside `project_scorecard`, and the second table in `panel_lines`: after the existing lines, `""`, `"| Agreement | Reviews | Agreed findings | Unique catches |"`, `"| --- | ---: | ---: | ---: |"`, then one `| <kind> | reviews | agreed | unique |` row per kind. When a usable signal exists its members replace the `"unknown"` placeholder in the `findings_union` call; with none, the placeholder stays. A malformed signal body (missing or non-list `members`, a member failing `PanelMember` validation, an `agreement_kind` outside `models` and `samples`, a non-integer `attempt`) is skipped, never raises.
- `docs/how-clutch-works.md` section 9.6: extend the panel scorecard bullet to say the scorecard also reads the journaled `panel_facts` signal and separates distinct-model from repeated-sample reviews. Edit only that bullet.
- `tests/unit/test_review_panel_use.py`, `tests/unit/test_diagnosis_panel_use.py`, `tests/unit/test_triage_panel_use.py`: switch their `panel_facts` assertions from the engine-log fake to the journal (a `FakeJournal` on the driver fake; assert the single `signal` event's body, ticket and key `None`, and that the engine-log fake records no `panel_facts` event). The remaining assertions in those files stay.
- `tests/integration/test_closed_sets.py`: add `"panel_facts"` to the expected `SIGNAL_NAMES` set in `test_journal_closed_sets_and_constants`.
- A new test file `tests/unit/test_panel_scorecard_kinds.py` (in-memory `Event` lists as in `tests/unit/test_panel_scorecard.py`, `FakeJournal` from `tests/fakes.py`). The implementer creates its clutch meta header with `uv run clutch meta refresh tests/unit/test_panel_scorecard_kinds.py` and then edits only the `# purpose:` line to a non-empty one-line sentence.
- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.

Scope out: `PanelFacts` and `clutch/panel.py`; `Driver.run_panel`; requisition review (not a panel surface, owner decision 2026-11-21); `clutch/retro.py` and `clutch/status.py` (they already print `panel_lines`); slot-row and cost-multiplier definitions; a run number on the signal; reading old engine-log lines; the extension; the roadmap; prompt specs.

## Scope fence
- clutch/journal.py
- clutch/stages.py
- clutch/triage.py
- clutch/scorecard.py
- docs/how-clutch-works.md
- tests/unit/test_review_panel_use.py
- tests/unit/test_diagnosis_panel_use.py
- tests/unit/test_triage_panel_use.py
- tests/unit/test_panel_scorecard_kinds.py
- tests/integration/test_closed_sets.py

## Acceptance criteria
1. A two-member `review` panel appends exactly one journal event of type `signal` whose body has `signal == "panel_facts"`, `surface == "review"`, the attempt, `members` carrying each member's real provider and model, and `agreement_kind`, with `ticket` set to the stem and `key` `None`; the engine-log fake records no `panel_facts` event, not the old log line: `./dev.py test tests/unit/test_review_panel_use.py`.
2. The same holds for `diagnose` (`surface == "diagnose"`, `ticket` the stem): `./dev.py test tests/unit/test_diagnosis_panel_use.py`.
3. Triage with a panel appends one signal with `surface == "triage"`, `box_id`, `attempt` equal to the pass number and `ticket` `None`, and no engine-log `panel_facts`; a size-1 pass and a pass whose members all fail append none: `./dev.py test tests/unit/test_triage_panel_use.py`.
4. `SIGNAL_NAMES` equals the expected closed set including `"panel_facts"`, a real `Journal.append` of that name is accepted, and the engine-signal scan finds the name in `clutch/stages.py` and `clutch/triage.py`: `./dev.py test tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py`.
5. For the worked example in Goal / Why, `project_scorecard(window).panel.kinds` equals `(PanelKindRow("models", 1, 1, 1), PanelKindRow("samples", 1, 0, 0))`, the slot rows are unchanged, and `panel_lines` ends with the exact second table in Scope in, not one merged row and not both kinds counted as `samples`: `./dev.py test tests/unit/test_panel_scorecard_kinds.py`.
6. A window with panel reviews and no `panel_facts` signal gives `kinds == ()` and `panel_lines` output identical to the existing slot-table output; a signal whose `members` length differs from the present slots, a malformed member, an unknown `agreement_kind`, or a non-integer `attempt` is skipped without raising and joins no kind row; a signal for another stem or attempt, or `surface == "diagnose"`, is never paired with a review group: `./dev.py test tests/unit/test_panel_scorecard_kinds.py`.
7. A usable signal's providers and models reach `findings_union` in place of `"unknown"`: a test passes members with real providers and checks the attribution still lands on the right slot when slot 0 is absent and slots 1 and 2 are present: `./dev.py test tests/unit/test_panel_scorecard_kinds.py`.
8. The existing slot, status and retro behavior is unchanged: `./dev.py test tests/unit/test_panel_scorecard.py tests/integration/test_scorecard.py tests/integration/test_status.py tests/integration/test_retro.py` pass without edits.
9. The section 9.6 panel scorecard bullet names the journaled `panel_facts` signal and the `models` and `samples` split: read `docs/how-clutch-works.md` section 9.6.
10. The new test file header carries a non-empty `# purpose:` and all seven keys: `uv run clutch meta check tests/unit/test_panel_scorecard_kinds.py`.

## Verification
```
./dev.py test tests/unit/test_review_panel_use.py tests/unit/test_diagnosis_panel_use.py tests/unit/test_triage_panel_use.py tests/unit/test_panel_scorecard_kinds.py tests/unit/test_panel_scorecard.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py tests/integration/test_scorecard.py tests/integration/test_status.py tests/integration/test_retro.py
uv run clutch meta check tests/unit/test_panel_scorecard_kinds.py
```

## Definition of rejected
- Any engine-log `panel_facts` event is still written, or a second journal signal name carries the same facts.
- The scorecard reads the engine log, or `"unknown"` remains the provider and model used when a usable signal exists.
- A size-1 stage, requisition review, or a failed panel writes a signal.
- A test is skipped or an existing slot, status or retro expectation is weakened to pass.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one signal move across three call sites plus one scorecard fold; splitting would leave the scorecard reading a signal nothing writes.
