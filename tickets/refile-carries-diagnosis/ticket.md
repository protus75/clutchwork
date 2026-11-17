---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::rejection_reason
- tests/unit/test_roadmap_refile.py
- clutch/status.py::reject_queue

## Goal / Why
Row 94's re-file promises the rejected stem's reason as the request, but `rejection_reason` reads a `reason` field on `reject_verdict` signals, and no `reject_verdict` the engine writes carries one (0 of 40 kill verdicts in the journal on 2026-11-17). So it always returns the literal "rejected", and `tests/unit/test_roadmap_refile.py` passes only because it journals a hand-made `reason` on a `reject_verdict`. After this ticket, a re-filed row's request carries the rejected stem's last Reject-queue reason and its last Diagnose lessons, both read from events the engine really writes: the `reason` on the latest `state_transition` for the stem that has `routed: reject_queue` (written by `clutch/runner.py`), and the `lessons` list on the latest `diagnosis` signal for the stem (written by `clutch/runner.py`). The refile test journals those events instead of a made-up field.

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py::rejection_reason` returns the last Reject-queue reason for the stem, taken from the latest `state_transition` event for that stem whose body has `routed == "reject_queue"` (its `reason` field), followed by the lessons of the stem's latest `diagnosis` signal (its `lessons` list), joined into one string. With neither event it returns the literal "rejected". It no longer reads `reject_verdict`.
- Both existing callers (the refile path and the status wait line) keep calling `rejection_reason(events, stem)` with the same signature; they change only if the return shape forces it.
- `tests/unit/test_roadmap_refile.py::test_rejected_linked_row_is_rewritten`: replace the hand-made `reject_verdict` `reason` event with a routed `state_transition` carrying a `reason` and a `diagnosis` signal carrying `lessons`, then assert both appear in the re-filed message summary. This is the one expectation that may change in that file.
Scope out: `clutch/runner.py` and what it journals; `status.reject_queue`; the re-file cap and stem renaming; docs outside the code (no document describes the field).

## Scope fence
- clutch/roadmap.py
- tests/unit/test_roadmap_refile.py
- tests/unit/test_roadmap_rejection_reason.py

## Acceptance criteria
1. In `tests/unit/test_roadmap_rejection_reason.py`, with a journal holding a `state_transition` `{"to": "premise_failed", "reason": "bad premise", "routed": "reject_queue"}` and a `diagnosis` signal `{"lessons": ["fix the path"]}` for the stem, `rejection_reason` returns a string containing both `bad premise` and `fix the path`, not `"rejected"`; run by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.
2. In the same file, when two routed terminals exist for the stem, the returned reason is the later one's, not the earlier one's; and a `state_transition` without `routed` is ignored; checked by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.
3. In the same file, with no routed terminal and no diagnosis for the stem, `rejection_reason` returns exactly `"rejected"`, and events of another stem are never read; checked by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.
4. In the same file, a `reject_verdict` signal carrying a `reason` field alone yields `"rejected"`, not that reason, ruling out the old read; checked by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.
5. `tests/unit/test_roadmap_refile.py::test_rejected_linked_row_is_rewritten` journals no `reason` on a `reject_verdict`, and its assertion on `box.messages()[-1].summary` finds both the terminal reason and the diagnosis lesson plus `[re-file 1]`; checked by `./dev.py test tests/unit/test_roadmap_refile.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_rejection_reason.py tests/unit/test_roadmap_refile.py tests/unit/test_roadmap_status.py
```

## Definition of rejected
A branch where `rejection_reason` still reads `reason` from `reject_verdict`, or where the refile test still journals a hand-made `reject_verdict` reason, or where any change touches `clutch/runner.py`.

## Time budget
- expected: 20m
- stuck: 40m
