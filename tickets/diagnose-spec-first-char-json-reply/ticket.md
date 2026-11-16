---
state: draft
source: box:retro_finding
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/unit/test_specs.py

## On-demand
- clutch/specs/diagnose.md

## Goal / Why
The Diagnose spec's Output format tells the model that the first character of its reply is `{` and the last is `}`, with no prose, markdown or code fence around the object, and that verdict reasoning goes in the lessons. Today it says only "Reply with ONLY one JSON object". On provider-failure-single-mapper, diagnose call 0/2 opened with prose before the object. `Driver` parses the reply with `unwrap_fence`, which strips only a fence that wraps the whole reply, so the reply was rejected and a paid re-prompt followed (call 0/3, $0.17). If the re-prompts run out, Diagnose falls back to the mechanical `abandon-human` verdict, which can send a buildable ticket to the Reject queue. `clutch/specs/requisition_review.md` already carries the same rule (line 89), added by requisition-review-bare-json-reply and review-spec-first-char-json-reply (retro/48).

## Scope in / Scope out
Scope in:
- In `clutch/specs/diagnose.md` `## Output format`, add one sentence: "The first character of your reply is `{` and the last is `}`; no prose, markdown or code fence surrounds the object, and reasoning goes in the lessons." The sentence goes after the JSON shape and before the line starting "Give 1 to 5 non-blank lessons".
- Bump the `version` in the `clutch/specs/diagnose.md` frontmatter to the next minor above the version on main.
- In `tests/unit/test_specs.py`, change only the diagnose version expectation in `test_spec_lint_accepts_the_implement_and_requisition_specs` to the bumped version. The bump forces this edit.
- Add a new test file `tests/integration/test_diagnose_spec_json_reply.py` that pins the sentence.

Scope out: every other section of `diagnose.md`, the parser or `unwrap_fence`, `clutch/specs/requisition_review.md`, and any other spec. The parser accepts bare JSON, so banning fences cannot reject a reply that passes today.

## Scope fence
- clutch/specs/diagnose.md
- tests/unit/test_specs.py
- tests/integration/test_diagnose_spec_json_reply.py

## Acceptance criteria
1. `tests/integration/test_diagnose_spec_json_reply.py` loads `clutch/specs/diagnose.md`, takes the text after `## Output format`, and asserts it contains "The first character of your reply is `{` and the last is `}`", "no prose, markdown or code fence surrounds the object" and "reasoning goes in the lessons". The test fails when the sentence is removed, not only when the whole section is removed.
2. The same test asserts the sentence sits inside the `## Output format` section and not in `## Task` or `## On-failure`.
3. `load_spec` of `clutch/specs/diagnose.md` reports a `meta.version` that is the next minor above the version on main (`1.6`), not `1.6`, and `lint_spec` returns `[]`. `tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs` expects that version.
4. `tests/integration/test_author.py` still passes. Its `1.6` pin is for `author.md`, not `diagnose.md`.

## Verification
```
./dev.py test tests/integration/test_diagnose_spec_json_reply.py tests/unit/test_specs.py tests/integration/test_author.py
```

## Definition of rejected
The branch edits any section of `diagnose.md` other than the Output format and the version, changes parser code, or leaves the diagnose version unbumped.

## Time budget
- expected: 10m
- stuck: 30m
