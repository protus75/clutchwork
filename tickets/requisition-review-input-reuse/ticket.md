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
- consumers: CLI review, engine dispatch, Author and Rework writers, the shared approval test fixture, and the approval reader
- observable change: add `input_identity`, a lowercase 64-character SHA-256 hex digest, to RequisitionVerdict and every completed requisition_verdict signal; mechanical outcomes that cannot gather valid inputs use null and cannot authorize reuse; retain existing verdict metadata and use the same composer for every writer
- compatibility: no new signal name, journal envelope version, hand-edited journal, database or authoritative side cache
- acceptance: a later non-approval supersedes an older approval; unknown or missing identity causes a fresh review
- tests: tests/unit/test_requisition_input_identity.py and tests/integration/test_requisition_reuse.py
- post-merge source of truth: clutch/requisition.py and journaled requisition_verdict

## Scope in / Scope out
Scope in:
- Expose `clutch/requisition.py::input_identity(material: Mapping[str, object]) -> str` as a pure synchronous canonical composer: JSON-compatible material has sorted mapping keys, sequences retain semantic order, and source bytes are represented as hex strings before SHA-256 hashing. The exact material keys are ticket (state-normalized text), tree (sorted tracked non-ticket path/content pairs, with null content for deletions), context (selected path/content pairs), coverage (bytes or null), siblings (rendered text), review_spec, implement_spec, and route (tier plus ordered resolved provider/model candidates and panel policy). Expose `async review_input_identity(repo, text, ticket, config, git, specs_dir, coverage_map, history, *, tier: AgentTier) -> str | None` to gather these inputs through existing seams and call that pure composer; None means fresh review is required. Capture identity before a review and record it only if gathering the inputs again after the call produces the same identity, otherwise return the verdict without reusable provenance.
- The CLI passes config.routing_default_tier; dispatch passes capability(ticket, history)[0]; Author and Rework pass the same tier as their existing review_ticket call. Resolve ordered candidates and panel members with the existing clutch.providers.candidates and panel_members owners against the same config snapshot, including the selected route panel policy; do not reproduce that policy from driver internals. The tests/approval.py fixture reads journal history and derives dispatch tier through capability(ticket, history). Equal default and effective tiers must yield equal CLI/dispatch identities; different effective reviewer tiers intentionally invalidate reuse.
- Add `async review_with_identity(driver, *, git, config, history, **review_kwargs) -> RequisitionVerdict` in clutch/requisition.py as the shared four-caller wrapper: review_kwargs are the existing review_ticket keyword arguments unchanged. It gathers identity with the explicit review_kwargs tier, invokes the existing review_ticket, rechecks identity and returns a model_copy carrying input_identity only on stable before/after material. The low-level review_ticket signature remains unchanged and its direct test callers return input_identity=None by default; every production caller migrates to the wrapper, so there is no production SHA-only or unprovenanced approval path. Mechanical lint failures return their existing verdict without reusable identity.
- Compose one conservative deterministic identity from canonical ticket content (ignore only frontmatter state), current tracked non-ticket repository tree content, actual selected Context bytes, coverage-map content, overlapping sibling material, full reviewer and Implement spec bytes, and resolved reviewer tier/candidate/panel identity. Exclude prior verdict prose, invocation IDs, timestamps and retry feedback from semantic identity. Hash tracked non-ticket working-tree contents (including edits and deletions), rather than refusing reuse merely because they differ from HEAD; use the Git wrapper only to establish tracked membership. If any required input cannot be established, perform a fresh review rather than trust stale evidence.
- Exclude ticket-only intake/confirmation commits from the repository-tree component; their substantive effects remain represented by this ticket and the actual sibling input. Do not implement a guessed fine-grained code dependency graph: any non-ticket tracked source change may conservatively invalidate approval.
- Reuse the existing Git wrapper and filesystem seams. Put identity and approval selection with requisition review; remove the ticket-SHA-only dispatch bypass and call the same reuse decision in CLI before constructing/preflighting the provider. Keep admission refusal precedence and provisional unmerged-dependency behavior.
- Record the identity on completed CLI, dispatch, Author and Rework verdicts, migrating all four existing requisition_verdict writers. Update the shared synchronous tests/approval.py fixture to invoke the production async gatherer and emit matching identity through the pure composer; it must also work when called inside an existing event loop, using a small test-only worker-thread bridge in that fixture rather than calling asyncio.run in the running loop or duplicating the identity algorithm; update the Rework exact event-body assertion and the RequisitionVerdict equality fixture to carry the new provenance. Legacy records remain readable and cause a fresh review. Choose the latest verdict for the stem, never search past a newer snag/rma to resurrect an approval. Preserve the current real dependency gates and failure routing.
- Add fake-driven unit tests for new pure identity/selection logic and integration tests for both entry points, using zero-call assertions. Update the existing gate test whose legacy SHA-only approval previously bypassed review. In tests/integration/test_ladder.py, insert a fresh requisition approve response in every script at a changed effective reviewer tier, including retry-wall and operator-confirm reset cases; reviewer-tier escalation intentionally invalidates prior approval even when ticket text is unchanged. Preserve the Implement ladder assertions.
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
- tests/integration/test_ladder.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_requisition_input_identity.py tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py` proves a second identical review, its confirmation-only transition and dispatch reuse approval with zero extra preflight/model calls.
2. `./dev.py test tests/unit/test_requisition_input_identity.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py` proves changes to code, Context bytes, dependency/sibling material, coverage, specs, selected tier/model/panel or substantive ticket text invalidate approval; legacy and newer snag/rma records cannot authorize reuse.
3. `./dev.py test tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py` proves both verdict writers record the same canonical identity and preserve provisional/refusal behavior; unit tests reach changed IO composition with injected seams.

4. `./dev.py test tests/integration/test_ladder.py tests/integration/test_requisition_reuse.py` proves a named CLI/default-tier versus dispatch/effective-tier equality case matches when their tiers match, reviewer-tier changes force one new review, tracked working-tree edits can be approved and reused until their bytes change, and the synchronous fixture produces matching provenance when called inside an active event loop.

## Verification
```
./dev.py test tests/unit/test_requisition_input_identity.py tests/unit/test_review_reuse_cli.py tests/unit/test_review_reuse_dispatch.py tests/integration/test_requisition_reuse.py tests/integration/test_requisition_gate.py tests/integration/test_ladder.py tests/integration/test_rework.py tests/unit/test_requisition_panel.py
```

## Definition of rejected
Removing required checks without evidence, introducing a second production authority, adding speculative settings, or changing files outside the fence.

## Time budget
- expected: 30m
- stuck: 60m
