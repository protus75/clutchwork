---
facet: type/api
version: "0.1"
summary: Describe the boundaries a consumer relies on and the behavior each owner guarantees.
aliases: []
applies_to: [create, derive]
requires: []
---
<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: api
relates: []
owner: engine
verified: d7719818
hash: fdda281a49b6e05c9ca4533fc3e14b970efaadd4ec8b14c088e6ede80411a9e1
-->

Write an API reference from the supplied material. A reader implementing the producer and a reader implementing a consumer must be able to work independently from this document and agree on the observable result.

## Scope and implementation phases

Name the capability, its consumers, and the boundaries in scope. A boundary can be a callable, command, callback, process, stored record, configuration value, or user workflow. Include an internal boundary when its producer and consumer can change independently. Leave private implementation choices with their owner.

Preserve the source’s phase names. For each phase, identify its deliverables and link to the boundary headings needed to implement them. For an existing API with no delivery phases, use “Current API” as a single review scope. This gives Buildability a named scope without inventing a delivery sequence.

## Boundary contract

Give each boundary a heading using its exact symbol, command, field, format, or workflow name. Start with its canonical owner and a representative consumer. Explain what the consumer relies on. Name the code, schema, command help, or maintained document that owns the contract after delivery. Include the contract facts here so an isolated reader can use them without opening the owner.

For a proposed change, use the project’s dispositions: reuse, extend, replace, create, or none. For an existing API reference, describe the current contract directly. Do not invent a change history to fill a disposition field.

- For reuse, identify the existing owner and show how the consumer uses it.
- For extend or replace, state the old and new observable behavior. Account for every known affected consumer. For a breaking change, identify what migrates each consumer, the ordering, and when the old form disappears.
- For create, name the closest existing owners, the concrete requirement each cannot meet, and the evidence that earns a new boundary. If the supplied material establishes none of that, record the decision as open.
- For none, give the reason and a concise preservation claim. State what a consumer can continue to rely on.

Describe inputs, outputs, failures, side effects, invariants, and compatibility where they affect a consumer. Include ordering, persistence, atomicity, retries, and production or test wiring when they change how the boundary can be used or verified. Define shared shapes and closed values once. Use the same names in signatures, examples, and consumer descriptions.

## Contract examples and verification

For each new or changed observable guarantee, give a concrete starting state, an invocation or event, and the expected observation at the consumer. Name the plausible wrong implementation the observation would catch. Cover a preserved guarantee when the change puts it at risk.

Where the source supplies an acceptance criterion or contract test, identify it. Where verification is still proposed, describe the distinguishing observation. Never present a proposed check as an existing test.

## Open decisions

Place each unresolved question under the boundary heading where an implementer would look for the answer, and collect links here. State what is missing, ambiguous, or contradictory and what difference it makes to the caller or reader. Record deliberate implementation freedom only when the source delegates the choice and specifies the guarantee that survives it.

Before returning the reference, select one phase. Sketch the producer signature or record and one real consumer’s call or read. Trace a success and a material failure or edge case. If either side needs a fact you supplied from habit, recover it from the source or record the open decision. Return the reference; the independent Buildability panel produces the ledger and verdict.
