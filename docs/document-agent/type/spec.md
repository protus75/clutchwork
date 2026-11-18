---
facet: type/spec
version: "0.1"
summary: Express the source requirements precisely while preserving their force and protected material.
aliases: []
applies_to: [create, derive]
requires: []
---

Produce specification-form Markdown for an implementer. Choose the structure according to the operation.

## Create from supplied requirements

For a new specification, order the content by scope and terms, observable contracts, failure and recovery behavior, then verification and open requirements. State who must do what, under which conditions, and what a consumer can observe. Carry supplied names, units, limits, defaults, ordering, compatibility, and refusal conditions into the owning section. Include a counterexample or check when the source provides it. Record a material ambiguity with the passages that cause it.

## Derive from a canonical document

Use the canonical document's exact section numbers, headings, order, and internal references. These existing sections are the output structure. Work through the source in order and account for every obligation, exception, refusal, and invariant. Preserve the distinction between required, recommended, and permitted behavior.

Copy fenced blocks, commands, paths, configuration examples, schemas, and extraction-marker regions including their delimiters byte for byte. Retain a concise reason where a rejected alternative or failure explains a decision. Collapse identical normative statements only when the reference to their owning section preserves every condition. Keep differing versions verbatim and surface the discrepancy for review.

Check from source to draft for dropped, altered, or invented requirements, silently resolved ambiguities, verbatim violations, and broken references. Leave an uncertain passage intact. Return the draft and the derivation provenance requested by the surface. Independent compression and fidelity review own the audit and verdict. Promotion requires LOSSLESS and a human-reviewed diff.
