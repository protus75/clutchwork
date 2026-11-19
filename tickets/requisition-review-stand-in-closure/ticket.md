---
state: draft
source: box:retro_finding
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/integration/test_requisition_review_whole_value_closure.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Requisition review approves tickets whose Scope in makes production code read an attribute that hand-built test stand-ins lack. Three tickets did this in retro/58 window: route-kinds-filter-r1 (`route.kinds` vs `SimpleNamespace` routes in tests/unit/test_gemini_adapter.py and tests/unit/test_qwen_adapter.py), projection-leftovers (`Redactor.from_config(config, env)` vs `SimpleNamespace(state_dir=tmp_path)` configs in tests/unit/test_drain_driver_overlap.py and tests/unit/test_driver_hooks.py), and status-hot-paths (`Ticket.scope_fence` vs ticket stand-ins in several unit and integration tests). Each cost an Implement run, a premise_bounce cap and a reject diagnosis; two reached the Reject queue.

The existing closure bullets match on a name (changed symbols, recorded constants, set members, whole-value comparisons, patched functions). A duck-typed stand-in never names the type it imitates, so none finds it.

After this ticket the requisition review spec carries one more fence-closure bullet. When Scope in makes a path read an attribute or field of a type that path did not read before (a new model field, a newly consumed config attribute, a required field now read by a new caller), the reviewer greps `tests/` for hand-built stand-ins of that type (`SimpleNamespace(...)`, ad-hoc fake classes, partial dicts) and raises a snag for each one that both reaches the changed read and lacks the attribute. The finding names the reaching call. Paved road: fence the stand-in and add a Scope-in line that adds only that attribute to it, or raise a snag; never a `getattr` fallback in production code. Stand-ins that never reach the changed read, or already carry the attribute, are not hits (about 557 `SimpleNamespace(` uses exist across 145 test files, so a broad rule would make fences far too wide).

Rule home: this is a rule about how Clutch's own requisition review judges tickets, so it lives in the shipped spec only.

Measurable aim: in later retro windows, no premise_bounce comes from a stand-in lacking an attribute newly read by an approved ticket's Scope in.

## Boundary contract
### Requisition review spec
- disposition: extend
- owner: clutch/specs/requisition_review.md
- consumers: the requisition review stage, which renders the spec as its prompt
- observable change: the Task bullet list gains one fence-closure bullet; the spec `version` goes to the next minor above the version on main
- compatibility: every existing bullet is unchanged and the reply format is unchanged; the new bullet only adds a snag condition
- acceptance: the rendered spec contains the stand-in attribute bullet with its narrowing conditions and paved road; both version pins match the bumped version
- tests: tests/integration/test_requisition_review_stand_in_closure.py and the two version pins
- post-merge source of truth: clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in:
- Add one bullet to the Task list of `clutch/specs/requisition_review.md`, directly after the whole-value-comparison bullet. It states: the trigger (a path newly reads an attribute or field of a type); the grep of `tests/` for hand-built stand-ins (`SimpleNamespace(...)`, ad-hoc fake classes, partial dicts); the narrowing (a hit must both reach the changed read and lack the attribute; the finding names the reaching call; stand-ins that never reach it or already carry the attribute are not hits); the paved road (fence the hit and add a Scope-in line adding only that attribute, or raise a snag; never a `getattr` fallback in production code).
- Bump the spec `version` to the next minor above the version on main (do not use a literal target), and update the version pins in `tests/unit/test_specs.py` and `tests/integration/test_specs_delimiter_note.py` to match.
- Add `tests/integration/test_requisition_review_stand_in_closure.py`, modeled on the existing whole-value closure test, that reads the spec through a `Path(__file__)` anchor.

Scope out: other spec bullets, the requisition code in `clutch/requisition.py`, any lint rule, and all documentation. No docs describe this bullet text, so none change.

## Scope fence
- clutch/specs/requisition_review.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_requisition_review_stand_in_closure.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_requisition_review_stand_in_closure.py` passes; it asserts the spec text names `SimpleNamespace`, requires a hit to both reach the changed read and lack the attribute, requires the finding to name the reaching call, and forbids a `getattr` fallback. The test fails on the unmodified spec (no bullet present), not just on a missing word.
2. `./dev.py test tests/integration/test_requisition_review_stand_in_closure.py` also asserts the Task list has exactly one more bullet than before and that each pre-existing bullet's first sentence is still present, so the existing bullets are not replaced.
3. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` passes with the `requisition_review` version pin equal to the spec front matter `version`, which is higher than the version on main; a stale pin of the old version fails.
4. `./dev.py test tests/integration/test_requisition_review_whole_value_closure.py` still passes, showing the existing closure bullets are unchanged.

## Verification
```
./dev.py test tests/integration/test_requisition_review_stand_in_closure.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_requisition_review_whole_value_closure.py
```

## Definition of rejected
The bullet tells the reviewer to fence every stand-in of the type regardless of reach or existing attribute, or suggests a `getattr` fallback in production code; or the spec version is a literal not derived from main's version, or a version pin is left stale; or any existing bullet is reworded.

## Time budget
- expected: 15m
- stuck: 30m
