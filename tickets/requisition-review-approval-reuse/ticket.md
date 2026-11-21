---
state: rejected
source: human
priority: P0
kind: feature
---

## Depends on
- requisition-review-input-identity

## Runs before
- requisition-review-compact-context

## Context
- clutch/requisition.py
- clutch/runner.py::drive
- clutch/__main__.py::_review
- clutch/caps.py::capability
- clutch/journal.py::Journal.append
- clutch/providers.py::_route
- tests/approval.py
- tests/integration/test_requisition_gate.py
- tests/unit/test_requisition_prior_review.py
- clutch/help.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md#3. Tickets

## Goal / Why
Stop paying for a repeated buildability investigation when its substantive inputs have not changed. CLI ticket review currently always calls the model, while dispatch reuses any historical approval matching only the ticket blob. Replace those different decisions with one conservative rule at both entry points: reuse only the latest verdict for the stem when it is an approval whose recorded `input_identity` (written by `requisition-review-input-identity`) matches the current inputs. Preserve approval across confirmation-only state changes and ticket-only intake commits; invalidate it on relevant code, input or reviewer changes. This is orchestration class prevention: reuse evidence with checked provenance instead of suppressing required review.

## Boundary contract
### Requisition approval identity
- disposition: extend
- owner: clutch/requisition.py
- consumers: clutch/__main__.py::_review and clutch/runner.py::drive
- observable change: both consumers reuse only the latest applicable approved verdict whose recorded input identity matches current review inputs, before provider preflight or invocation
- compatibility: old journal events remain readable but approvals without an identity are stale; provisional, snag, rma and invalid replies never authorize a skip; the ticket-SHA-only dispatch bypass is removed and no parallel legacy reuse path remains
- acceptance: identical inputs and draft-to-confirmed state-only changes produce zero additional provider calls; changed code or review material forces a review
- tests: tests/unit/test_review_reuse_cli.py, tests/unit/test_review_reuse_dispatch.py and tests/integration/test_requisition_reuse.py
- post-merge source of truth: clutch/requisition.py

## Scope in / Scope out
Scope in:
- Add one approval-selection function in clutch/requisition.py that takes the stem's journal history and the current identity from the existing `review_input_identity` gatherer and returns the reusable approval or None: it looks only at the latest requisition_verdict for the stem, never searching past a newer snag/rma/provisional to resurrect an approval; a missing, null or mismatching identity, or a null current identity, means fresh review.
- CLI `_review` calls that decision with config.routing_default_tier before constructing or preflighting the provider; on reuse it reports the reused approval and makes no provider call or new verdict event.
- Dispatch in runner.drive replaces the ticket-SHA-only approval check with the same decision at capability(ticket, history)[0]. Keep admission refusal precedence, provisional unmerged-dependency behavior, the real dependency gates and failure routing.
- Different effective reviewer tiers and changed review inputs intentionally invalidate reuse. In every scripted integration test where the effective reviewer tier or the review inputs change between the fixture approval and the next `agent()` call, insert a fresh requisition `verdict()` approve response before that `agent()`. This covers tests/integration/test_ladder.py (retry-wall, rework-escalation, escalation-rung and operator-confirm reset cases, currently failing with `assert None is not None` on `LLMRequest(surface='requisition_review').worktree` when unadjusted), tests/integration/test_diagnose.py (the infra-cap test edits tracked config after its fixture approval), tests/integration/test_drain_reentry.py (re-entry scripts), tests/integration/test_drain.py (rework and split scripts), tests/integration/test_merge_model_resolve.py and tests/integration/test_retro_box.py. Refreshing shared fixture approvals does not fix these scripts; each needs its own scripted verdict. Preserve the Implement ladder and each script's existing assertions.
- Update the existing gate test in tests/integration/test_requisition_gate.py whose legacy SHA-only approval previously bypassed review.
- Shared fixture configs: `tests/approval.py::approve` records `input_identity` from `review_input_identity`, which is None when `providers._route` finds no review route at the fixture's dispatch tier, so those fixture approvals no longer authorize dispatch. Add the review route at the tier each fixture dispatches at to the shared configs `CONFIG` in tests/integration/test_stages.py, `CONFIG` in tests/integration/test_cli.py and `_CONFIG` in tests/harness/shakeout/bench.py, and adjust tests/integration/serve_rig.py and tests/integration/test_serve_parallel_admission.py (which rewrite config.yaml from the test_cli root) only where their scripts still fail. Do not make `review_input_identity` tolerate a missing route; identity composition is scope-out.
- Add fake-driven unit tests for the selection logic and each entry point with injected seams, and integration tests for both entry points using zero-call assertions.
- Update the CLI review help text, the `clutch/docs/host-running.md` verb row, and the requisition section of docs/how-clutch-works.md to explain the recorded identity, conservative reuse and invalidation. Update the clutch/help.py extension entry if its ticket-review description states the superseded behavior.
Scope out:
- Identity composition, the verdict field and writer migration (delivered by `requisition-review-input-identity`).
- No time-based approval expiry, new config flag, cache service, learned dependency tracker, speculative delta-review framework, or reuse of a changed ticket beyond confirmation state. Context packing is delivered by `requisition-review-compact-context`.

## Scope fence
- clutch/requisition.py
- clutch/runner.py
- clutch/__main__.py
- clutch/help.py
- tests/unit/test_review_reuse_cli.py
- tests/unit/test_review_reuse_dispatch.py
- tests/integration/test_requisition_reuse.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_ladder.py
- tests/integration/test_stages.py
- tests/integration/test_cli.py
- tests/integration/serve_rig.py
- tests/integration/test_serve_parallel_admission.py
- tests/integration/test_diagnose.py
- tests/integration/test_drain_reentry.py
- tests/integration/test_drain.py
- tests/integration/test_merge_model_resolve.py
- tests/integration/test_retro_box.py
- tests/harness/shakeout/bench.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py` proves a second identical CLI review, its confirmation-only transition and dispatch reuse approval with zero extra preflight/model calls.
2. `./dev.py test tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py` proves changes to code, Context bytes, sibling material, coverage, specs or substantive ticket text force a new review, and that legacy approvals without identity and approvals followed by a newer snag/rma cannot authorize reuse.
3. `./dev.py test tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py` proves both entry points preserve provisional and admission-refusal behavior; unit tests reach the changed IO composition with injected seams.
4. `./dev.py test tests/integration/test_ladder.py tests/integration/test_requisition_reuse.py` proves a CLI default-tier approval is reused by dispatch when tiers match, a reviewer-tier change forces exactly one new review, and tracked working-tree edits can be approved and reused until their bytes change.
5. `./dev.py test tests/integration/test_stages.py tests/integration/test_cli.py tests/integration/test_serve_parallel_admission.py tests/integration/test_shakeout.py` proves fixture approvals from the shared configs record a non-null identity and still authorize dispatch.
6. `./dev.py test tests/integration/test_diagnose.py tests/integration/test_drain_reentry.py tests/integration/test_drain.py tests/integration/test_merge_model_resolve.py tests/integration/test_retro_box.py` proves scripts whose review inputs or reviewer tier change after the fixture approval pass with one scripted fresh requisition review each and keep their existing assertions.

## Verification
```
./dev.py test tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py tests/integration/test_ladder.py tests/unit/test_requisition_input_identity.py tests/integration/test_review_command.py tests/unit/test_requisition_prior_review.py tests/integration/test_stages.py tests/integration/test_cli.py tests/integration/test_serve_parallel_admission.py tests/integration/test_shakeout.py tests/integration/test_diagnose.py tests/integration/test_drain_reentry.py tests/integration/test_drain.py tests/integration/test_merge_model_resolve.py tests/integration/test_retro_box.py
```

## Definition of rejected
Removing required checks without evidence, keeping the ticket-SHA-only bypass or any second production reuse authority, adding speculative settings, making `review_input_identity` tolerate a missing route, or changing files outside the fence.

## Time budget
- expected: 30m
- stuck: 60m