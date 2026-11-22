---
state: draft
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- llm-request-subject

## Context
- clutch/requisition.py::review_ticket
- clutch/providers.py::ClaudeAdapter.session_name
- clutch/llm.py::LLMRequest
- clutch/llm.py::FakeLLM
- tests/regress_requisition_events_owner_stem.py

## Goal / Why
Every Requisition Review `claude` session clutch starts shows up in the VS Code Claude panel as plain `Clutch Requisition Review`, with no ticket stem. Review, Rework and Diagnose sessions show `Clutch <Surface> <stem>` (see `evidence/`). With a dozen identical rows in the list, the owner cannot tell which ticket a Requisition Review session belongs to.

Cause: `ClaudeAdapter.session_name` appends `LLMRequest.ticket` when it is set. `review_ticket` in `clutch/requisition.py` has the reviewed ticket's `stem` in scope, but builds its request with `ticket=None`. After this ticket, that request carries `ticket=stem`, so the session is named `Clutch Requisition Review <stem>`.

The class fix (making every request name its subject so a dropped stem cannot pass silently) is `llm-request-subject`. This ticket is only the instance.

## Boundary contract
### Requisition Review LLM request
- disposition: extend
- owner: clutch/requisition.py
- consumers: `ClaudeAdapter.session_name` via `CliAdapter.invoke` (the only reader of `LLMRequest.ticket`)
- observable change: the Requisition Review request carries `ticket=<reviewed stem>`, so the `claude` argv ends with `--name "Clutch Requisition Review <stem>"`
- compatibility: restores the naming contract `claude-session-names` specified for this surface; journal keys, spool paths, engine log events and `event_context` are unchanged because none of them read `LLMRequest.ticket`
- acceptance: the regression reproducer sees the reviewed stem on the requisition_review request
- tests: `tests/regress_requisition_session_stem.py`
- post-merge source of truth: clutch/requisition.py

## Scope in / Scope out
In: in `review_ticket` in `clutch/requisition.py`, change the `LLMRequest(surface="requisition_review", ...)` argument `ticket=None` to `ticket=stem`. Add the reproducer `tests/regress_requisition_session_stem.py`, built on the same rig as `tests/regress_requisition_events_owner_stem.py`: a `FakeLLM` scripted with one author proposal and one approve verdict, an author `driver.run` with `ticket=None`, and `review_ticket` called with `stem="candidate"` from the stage's review hook. It reads `llm.requests`, picks the request whose `surface` is `requisition_review`, and prints `{"regression_result": "pass"}` with exit 0 when its `ticket` is `"candidate"`, or `{"regression_result": "defect"}` with exit 1 when it is anything else. It prints `{"regression_result": "error"}` with exit 2 when no requisition_review request was recorded. Add the new unit test `tests/unit/test_requisition_session_stem.py`. It runs `review_ticket` with a `FakeLLM` and `stem="abc"`, with a stub specs dir and context written under `tmp_path`, and asserts that the recorded requisition_review request has `ticket == "abc"`.
Out: every other `ticket=None` call site; those surfaces have no ticket. Renaming or retyping `LLMRequest.ticket` belongs to `llm-request-subject`. No change to `session_name`, the driver, or the journal.

## Scope fence
- clutch/requisition.py
- tests/regress_requisition_session_stem.py
- tests/unit/test_requisition_session_stem.py

## Acceptance criteria
1. `uv run python tests/regress_requisition_session_stem.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `defect` (not `error`) at the merge base, where the request carries `ticket=None`.
2. `./dev.py test tests/unit/test_requisition_session_stem.py` passes. It runs `review_ticket` with a `FakeLLM` and `stem="abc"`, with a stub specs dir and context written under `tmp_path`, and asserts that the recorded requisition_review request has `ticket == "abc"`, not `None`.
3. `./dev.py test tests/unit/test_claude_session_name.py` still passes, unchanged.

## Verification
```
uv run python tests/regress_requisition_session_stem.py
./dev.py test tests/unit/test_requisition_session_stem.py tests/unit/test_claude_session_name.py
```

## Definition of rejected
The change edits any file outside `clutch/requisition.py` other than the two new tests, renames `LLMRequest.ticket`, or changes the journal, spool, or `event_context` keying of requisition review.

## Time budget
- expected: 10m
- stuck: 20m

## Regression
```
uv run python tests/regress_requisition_session_stem.py
```
- carries: tests/regress_requisition_session_stem.py
