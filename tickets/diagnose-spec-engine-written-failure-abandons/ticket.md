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
- tests/integration/test_diagnose_spec_json_reply.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py

## On-demand
- clutch/specs/diagnose.md

## Goal / Why
The Diagnose prompt defines `abandon-human` only as credentials, external environment, or an unreadable cause. It says nothing about a failure written onto the candidate by an engine step after Implement (Check's meta refresh, a generated block, a rebase). On `spools-capture-keys` attempt 0, Diagnose named the engine cause (`meta._render` in `clutch/meta.py` writes a trailing space for an empty value, outside the fence) and still chose `retry` with a lesson to write `# purpose:` headers by hand. Attempt 1 failed the same `ruff format` gate and cost an extra Implement, Check and diagnosis. `serve-polls-block-parallel-runs` spent a retry on the same defect. The merged `meta-render-empty-purpose-no-trailing-space` fixed that one defect, not the Diagnose behavior.

After this ticket `clutch/specs/diagnose.md` says: when the run record or checks show that an engine step wrote the failing lines onto the candidate after Implement, and the cause is in engine code outside the fence, choose `abandon-human`, and the lessons name the engine file and the defect so the fix can be ordered ahead. It never chooses `retry` with a lesson asking the implementer to pre-empt the engine's output. A failure the implementer's own diff produced keeps the normal verdicts.

## Boundary contract
### Diagnose prompt spec
- disposition: extend
- owner: clutch/specs/diagnose.md
- consumers: `diagnose_stage` in clutch/stages.py and the diagnosis eval in eval/diagnose.py, which render the spec
- observable change: the `abandon-human` verdict description gains an engine-written-failure case, with an explicit carve-out that implementer-produced content keeps the normal verdicts; the spec version bumps
- compatibility: reply shape, verdict vocabulary, placeholders, lesson limits and every other rule are unchanged
- acceptance: a test over the spec text checks the new rule, its evidence condition, and the carve-out
- tests: tests/integration/test_diagnose_spec_engine_cause.py and the version pins in tests/unit/test_specs.py and tests/integration/test_specs_delimiter_note.py
- post-merge source of truth: clutch/specs/diagnose.md

## Scope in / Scope out
Scope in: in `clutch/specs/diagnose.md`, extend the `abandon-human` bullet (or add one rule paragraph directly under the verdict list) with the engine-written-failure rule. The rule fires only when the run record or checks show an engine step wrote the failing lines onto the candidate after Implement and the cause is engine code outside the fence. It tells Diagnose to name the engine file and the defect in the lessons, and not to choose `retry` with a lesson asking the implementer to pre-empt the engine output. A failure whose failing content the implementer's diff produced keeps `retry`, `escalate`, `split` or `reject`. Bump the spec `version` to the next minor above the version on main. Update the diagnose version pin at `tests/unit/test_specs.py` (the tuple loop near the top) to that value. Update the `("diagnose", "1.8")` parametrize entry in `tests/integration/test_specs_delimiter_note.py` to the same bumped value; nothing else changes in that file. Add the new test file.
Scope out: the eval fixture corpus under `eval/` and its fixed size of 12 stay as they are; `clutch/stages.py`, `clutch/meta.py` and every other spec stay as they are.

## Scope fence
- clutch/specs/diagnose.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_diagnose_spec_engine_cause.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_diagnose_spec_engine_cause.py` loads `clutch/specs/diagnose.md` via `Path(__file__)` and asserts the `abandon-human` description mentions an engine step writing the failing content onto the candidate after Implement, and mentions naming the engine file and defect in the lessons; the test fails on the current spec, which has neither.
2. `./dev.py test tests/integration/test_diagnose_spec_engine_cause.py` also asserts the rule is conditioned on the run record or checks showing the engine step wrote the lines, and that content the implementer's diff produced keeps the normal verdicts; an unconditional "engine failures abandon" wording fails that assertion.
3. `./dev.py test tests/integration/test_diagnose_spec_engine_cause.py` also asserts the spec tells Diagnose not to choose `retry` with a lesson that asks the implementer to pre-empt engine output.
4. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py` passes with the diagnose version pins at the bumped value; the old value no longer matches `load_spec(text).meta.version`.
5. `./dev.py test tests/integration/test_diagnose_spec_json_reply.py tests/integration/test_diagnose_eval.py tests/integration/test_spec_unit_io_seam.py` passes, so the reply shape, the 12-case corpus render and the unit I/O rule text are unchanged.

## Verification
```
./dev.py test tests/integration/test_diagnose_spec_engine_cause.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_diagnose_spec_json_reply.py tests/integration/test_diagnose_eval.py tests/integration/test_spec_unit_io_seam.py
```

## Definition of rejected
The rule applies without evidence that an engine step wrote the failing lines, or drops the carve-out for implementer-produced content. The change edits files outside the fence, adds an eval fixture, or changes the reply shape or lesson limits.

## Time budget
- expected: 12m
- stuck: 24m
