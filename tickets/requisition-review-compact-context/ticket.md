---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- requisition-review-input-reuse

## Context
- clutch/requisition.py
- clutch/stages.py::implement_inputs
- clutch/tickets.py::render_context
- tests/integration/test_requisition.py
- tests/unit/test_requisition_panel.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- docs/document-agent/review/CompressionReview.md
- docs/how-clutch-works.md#3. Tickets

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
Reduce requisition review input without paying another model to compress it. The current prompt embeds the ticket once directly and again inside the complete Implement prompt, including execution instructions for a role the reviewer does not perform. Borrow only the simple lossless aspects of compression review: deduplicate exact content, preserve normative requirements and protected bytes, and measure before/after size. Keep buildability checks and the implementation-render feasibility gate; do not infer that interface contracts alone make full review unnecessary. Review depth is an owner decision implemented by `requisition-contract-review-comparison`; no comparison study is required.

## Boundary contract
### Requisition prompt material
- disposition: extend
- owner: clutch/requisition.py and clutch/specs/requisition_review.md
- consumers: requisition reviewer and evaluation fixtures
- observable change: send one exact authored ticket and one exact selected Context block with existing dependent, sibling and prior-review material; omit duplicated ticket and Implement-only instruction prose
- compatibility: RequisitionReply schema, dependent accounting, tool permissions and Implement rendering/headroom remain unchanged; no semantic source summarization or auxiliary model call
- acceptance: representative fixture has exactly one ticket copy, preserves protected bytes and normative fields, and is shorter than the old full-Implement wrapper
- tests: tests/unit/test_requisition_context_pack.py and tests/integration/test_requisition_context_pack.py
- post-merge source of truth: clutch/requisition.py and clutch/specs/requisition_review.md

## Scope in / Scope out
Scope in:
- Keep _base_render as the unchanged production Implement render for feasibility measurement and existing callers; stop embedding that full render in the reviewer prompt. Reuse implement_inputs to obtain the actual ticket-selected Context bytes without introducing a second Context selector or a summarization agent.
- Replace the reviewer template render slot with a context slot and update its input description. Include the exact authored ticket once and selected Context once, preserving the existing data-block delimiter escaping (byte-identity assertions compare material before that established quoting transform); do not rewrite, truncate or summarize source/code/contracts, change commands, weaken obligations, resolve ambiguity, or discard distinct sibling/dependent/prior-review evidence. No compressor or fidelity subagents are launched.
- Preserve full Implement render_chars and existing headroom/mechanical refusal semantics. The deterministic review pack is for reviewer input, not an alternate Implement prompt. Recompute the reuse identity from the actual review inputs using the dependency ticket's canonical owner so changed packing/spec inputs invalidate old approvals.
- Bump the requisition_review prompt version to the next minor above main. Update its existing input-shape assertion and both version pins; adjust the existing review-render-over-bound fixture to exceed the new reviewer pack bound rather than relying on the old duplicated wrapper; add new unit tests with injected material and integration tests with Path(__file__) anchored shipped specs, including protected commands/code and contradictory contracts that must both survive.
- Migrate the hand-built ticket stand-ins reaching the new Context read in tests/unit/test_requisition_panel.py, test_requisition_dependents.py, test_requisition_sibling_tickets.py, test_requisition_stage_events.py and test_key_scope.py: give them context=() or inject the existing implement_inputs seam with explicit fake Context bytes. Preserve their panel, dependent, sibling, event and effect-key assertions; add no getattr fallback or new production compatibility path.
- Update requisition documentation with exactly what is omitted, what remains verbatim and the before/after character measurement. New unit tests exercise new Python statements using fake inputs rather than repository reads.
Scope out:
- No changes to review verdict schema, review rigor, tool permissions, Context authoring rules, document-agent compression pipeline, Implement prompt, or provider pricing.


## Scope fence
- clutch/requisition.py
- clutch/specs/requisition_review.md
- tests/unit/test_requisition_context_pack.py
- tests/integration/test_requisition_context_pack.py
- tests/integration/test_requisition.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- docs/how-clutch-works.md

- tests/unit/test_requisition_panel.py
- tests/unit/test_requisition_dependents.py
- tests/unit/test_requisition_sibling_tickets.py
- tests/unit/test_requisition_stage_events.py
- tests/unit/test_key_scope.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_requisition_context_pack.py tests/integration/test_requisition_context_pack.py tests/integration/test_requisition.py` proves ticket/Context appear once, protected source bytes survive exactly before existing delimiter escaping, divergent requirements remain unreconciled and a representative pack is strictly smaller than the former full-Implement wrapper without an extra LLM call.
2. `./dev.py test tests/integration/test_requisition.py tests/unit/test_requisition_context_pack.py tests/integration/test_requisition_context_pack.py` proves Implement render/headroom behavior is preserved and modified Context/spec material invalidates reuse through the shared identity.
3. `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/unit/test_requisition_panel.py` passes after migrating the changed prompt-input shape and version pins, retaining verdict/dependent contracts.

## Verification
```
./dev.py test tests/unit/test_requisition_context_pack.py tests/integration/test_requisition_context_pack.py tests/integration/test_requisition.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/unit/test_requisition_panel.py tests/unit/test_requisition_dependents.py tests/unit/test_requisition_sibling_tickets.py tests/unit/test_requisition_stage_events.py tests/unit/test_key_scope.py
```

## Definition of rejected
Removing required checks without evidence, introducing a second production authority, adding speculative settings, or changing files outside the fence.

## Time budget
- expected: 22m
- stuck: 44m
