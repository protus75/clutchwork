---
state: draft
source: box:retro_finding
priority: P3
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/integration/test_specs_json_reply_specs.py

## Goal / Why
`clutch/specs/requisition_review.md` already says the reply starts with `{`, ends with `}`, has no prose, markdown or code fence around it, and that reasoning goes in `summary`. It also says to re-emit the same verdict as bare JSON when `retry_findings` reports an invalid reply schema. This is the fix for the earlier finding (box-000285, merged as `requisition-review-bare-json-reply`). No test pins that wording for this spec: `tests/integration/test_specs_json_reply_specs.py` covers only author, triage, rework, retro and implement. A later spec edit could drop the wording without any gate failing, and the requisition reviewer would again wrap its verdict in prose or a fence, wasting a retry. This ticket adds the pin and changes no spec text.

## Scope in / Scope out
Scope in: add a new test file `tests/integration/test_requisition_review_bare_json.py`. It reads the requisition review prompt spec and asserts two things. The `## Output format` section contains the sentence "The first character of your reply is `{` and the last is `}`; no prose, markdown or code fence surrounds the object, and reasoning goes in `summary`." The `## On-failure` section contains "re-emit the same verdict as bare JSON".

Scope out: the requisition review prompt spec itself (no wording or version change), the engine parser (it must not accept fenced replies), the allowed verdicts and findings, and the existing JSON-reply tests.

## Scope fence
- tests/integration/test_requisition_review_bare_json.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_requisition_review_bare_json.py` passes. It asserts the bare-JSON sentence is inside the `## Output format` section of the spec, so a spec that has the sentence only elsewhere fails.
2. The same test asserts "re-emit the same verdict as bare JSON" is inside the `## On-failure` section. A spec with that sentence removed makes `./dev.py test tests/integration/test_requisition_review_bare_json.py` fail, not pass.
3. `git diff --name-only` against main lists only `tests/integration/test_requisition_review_bare_json.py`, checked with `git diff --name-only main`.

## Verification
```
./dev.py test tests/integration/test_requisition_review_bare_json.py
```

## Definition of rejected
Any edit to `clutch/specs/requisition_review.md` or to the engine reply parser, or a test that still passes when the sentence is removed from the spec.

## Time budget
- expected: 10m
- stuck: 20m
