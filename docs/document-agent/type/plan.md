---
facet: type/plan
version: "0.1"
summary: Turn a proposed change into a design with observable goals, decisions, and phase exits.
aliases: []
applies_to: [create, derive]
requires: []
---

Write the canonical plan so an owner can decide whether to build it and an implementer can take on one named phase. Keep headings stable as the plan evolves. When deriving from an existing document, carry forward decisions at their original strength.

## Goals and measure of success

Identify whose problem prompted the work, the observed cost, and what outcome would justify the change. State the optimization metric, its direction, and how it can be observed. Preserve any stated baseline and target. If no metric was supplied, make that an open decision. A Cut reviewer needs the owner's measure to judge whether a feature earns its place.

## Current state and scope

Describe what works today using the supplied owning artifacts. Separate observed failures from predictions. Name the smallest deliverable that serves the goal. Keep an explicit refusals list with the reason for each cut and any agreed condition for reconsidering it.

## Design and boundaries

Walk one representative case through the proposed system. For each material boundary, name the owner, consumers, observable behavior, and what changes. Explain the nearest reuse candidate when proposing a new owner. State the failure scenario that would defeat the design and the evidence that supports or challenges the premise. Carry forward decided tradeoffs and unresolved contradictions.

## Implementation phases

Give each phase a stable name a Buildability reviewer can select. State its entry conditions, deliverables, affected contracts, and observable exit. Identify what produces the exit evidence. Where a phase places work on hold, identify the available release path and its owner.

## Ticket breakdown

Give each proposed unit one outcome and a check that distinguishes success from a plausible wrong result. Show which units require another unit's merged artifact and which merely benefit from running earlier. Identify manual decisions and missing oracles so the Automatable review can examine them.

## Open decisions

For each unresolved choice, name the owning section, the decision needed, and what it blocks. In guided drafting ask about one material gap at a time. In headless drafting preserve it here. Review findings become proposed edits for the owner.
