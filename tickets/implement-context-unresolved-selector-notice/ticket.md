---
state: confirmed
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/stages.py::implement_inputs
- clutch/tickets.py::render_context

## Goal / Why
On 2026-11-22 serve stopped with `ValueError: Python selector 'implement_reply' must match exactly one definition`. The ticket `shared-review-script` was correct when reviewed. Its retry started from the prior branch (merged `retry-keeps-prior-branch`), and that branch had moved the Context-selected definitions to `tests/stage_replies.py`. `implement_inputs` calls `render_context` on the worktree, and `render_context` raises a bare ValueError when a selector matches zero or several definitions. Only lint turns that ValueError into a finding. Merged `serve-contains-dispatch-exception` keeps serve alive, but the ticket still spends an infra attempt and repeats the same crash on every later retry.

When this ticket is done, a Context selector that no longer resolves in the worktree no longer raises out of `implement_inputs`. That entry renders as a one-line notice naming the entry and the resolution error and telling the agent to read the file from its worktree. The other Context entries render unchanged. The ticket is not blamed for a branch change it did not cause.

Simpler approach rejected: resolving selectors against main. It needs a new git read path and a main ref inside a pure rendering helper. The fallback notice needs only a try/except at the one call site, and the agent can read the moved definitions directly.

Class prevention: the guard sits in `implement_inputs`, the single owner of Implement's Context rendering for every retry. `requisition.py` also calls `implement_inputs`, so every future caller inherits it.

## Boundary contract
### Implement context rendering
- disposition: extend
- owner: clutch/stages.py (`implement_inputs`)
- consumers: `implement_stage` in clutch/stages.py, and the requisition review calls in clutch/requisition.py
- observable change: a ticket Context entry whose selector raises ValueError in `render_context` renders as `(selector does not resolve in this worktree: <error>; read the file directly)` under its `### <entry>` heading, instead of raising
- compatibility: entries that resolve render byte-identically; non-ticket context files are read as before; a missing file still raises as before; `render_context` and lint behavior are unchanged
- acceptance: unit test in a new test file renders a worktree where one selector fails and one succeeds
- tests: tests/unit/test_stages_context_unresolved.py
- post-merge source of truth: clutch/stages.py

## Scope in / Scope out
Scope in: in `implement_inputs`, catch ValueError from `render_context` for a ticket Context entry and render the notice above in its place. Add the new unit test file. Because the fenced stages.py has a coverage floor, the unit test covers the added lines using `tmp_path` only (no repo files, no process).
Scope out: `clutch/tickets.py` and lint, which still report an unresolvable selector as a finding. Also out: retry or branch policy, serve exception containment, and docs, since no documented behavior changes.

## Scope fence
- clutch/stages.py
- tests/unit/test_stages_context_unresolved.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_stages_context_unresolved.py` shows that `implement_inputs` on a `tmp_path` repo whose Context lists `a.py::gone` (no such definition) and `b.md` returns normally. The test rules out a ValueError escaping.
2. `./dev.py test tests/unit/test_stages_context_unresolved.py` asserts the `context` value contains `### a.py::gone` followed by the notice text, and does not contain an empty body for that entry.
3. `./dev.py test tests/unit/test_stages_context_unresolved.py` asserts the `b.md` entry renders its full file text exactly as before, so the notice is not applied to entries that resolve.
4. `./dev.py test tests/unit/test_stages_context_unresolved.py` asserts a selector that matches two definitions in the file renders the notice too, not the first match.

## Verification
```
./dev.py test tests/unit/test_stages_context_unresolved.py tests/integration/test_tickets.py tests/integration/test_requisition.py tests/integration/test_implement_related_files_prompt.py
```

## Definition of rejected
The branch changes `render_context`, lint findings, or retry policy. The branch swallows errors other than the selector ValueError. The branch silently drops the entry with no notice.

## Time budget
- expected: 12m
- stuck: 24m
