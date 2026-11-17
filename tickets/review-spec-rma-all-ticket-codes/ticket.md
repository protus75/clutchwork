---
state: confirmed
source: box:retro_finding
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/artifacts.py::ReviewVerdict

## On-demand
- clutch/specs/review.md

## Goal / Why
`clutch/specs/review.md` and the reply validator agree on what an `rma` reply may contain. Today the spec (Output format, last paragraph) says `rma` carries "at least one finding coded `ticket`", which allows a mix of codes. `ReviewVerdict._findings_match_verdict` in `clutch/artifacts.py` rejects an `rma` unless every finding is coded `ticket`. A reviewer that follows the spec can produce a reply the engine is certain to reject. On `defer-journal-window` attempt 0 this spent three review calls (about $1.60). The fourth call passed the validator by switching to `snag` and dropping the out-of-fence `ticket` finding. The ticket then merged with a break its Definition of rejected forbids. The spec must say how to report an out-of-fence break together with in-fence defects without dropping either.

## Scope in / Scope out
Scope in: edit `clutch/specs/review.md` only in these places.
- The `rma` bullet in `## Task` and the final paragraph of `## Output format` state that every finding in an `rma` reply is coded `ticket`, and that no other code is allowed in an `rma` reply.
- A short rule in the out-of-fence paragraph of `## Task` covers a mix of an out-of-fence break and in-fence defects. The reviewer replies `rma` and codes each in-fence defect `ticket` too, with its own `path`, `line`, `message` and `paved_road`, so no finding is dropped to fit the shape. The rule also says to use `rma` for in-fence defects only when an out-of-fence break is present, so a fixable diff is not sent to a human.
- Bump the spec `version` to the next minor above the version on main.
- In `tests/unit/test_specs.py`, change only the two `spec.meta.version == "1.6"` pins for `review.md` to the bumped value.
- In `tests/integration/test_stages.py`, change only the `review.spec_version == "1.6"` assertion in `test_implement_check_review_all_ok_with_artifacts_and_provenance` to the bumped value. This edit is forced by the version bump; add no test, fixture or helper there.
- Add a new test file `tests/integration/test_review_spec_rma_codes.py`. It reads the spec text and builds replies through the existing `ReviewVerdict` validator. It is under `tests/integration/` because it reads a repo file.

Scope out: no change to `clutch/artifacts.py` validation, to the `snag` rules, or to any other spec. No change to the prose of other sections.

## Scope fence
- clutch/specs/review.md
- tests/unit/test_specs.py
- tests/integration/test_stages.py
- tests/integration/test_review_spec_rma_codes.py

## Acceptance criteria
1. `clutch/specs/review.md` no longer contains the phrase "at least one finding coded `ticket`"; the Output format section states that every finding in an `rma` reply is coded `ticket`. Checked by `./dev.py test tests/integration/test_review_spec_rma_codes.py`, which fails if the old phrase is still in the spec.
2. The Task section tells the reviewer that when an out-of-fence break and in-fence defects occur together, the reply is `rma` and each in-fence defect is also coded `ticket`. A test asserts the spec's Task section contains this instruction, and fails if it is removed.
3. The test builds a `ReviewVerdict` with verdict `rma` and findings coded `ticket` and `acceptance` and asserts the validator raises. This confirms the shape the spec forbids is the shape the validator rejects. It builds an `rma` with only `ticket` findings and asserts it is accepted. Run with `./dev.py test tests/integration/test_review_spec_rma_codes.py`.
4. `spec.meta.version` of `clutch/specs/review.md` is the next minor above main's value, both pins in `tests/unit/test_specs.py` match it, and the `review.spec_version` assertion in `tests/integration/test_stages.py` matches it, checked by `./dev.py test tests/unit/test_specs.py` and `./dev.py test tests/integration/test_stages.py -k test_implement_check_review_all_ok_with_artifacts_and_provenance`.
5. `lint_spec` on `clutch/specs/review.md` returns `[]`, checked by `./dev.py test tests/integration/test_specs_json_reply_specs.py`.

## Verification
```
./dev.py test tests/integration/test_review_spec_rma_codes.py tests/unit/test_specs.py tests/integration/test_specs_json_reply_specs.py
./dev.py test tests/integration/test_stages.py -k test_implement_check_review_all_ok_with_artifacts_and_provenance
```

## Definition of rejected
The spec still allows an `rma` reply with a non-`ticket` finding. Or the spec tells the reviewer to drop an in-fence defect when an out-of-fence break is present. Or `clutch/artifacts.py` is changed to loosen the validator. Or the new test passes without checking the validator's rejection.

## Time budget
- expected: 15m
- stuck: 30m
