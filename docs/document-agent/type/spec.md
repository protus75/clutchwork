---
facet: type/spec
version: "0.1"
summary: Express the source requirements precisely while preserving their force and protected material.
aliases: []
applies_to: [create, derive]
requires: []
---
<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: spec
relates: []
owner: engine
verified: d7719818
hash: bb951deeb5ff2b939467bb0a47c057d6c09aa3f8eb1d7df63aaf8b2b4bd16787
-->

Produce specification-form Markdown for an implementer. Annotate the document as a Spec/Contract (`kind: spec`) and never mix always-loaded AI behavioral rules into it. Choose the structure according to the operation.

## Obligation keywords

Use RFC 2119 keywords (`MUST`, `MUST NOT`, `SHOULD`, `MAY`) consistently so implementers and fidelity auditors have an unambiguous obligation scale:
- `MUST` / `MUST NOT` for required invariants, contracts, and refusals.
- `SHOULD` only with its override condition (when deviation is permitted and what it requires).
- `MAY` for explicitly permitted behavior or optional extensions.

Do not invent obligation force where the source is silent or contradictory: leave ambiguous passages unresolved and surface missing or conflicting `MUST`/`SHOULD`/`MAY` qualifications for owner resolution.

## Create from supplied requirements

For a new specification, order the content by scope and terms, observable contracts, failure and recovery behavior, then verification and open requirements. State who must do what, under which conditions, and what a consumer can observe. Carry supplied names, units, limits, defaults, ordering, compatibility, and refusal conditions into the owning section. Include a counterexample or check when the source provides it. Record a material ambiguity with the passages that cause it.

## Derive from a canonical document

Use the canonical document's exact section numbers, headings, order, and internal references. These existing sections are the output structure. Work through the source in order and account for every obligation, exception, refusal, and invariant. Preserve the distinction between required, recommended, and permitted behavior.

Copy fenced blocks, commands, paths, configuration examples, schemas, and extraction-marker regions including their delimiters byte for byte. Retain a concise reason where a rejected alternative or failure explains a decision. Collapse identical normative statements only when the reference to their owning section preserves every condition. Keep differing versions verbatim and surface the discrepancy for review.

Check from source to draft for dropped, altered, or invented requirements, silently resolved ambiguities, verbatim violations, and broken references. Leave an uncertain passage intact. Return the draft and the derivation provenance requested by the surface. Independent compression and fidelity review own the audit and verdict. Promotion requires LOSSLESS and a human-reviewed diff.
