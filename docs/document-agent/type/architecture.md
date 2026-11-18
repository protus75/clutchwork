---
facet: type/architecture
version: "0.1"
summary: Explain component ownership and trace how data, decisions, and effects cross boundaries.
aliases: []
applies_to: [create, derive]
requires: []
---

Write an architecture document that lets a maintainer locate a change and predict which consumers it affects. Use exact component and artifact names from the source. Label proposed components as proposed.

## System boundary and responsibilities

Identify the actors, the capability owned by the system, and the responsibilities owned elsewhere. For Clutch designs, distinguish engine process policy from host project content wherever the two meet. Identify the entry point for one representative operation.

## Components and contracts

Group components by the capabilities they own. For each material crossing identify the producer, consumer, contract, and production composition point. Describe inputs, results, failures, and compatibility to the extent needed to reason about that crossing. Name the durable definition of each shared rule or format. Show which existing seam a change reuses and which incident earns a new one. Avoid inventing layers from directory names.

## Execution, state, and recovery

Trace the representative operation in execution order. Identify the authoritative write, the reader, and any derived view. Where effects, locks, or retries matter, trace one interruption at a named point. Explain what survives, who can resume, and how that actor distinguishes pending from completed work. For Clutch, ground these claims in the owning files, journal, and effect records as applicable. Distinguish operational diagnostics from durable decisions.

## Decisions and verification

Record the constraint behind each significant design choice, the alternative it rules out, and the observation that would expose a violation. Include the production path and the test seam when supplied. Close with any ownership or recovery question that the sources leave unresolved. A reader should be able to trace both an ordinary call and its failure path from the document alone.
