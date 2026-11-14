---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: confirmed
---

## Depends on
none

## Context
- chupa/rework.py
- tests/integration/test_rework.py

## Goal / Why
When rework splits an order into proposals where one depends on a sibling, the requisition reviewer for each proposal is told about the sibling proposals. Today `chupa/rework.py` writes every proposal into a scratch worktree `tree` and calls `review_ticket(repo=tree, ...)`. The `prior` JSON carries only `action`, `original_stem`, `original_ticket`, `snag_list` and `retry_findings`. The read-only reviewer call runs with `cwd=self._cwd`, the main checkout (`chupa/providers.py` line 338), where the siblings do not exist. On 2026-11-13 the vscode-help rework (attempt 3) failed its gate because a reviewer said sibling `vscode-help-registry` "exists nowhere in the repo". The umbrella went to the Reject queue and needed a hand re-split. After this change the `prior` block lists every other proposal of the same order (stem and full ticket text), with a note that they are part of the same order and will exist when it is accepted.

## Scope in / Scope out
Scope in: in `chupa/rework.py`, build the `prior` JSON in one module-level function `review_prior(action, original_stem, original_ticket, snag_list, retry_findings, proposals, current_stem)` and call it from the review loop. Its output keeps the five existing keys unchanged and adds `sibling_proposals`, a list of `{"stem", "ticket"}` for every proposal whose stem is not `current_stem`, plus `sibling_note`, a fixed sentence saying these tickets are part of the same rework order, are absent from the checkout the reviewer browses, and count as existing for dependency and fence checks. For `update` and for a single-proposal split `sibling_proposals` is `[]`. A function is used because the unit-tier floor on `chupa/rework.py` needs a unit test that does not build the integration context.
Scope out: `chupa/providers.py` cwd, `chupa/requisition.py`, the requisition review spec and its version, and `docs/`. The `prior` key set is not documented outside the code. The simpler approach of running the review with `cwd=tree` is rejected because it changes provider cwd policy for every read-only call and the Claude read-only tool restriction.
The existing tests in `tests/integration/test_rework.py` that capture `prior` pass unchanged because the five original keys keep their values.

## Scope fence
- chupa/rework.py
- tests/unit/test_rework_review_prior.py
- tests/integration/test_rework.py

## Acceptance criteria
1. `tests/unit/test_rework_review_prior.py` calls `review_prior` with proposals A and B and `current_stem="B"`. It asserts `json.loads(result)["sibling_proposals"] == [{"stem": "A", "ticket": <A text>}]`, not `[]` and not a list containing B.
2. The same file asserts that with a single proposal `sibling_proposals == []`, and that `action`, `original_stem`, `original_ticket`, `snag_list` and `retry_findings` equal the inputs, so the old keys are not dropped.
3. The same file asserts `sibling_note` is a non-empty string in both cases.
4. A split test in `tests/integration/test_rework.py` with two proposals, B depending on A, replaces `review_ticket` as the existing tests do and asserts the `prior` received for B parses to `sibling_proposals` containing A's stem and text, and the `prior` received for A contains B's. A `prior` with no `sibling_proposals` key fails it.
5. `./dev.py test tests/integration/test_rework.py tests/unit/test_rework_review_prior.py` exits 0.

## Verification
```
./dev.py test tests/integration/test_rework.py tests/unit/test_rework_review_prior.py
```

## Definition of rejected
The branch changes provider cwd handling or the requisition review spec, drops or renames any of the five existing `prior` keys, or passes only because the test does not read the `prior` the reviewer receives.

## Time budget
- expected: 25m
- stuck: 60m
