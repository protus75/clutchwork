---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Runs before
- requisition-review-compact-context

## Context
- clutch/requisition.py
- clutch/author.py::author
- clutch/rework.py::rework
- tests/approval.py
- clutch/runner.py::drive
- clutch/__main__.py::_review
- clutch/git.py
- clutch/journal.py::Journal.append
- tests/integration/test_requisition_gate.py
- tests/unit/test_requisition_prior_review.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md#3. Tickets

## Goal / Why
Stop paying for a repeated buildability investigation when its substantive inputs have not changed. CLI ticket review currently always calls the model, while dispatch reuses any historical approval matching only the ticket blob. Replace those different decisions with one conservative input-identity rule at both entry points. Preserve approval across confirmation-only state changes and ticket-only intake commits; invalidate it on relevant code, input or reviewer changes. This is orchestration class prevention: reuse evidence with checked provenance instead of suppressing required review.

## Boundary contract
### Requisition approval identity
- disposition: extend
- owner: clutch/requisition.py
- consumers: clutch/__main__.py::_review and clutch/runner.py::drive
- observable change: both consumers reuse only the latest applicable approved verdict whose recorded input identity matches current review inputs, before provider preflight or invocation
- compatibility: old journal events remain readable but approvals without the new identity are stale; provisional, snag, rma and invalid replies never authorize a skip; no parallel legacy reuse path remains
- acceptance: identical inputs and draft-to-confirmed state-only changes produce zero additional provider calls; changed code or review material forces a review
- tests: tests/unit/test_requisition_input_identity.py and tests/integration/test_requisition_reuse.py
- post-merge source of truth: clutch/requisition.py

### Requisition verdict journal body
- disposition: extend
- owner: clutch/requisition.py and the existing requisition_verdict signal
- consumers: CLI review and engine dispatch writers and approval reader
- observable change: extend the existing signal with deterministic input identity and retain existing verdict metadata; use the same identity in both writers
- compatibility: no new signal name, journal envelope version, hand-edited journal, database or authoritative side cache
- acceptance: a later non-approval supersedes an older approval; unknown or missing identity causes a fresh review
- tests: tests/unit/test_requisition_input_identity.py and tests/integration/test_requisition_reuse.py
- post-merge source of truth: clutch/requisition.py and journaled requisition_verdict

## Scope in / Scope out
Scope in:
- Compose one conservative deterministic identity from canonical ticket content (ignore only frontmatter state), current tracked non-ticket repository tree content, actual selected Context bytes, coverage-map content, overlapping sibling material, full reviewer and Implement spec bytes, and resolved reviewer tier/candidate/panel identity. Exclude prior verdict prose, invocation IDs, timestamps and retry feedback from semantic identity. Detect non-ticket working-tree edits before reuse; if the inspected tree cannot be established, perform a fresh review rather than trust stale evidence.
- Exclude ticket-only intake/confirmation commits from the repository-tree component; their substantive effects remain represented by this ticket and the actual sibling input. Do not implement a guessed fine-grained code dependency graph: any non-ticket tracked source change may conservatively invalidate approval.
- Reuse the existing Git wrapper and filesystem seams. Put identity and approval selection with requisition review; remove the ticket-SHA-only dispatch bypass and call the same reuse decision in CLI before constructing/preflighting the provider. Keep admission refusal precedence and provisional unmerged-dependency behavior.
- Record the identity on completed CLI, dispatch, Author and Rework verdicts, migrating all four existing requisition_verdict writers. Update the shared tests/approval.py fixture to emit valid matching identity through the production owner; update the Rework exact event-body assertion and the RequisitionVerdict equality fixture to carry the new provenance. Legacy records remain readable and cause a fresh review. Choose the latest verdict for the stem, never search past a newer snag/rma to resurrect an approval. Preserve the current real dependency gates and failure routing.
- Add fake-driven unit tests for new pure identity/selection logic and integration tests for both entry points, using zero-call assertions. Update the existing gate test whose legacy SHA-only approval previously bypassed review.
- Update the CLI review help text, affected host guide verb row and requisition documentation to explain conservative reuse and invalidation. Update extension help if its existing ticket-review description states the superseded behavior.
Scope out:
- No time-based approval expiry, new config flag, cache service, learned dependency tracker, speculative delta-review framework, or reuse of a changed ticket beyond confirmation state. Context packing is delivered by `requisition-review-compact-context`.

## Scope fence
- clutch/requisition.py
- clutch/runner.py
- clutch/__main__.py
- clutch/help.py
- clutch/author.py
- clutch/rework.py
- tests/approval.py
- tests/integration/test_rework.py
- tests/unit/test_requisition_panel.py
- tests/unit/test_requisition_input_identity.py
- tests/unit/test_review_reuse_cli.py
- tests/unit/test_review_reuse_dispatch.py
- tests/integration/test_requisition_reuse.py
- tests/integration/test_requisition_gate.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_requisition_input_identity.py tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py` proves a second identical review, its confirmation-only transition and dispatch reuse approval with zero extra preflight/model calls.
2. `./dev.py test tests/unit/test_requisition_input_identity.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py` proves changes to code, Context bytes, dependency/sibling material, coverage, specs, selected tier/model/panel or substantive ticket text invalidate approval; legacy and newer snag/rma records cannot authorize reuse.
3. `./dev.py test tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py` proves both verdict writers record the same canonical identity and preserve provisional/refusal behavior; unit tests reach changed IO composition with injected seams.

## Verification
```
./dev.py test tests/unit/test_requisition_input_identity.py tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py
```

## Definition of rejected
Removing required checks without evidence, introducing a second production authority, adding speculative settings, or changing files outside the fence.

## Time budget
- expected: 30m
- stuck: 60m
