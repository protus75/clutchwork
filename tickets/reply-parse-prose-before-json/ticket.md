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
- clutch/driver.py::unwrap_fence
- clutch/requisition.py

## On-demand
- tests/integration/test_driver.py

## Goal / Why
A model reply that opens with prose and then holds exactly one top-level JSON object parses on the first call, with no schema retry. Today `unwrap_fence` returns the text unchanged unless the whole reply is one fenced block, so `model_validate_json` fails on any lead-in sentence. Spools from 2026-11-15..17 show 15/417 requisition_review, 7/164 review, 11/270 author and 5/135 triage replies starting with prose, each costing a retry. Retro 53 reopened box-000283 with 5 extra calls on 4 reviews. Two spec-wording fixes already failed (box-000283, box-000287), so this fixes the shared parse seam instead of adding a third wording patch. All callers (`clutch/driver.py`, `clutch/author.py`, `clutch/requisition.py`, `clutch/scorecard.py`, `clutch/stages.py`, `clutch/triage.py`) get the fix through the one helper.

## Boundary contract
### Reply text unwrapping
- disposition: extend
- owner: clutch/driver.py::unwrap_fence
- consumers: driver stage parse, author, requisition, scorecard, review stage, triage
- observable change: when the text is not one fenced block and does not already start with `{` after whitespace, and exactly one top-level JSON object can be decoded from it, that object's text is returned. Zero or several top-level objects return the text unchanged, so validation still fails closed and the retry path runs.
- compatibility: a single fenced block, a bare object, and text with no or several objects return exactly what they do today. Only a reply that was a validation failure before (prose plus one object) now succeeds.
- acceptance: unit tests cover prose before one object, prose around one object, two objects, no object, braces in prose, and braces inside JSON strings
- tests: tests/unit/test_driver_unwrap_prose.py
- post-merge source of truth: clutch/driver.py::unwrap_fence

## Scope in / Scope out
Scope in: in `clutch/driver.py`, extend `unwrap_fence` in place. Keep the one-fence strip first and unchanged. If it did not match and the stripped text does not start with `{`, scan each `{` with `json.JSONDecoder.raw_decode`, skip positions inside an already decoded object, and collect the decoded top-level objects (dicts only). Return the object's source slice when there is exactly one; otherwise return the text unchanged. Add `import json` there. In `tests/integration/test_driver.py`, the one expectation that may change is the `'prose first\n```json\n{"a": 1}\n```'` case of `test_unwrap_fence`, which now expects `'{"a": 1}'`. Add new tests in the new file.

Scope out: no spec wording changes, no provider JSON-mode request, no journal event for the extraction (the measured effect is the drop in schema retries), no caller changes, no documentation edits.

## Scope fence
- clutch/driver.py
- tests/unit/test_driver_unwrap_prose.py
- tests/integration/test_driver.py

## Acceptance criteria
1. `unwrap_fence('Verdict: approve.\n{"a": 1}')` returns `'{"a": 1}'`, not the input unchanged; checked by `./dev.py test tests/unit/test_driver_unwrap_prose.py`.
2. A reply with two top-level objects (`'x {"a": 1} y {"b": 2}'`) and a reply with none (`'no json here'`) are returned unchanged, not the first object; checked by `./dev.py test tests/unit/test_driver_unwrap_prose.py`.
3. Prose with stray braces before the object (`'see {not json} then {"a": {"b": 1}}'`) returns `'{"a": {"b": 1}}'`, and a nested object is not counted as a second top-level object; a string value containing `}` inside the object does not truncate it; checked by `./dev.py test tests/unit/test_driver_unwrap_prose.py`.
4. Fenced input, bare-object input and the `````` fence-in-fence case keep their current outputs, and the prose-then-fence case now returns the bare object; checked by `./dev.py test tests/integration/test_driver.py -k unwrap_fence`.
5. A prose-led reply fed through `RequisitionReply.model_validate_json(unwrap_fence(text))` validates, where it raised `ValidationError` before; checked by `./dev.py test tests/unit/test_driver_unwrap_prose.py`.

## Verification
```
./dev.py test tests/unit/test_driver_unwrap_prose.py tests/integration/test_driver.py
```

## Definition of rejected
A branch that accepts replies with zero or several top-level objects, adds a per-spec wording change, adds a second parse path beside `unwrap_fence`, or edits a caller instead of the shared helper.

## Time budget
- expected: 15m
- stuck: 30m
