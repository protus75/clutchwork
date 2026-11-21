---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Runs before
- requisition-review-approval-reuse
- requisition-review-compact-context

## Context
- clutch/requisition.py
- clutch/author.py::author
- clutch/rework.py::rework
- clutch/runner.py::drive
- clutch/__main__.py::_review
- clutch/providers.py::candidates
- clutch/providers.py::panel_members
- clutch/caps.py::capability
- clutch/git.py
- clutch/journal.py::Journal.append
- tests/approval.py
- tests/unit/test_requisition_panel.py
- tests/integration/test_rework.py
- tests/integration/test_review_command.py

## Goal / Why
Stop paying for a repeated buildability investigation when its substantive inputs have not changed. This first half records checked provenance: every completed requisition verdict carries one conservative, deterministic identity of the inputs it reviewed, composed by one owner and written by all four verdict writers through one wrapper. The follow-up `requisition-review-approval-reuse` then makes CLI review and dispatch reuse an approval only when that identity matches. This is orchestration class prevention: reuse evidence with checked provenance instead of suppressing required review.

## Boundary contract
### Requisition verdict journal body
- disposition: extend
- owner: clutch/requisition.py and the existing requisition_verdict signal
- consumers: CLI review, engine dispatch, Author and Rework writers, and the shared approval test fixture
- observable change: add `input_identity`, a lowercase 64-character SHA-256 hex digest, to RequisitionVerdict and every completed requisition_verdict signal; mechanical outcomes that cannot gather valid inputs, and reviews whose inputs changed during the call, record null; existing verdict metadata is retained and every writer uses the same composer
- compatibility: no new signal name, journal envelope version, hand-edited journal, database or authoritative side cache; old events without the field remain readable; the dispatch reuse decision is unchanged by this ticket
- acceptance: all four writers and the fixture record the same identity for the same inputs and tier
- tests: tests/unit/test_requisition_input_identity.py and tests/integration/test_requisition_identity_record.py
- post-merge source of truth: clutch/requisition.py and journaled requisition_verdict

## Scope in / Scope out
Scope in:
- Expose `clutch/requisition.py::input_identity(material: Mapping[str, object]) -> str` as a pure synchronous canonical composer: JSON-compatible material has sorted mapping keys, sequences retain semantic order, and source bytes are represented as hex strings before SHA-256 hashing. The exact material keys are ticket (state-normalized text), tree (sorted tracked non-ticket path/content pairs, with null content for deletions), context (selected path/content pairs), coverage (bytes or null), siblings (rendered text), review_spec, implement_spec, and route (tier plus ordered resolved provider/model candidates and panel policy).
- Expose `async review_input_identity(repo, text, ticket, config, git, specs_dir, coverage_map, history, *, tier: AgentTier) -> str | None` to gather these inputs through existing seams and call that pure composer; None means the inputs could not be established. Ignore only frontmatter state in the ticket component. Hash tracked non-ticket working-tree contents (including edits and deletions); use the Git wrapper only to establish tracked membership. Exclude ticket-only paths from the tree component; their substantive effects remain represented by the ticket and actual sibling input. Exclude prior verdict prose, invocation IDs, timestamps and retry feedback. Do not implement a fine-grained code dependency graph.
- Resolve ordered candidates and panel members with the existing clutch.providers.candidates and panel_members owners against the same config snapshot, including the selected route panel policy; do not reproduce that policy from driver internals.
- Add `RequisitionVerdict.input_identity: str | None = None`. Add `async review_with_identity(driver, *, git, config, history, **review_kwargs) -> RequisitionVerdict` in clutch/requisition.py as the shared four-caller wrapper: review_kwargs are the existing review_ticket keyword arguments unchanged. It gathers identity with the explicit review_kwargs tier, invokes the existing review_ticket, regathers identity and returns a model_copy carrying input_identity only when before and after identities are equal and non-null. The low-level review_ticket signature remains unchanged and its direct test callers get input_identity=None. Mechanical lint failures return their existing verdict without identity.
- Migrate all four production requisition_verdict writers to the wrapper and record `input_identity` in their signal body: CLI `_review` passes config.routing_default_tier, dispatch in runner.drive passes capability(ticket, history)[0], Author and Rework pass the same tier as their existing review_ticket call. Keep the existing dispatch ticket-SHA approval check unchanged in this ticket; only the writer changes.
- Update the shared synchronous tests/approval.py fixture to read journal history, derive the dispatch tier through capability(ticket, history), invoke the production async gatherer, and emit the matching identity in its approval body. It must also work when called inside an existing event loop, using a small test-only worker-thread bridge in that fixture rather than calling asyncio.run in the running loop or duplicating the identity algorithm.
- Update the Rework exact event-body assertion in tests/integration/test_rework.py and the RequisitionVerdict equality fixture in tests/unit/test_requisition_panel.py to carry the new field.
- Six test files patch `review_ticket` on `clutch.author`, plus `tests/integration/test_rework.py` on `clutch.rework`: `tests/integration/test_author.py` (line 215), `tests/unit/test_author.py` (143), `tests/unit/test_author_roadmap_row.py` (188), `tests/unit/test_author_stem_claimed.py` (52), `tests/unit/test_key_scope.py` (178), `tests/unit/test_ticket_write_consumers_author.py` (129), and `tests/integration/test_rework.py` (128, 175). After Author and Rework call `review_with_identity`, each patch targets the call the site now makes, and only the patched name changes; no unused `review_ticket` import stays in `clutch/author.py` or `clutch/rework.py` to keep an old patch resolving.
- Add fake-driven unit tests for the pure composer and the gatherer/wrapper with injected seams, and an integration test that the writers and fixture record matching identities.
Scope out:
- The reuse decision itself (latest-verdict selection, CLI skip before preflight, replacing the dispatch ticket-SHA bypass), test_ladder.py changes, CLI help and documentation: delivered by `requisition-review-approval-reuse`.
- No time-based expiry, new config flag, cache service, learned dependency tracker or delta-review framework. Context packing is delivered by `requisition-review-compact-context`.

## Scope fence
- clutch/requisition.py
- clutch/runner.py
- clutch/__main__.py
- clutch/author.py
- clutch/rework.py
- tests/approval.py
- tests/integration/test_rework.py
- tests/unit/test_requisition_panel.py
- tests/unit/test_requisition_input_identity.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_author.py
- tests/unit/test_author.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_author_stem_claimed.py
- tests/unit/test_key_scope.py
- tests/unit/test_ticket_write_consumers_author.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_requisition_input_identity.py` proves the pure composer is canonical (key order independent, sequence order significant, 64 lowercase hex), that frontmatter-state-only and ticket-only-path changes keep the identity, and that changes to tracked non-ticket working-tree bytes (including deletions), Context bytes, sibling material, coverage, review or Implement spec bytes, tier, resolved candidates or panel policy, or substantive ticket text change it.
2. `./dev.py test tests/unit/test_requisition_input_identity.py` proves with injected seams that review_with_identity returns the before identity when regathered inputs match, returns null when inputs change during the call or cannot be established, and returns null for mechanical lint failures.
3. `./dev.py test tests/integration/test_requisition_identity_record.py` proves the CLI, dispatch, Author and Rework writers record `input_identity` in their requisition_verdict body, that a CLI default-tier review and a dispatch review at an equal effective tier record the same identity, and that the synchronous tests/approval.py fixture records that same identity both outside and inside an active event loop.
4. `./dev.py test tests/integration/test_rework.py tests/unit/test_requisition_panel.py tests/integration/test_author.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_stem_claimed.py tests/unit/test_key_scope.py tests/unit/test_ticket_write_consumers_author.py` passes with the patch sites retargeted and the exact-body and equality fixtures carrying the new field.

## Verification
```
./dev.py test tests/unit/test_requisition_input_identity.py tests/integration/test_requisition_identity_record.py tests/integration/test_rework.py tests/unit/test_requisition_panel.py tests/integration/test_author.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_stem_claimed.py tests/unit/test_key_scope.py tests/unit/test_ticket_write_consumers_author.py tests/integration/test_requisition_gate.py tests/integration/test_review_command.py tests/integration/test_ladder.py
```

## Definition of rejected
Removing required checks without evidence, introducing a second identity composer or a production writer that bypasses review_with_identity, changing the dispatch reuse decision, adding speculative settings, or changing files outside the fence.

## Time budget
- expected: 30m
- stuck: 60m