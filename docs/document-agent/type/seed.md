---
facet: type/seed
version: "0.1"
summary: Translate settled plan decisions into evidence a ticket author can use.
aliases: []
applies_to: [create, derive]
requires: []
---
<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: seed
relates: []
owner: engine
verified: d7719818
hash: 417cc847e7266b4dab221b0e9e9f427b78bd83cf16d76070032a8dfbab814125
-->

Write a seed for the person or agent who will author tickets. Work from the canonical plan and supplied repository evidence. A proposed decomposition from an Automatable review is input only when the owner has accepted it. The deliverable is a Markdown seed.

## Origin and delivery scope

Identify the canonical plan sections, selected phase, entry conditions, and exit evidence. State which refusals and owner decisions constrain all work in this seed. Keep existing identifiers so a downstream author can trace a change back to the plan.

## Proposed work

For each ticket-sized outcome, give the proposed stem, goal, owning plan section, and artifact the work delivers. Identify existing files or symbols the author needs as context and the paths the change forces into its write fence. Include callers, importers, readers, tests, and documentation that pin the changed behavior. Mark a path as proposed when it does not exist. Flag unverified ownership or consumer closure for investigation.

Describe each material boundary through its canonical owner, consumer, observable change, and compatibility. Identify the implementation and verification seams already available. Assign each new or preserved guarantee an acceptance observation, the wrong result it rules out, and a check supported by the supplied project material. For Clutch itself, express test verification through `./dev.py test`. For a reported bug, identify the actual evidence and the case that distinguishes the base from the fix.

## Ordering and phase exit

For each hard dependency, name the merged artifact its consumer requires. Put scheduling preferences under priority or runs-before. Trace the phase exit to the proposed work that produces its evidence. If an exit depends on a human choice, identify the decision and who can make it.

## Authoring gaps

Record missing evidence, unresolved contract changes, likely fence collisions, and criteria with no observable check against the affected work item. Hand the seed to the normal authoring process. The host authoring guide owns ticket content and the ticket skeleton owns its grammar. Keep the seed usable as input to that process without emitting ticket files.
