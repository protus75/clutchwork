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
- clutch/artifacts.py::DiagnosisReply
- clutch/artifacts.py::Diagnosis
- clutch/stages.py::diagnose
- clutch/driver.py::_invalid
- tests/integration/test_diagnose.py
- docs/how-clutch-works.md#6.3 Diagnosis

## Goal / Why
A Diagnose reply is no longer discarded because one lesson is a few characters over `DIAGNOSIS_LESSON_CHARS` (300). Today `DiagnosisReply` refuses the whole reply, the driver re-prompts, and the model rewrites every lesson on each call, so the loop does not converge. Since 2026-11-11, 42 Diagnose runs made 89 calls (47 extra). Only 10 were valid on the first call, and 28 had an over-long lesson. Overruns are small: median 12 characters, and 51 of 66 overruns are 25 characters or fewer. merge-admission-single-owner attempt 1 lost all its lessons to a placeholder `abandon-human`. The spec-only fixes (`diagnose-spec-lesson-length`, `diagnose-spec-first-char-json-reply`) have merged and did not close the gap. `diagnose-over-long-lesson-road` changed only the re-prompt advice and was rejected on 2026-11-16.

After this change, a reply whose only schema violation is lessons longer than 300 characters (after stripping surrounding whitespace) is valid. Each over-long lesson is trimmed to at most 300 characters at a word boundary, and the indexes of the trimmed lessons are recorded in `diagnosis.json`. The 300-character limit stays stated in `clutch/specs/diagnose.md` and stays 300 in code. Every other violation (bad verdict, zero or more than 5 lessons, blank lesson, unknown key, non-string lesson) still invalidates the reply. A reply that merged code accepts stays accepted.

## Scope in / Scope out
Scope in:
- `clutch/artifacts.py`: `DiagnosisReply` gets a `trimmed_lessons: list[int]` field (default `[]`) and a `model_validator(mode="before")`. For each string lesson, the validator strips it first and trims only when the stripped length is over `DIAGNOSIS_LESSON_CHARS`. It cuts the stripped text at the last whitespace within the first 300 characters, or at exactly 300 characters if there is none, then strips trailing whitespace. Because the text is stripped first, a trimmed lesson is never blank. It records the zero-based index of each trimmed lesson, overwriting any `trimmed_lessons` the model supplied. Lessons not trimmed are left as given. The `max_length` constraint on the lesson string stays as the backstop. `Diagnosis` gets the same `trimmed_lessons: list[int] = []` field, so existing `diagnosis.json` files still load.
- `clutch/stages.py::diagnose`: pass `reply.trimmed_lessons` into `write_diagnosis` and onto the written `Diagnosis`. The mechanical placeholder path writes `[]`.
- `tests/integration/test_diagnose.py`: the parametrized case `{"verdict": "retry", "lessons": ["x" * 301]}` in `test_reply_schema_refuses_invalid_shape` no longer holds. Remove only that case. Add one test there that drives `diagnose` end to end with a scripted over-long lesson.
- `docs/how-clutch-works.md` section 6.3: add one sentence saying an over-long lesson is trimmed and recorded in `diagnosis.json` `trimmed_lessons`, not refused.
- New `tests/unit/test_diagnosis_lesson_trim.py` for the model-level behavior.

Scope out: `DIAGNOSIS_LESSON_CHARS`, `DIAGNOSIS_MAX_LESSONS`, the Diagnose prompt spec (so the `tests/unit/test_specs.py` pins stay valid), the driver module and its re-prompt advice, other stages' schemas, and the journal event shapes.

## Scope fence
- clutch/artifacts.py
- clutch/stages.py
- tests/integration/test_diagnose.py
- tests/unit/test_diagnosis_lesson_trim.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_diagnosis_lesson_trim.py` exits 0. Its tests build replies by hand from the observed overrun lengths (324, 306, 343, 331, 303), because the saved spools are untracked. `DiagnosisReply.model_validate` on `{"verdict": "retry", "lessons": [<324-char text of 5-character words>]}` returns a reply whose lesson has at most 300 characters and ends on a whole word, not a validation error. Its `trimmed_lessons` is `[0]`, not `[]`.
2. In that file, a 400-character lesson with no whitespace is cut to exactly 300 characters. A 300-character lesson and a 299-character lesson are left byte-identical with `trimmed_lessons == []`, so the trim does not fire at or under the limit.
3. In that file, with lessons of 100, 320 and 100 characters, only the middle lesson is trimmed. The result has `trimmed_lessons == [1]`, and lessons 0 and 2 are unchanged.
4. In that file, a reply that supplies `"trimmed_lessons": [9]` with all lessons within the limit returns `trimmed_lessons == []`, not `[9]`.
5. In that file, these still raise `ValidationError`: `verdict` "maybe", empty `lessons`, a whitespace-only lesson, 6 lessons, an unknown key, and a non-string lesson. A fix that trims or coerces other violations fails these.
6. In that file, `' ' * 300 + 'x' * 100` validates (as merged code accepts it) with `trimmed_lessons == []`, and `' ' + 'x' * 399` validates with the lesson equal to `'x' * 300` and `trimmed_lessons == [0]`, not a validation error.
7. `./dev.py test tests/integration/test_diagnose.py` exits 0. The new end-to-end test scripts a first and only provider reply with one 324-character lesson and asserts exactly one provider call. The written `diagnosis.json` has `verdict` "retry", `mechanical` null, the trimmed lesson of at most 300 characters, and `trimmed_lessons == [0]`. It must not show the `abandon-human` placeholder or a second call.
8. `./dev.py test tests/integration/test_closed_sets.py tests/unit/test_specs.py` exits 0, showing `DIAGNOSIS_LESSON_CHARS` is still 300 and the spec's 300-character sentences are unchanged.
9. `grep -n "trimmed_lessons" docs/how-clutch-works.md` prints a line inside section 6.3.

## Verification
```
./dev.py test tests/unit/test_diagnosis_lesson_trim.py tests/integration/test_diagnose.py tests/integration/test_closed_sets.py tests/unit/test_specs.py
```

## Definition of rejected
The branch is thrown away if it raises `DIAGNOSIS_LESSON_CHARS` or changes `clutch/specs/diagnose.md`. It is also thrown away if it trims or coerces any violation other than an over-long lesson, adds a compat or dual path, makes a reply invalid that merged code accepts, or leaves invalid a Diagnose reply whose only schema violation is one or more lessons whose stripped text is longer than 300 characters.

## Time budget
- expected: 40m
- stuck: 90m
