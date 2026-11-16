---
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- clutch/driver.py::_invalid
- clutch/artifacts.py::DiagnosisReply

## Goal / Why
When a model reply fails schema validation because a string is over its length limit, the `invalid_artifact` finding's paved road names the offending field, its length and the limit, and says to shorten it or split it. Today `_invalid` in `clutch/driver.py` gives every validation error the same road: "reply with ONLY one JSON object matching the <Schema> schema, no prose". For an over-long Diagnose lesson that road does not fit the error. merge-admission-single-owner attempt 1 (2026-11-16) used all 4 diagnose calls and got a placeholder abandon-human. Three of those replies were valid JSON whose lessons were over `DIAGNOSIS_LESSON_CHARS` = 300 (lengths 324; 306; 343, 331, 303). The re-prompt never told the model which lesson was long or by how much, so it kept trimming blindly, and the verdict was discarded. Spec-only repairs (`diagnose-spec-lesson-length`, `diagnose-spec-first-char-json-reply`) already merged and did not close the gap. The fix is engine-side: the re-prompt finding carries an exact, actionable road.

## Scope in / Scope out
Scope in: in `clutch/driver.py`, change `_invalid` so that when any error in the `ValidationError` has type `string_too_long`, the `paved_road` lists each such error as its dotted location (for example `lessons.0`), the actual length of the input string, and the limit from the error's `ctx["max_length"]`. It tells the model to shorten that string to the limit, or for a list of strings to split it into separate entries within the list's own cap, and still says to reply with only the JSON object. Errors that are not `string_too_long` keep the existing road text byte-for-byte. The finding `code` and `message` are unchanged. No other edit to `clutch/driver.py`.
Scope out: no truncation of replies, no change to `DiagnosisReply` or the limits, no change to `clutch/specs/diagnose.md`, no change to the re-prompt loop or call cap, no new config.

## Scope fence
- clutch/driver.py
- tests/unit/test_driver_invalid_road.py

## Acceptance criteria
1. `_invalid` on the `ValidationError` from validating a `DiagnosisReply` JSON whose lessons are strings of 324, 306 and 10 characters returns a finding whose `paved_road` contains `lessons.0`, `324`, `lessons.1`, `306` and `300`, and does not contain `lessons.2`. Checked by `./dev.py test tests/unit/test_driver_invalid_road.py`; a test that only finds the old generic road text fails.
2. The same finding's `paved_road` still tells the model to reply with ONLY one JSON object, and its `code` is `invalid_artifact`.
3. `_invalid` on the error from a `DiagnosisReply` with an unknown `verdict` and valid lessons returns a `paved_road` equal to `reply with ONLY one JSON object matching the DiagnosisReply schema, no prose`, not a length road.
4. The test builds its stage as a `types.SimpleNamespace(emits=DiagnosisReply)` and reads no repo file, process or network.

## Verification
```
./dev.py test tests/unit/test_driver_invalid_road.py
```

## Definition of rejected
A branch that truncates or accepts over-long lessons, changes the lesson limit, edits the diagnose spec, or changes the paved road of non-length errors.

## Time budget
- expected: 20m
- stuck: 45m
