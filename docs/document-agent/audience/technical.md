---
facet: audience/technical
version: "0.1"
summary: Explain mechanisms and tradeoffs to a technically fluent reader.
aliases: []
applies_to: [create, derive]
requires: []
---
<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: technical
relates: []
owner: engine
verified: d7719818
hash: fbdc8dfceec67ad9a3e24fe925438ec75ef882c967bfbb74df43e73783fcd65c
-->

Assume familiarity with interfaces, state, and failure handling. Introduce project-specific terms at first use. Start from the property the reader needs to understand, then trace the shortest path from input to observable result. Identify the owner of the state and the condition that makes the result trustworthy.

Explain one failure or tradeoff that changes the conclusion. For example, when describing a status view, distinguish the event that records a transition from the projection that displays it. Include implementation details when they explain a guarantee, cost, or limit. Keep exact identifiers available for follow-up.
