---
facet: type/ai-rule
version: "0.1"
summary: Concise, always-loaded behavioral rules for AI agents within a strict context budget.
aliases: [rules]
applies_to: [create, derive]
requires: []
---

Produce an always-loaded AI rule file (such as `CLAUDE.md`, `AGENTS.md`, or a nested rule file) for coding agents. Keep the file lean, high-signal, and strictly separated from specification or contract prose.

## Document class and budget

Annotate the file as an AI rule (`kind: rule`), never as a Spec/Contract (`kind: spec`). Do not mix schemas, wire contracts, or RFC 2119 specification prose into an AI rule file; move those to a Spec/Contract document and link to them if needed.

Keep a root AI rule file under **200 lines** and **8 KB (8,192 bytes)**. Every line enters every session context and must prevent a concrete failure.

## Obligation voice and flag discipline

Write rules in short, imperative sentences. Reserve explicit binary flags (`MUST`, `NEVER`, or `HARD:`) for top-extreme invariants only; overusing flags flattens compliance across the entire file. Leave routine conventions and defaults unflagged.

Avoid bare `SHOULD` without an explicit override condition (*"Prefer X; use Y when Z"*). Omit `MAY` unless it carves out an explicit exception to a nearby prohibition.

## What to compress, drop, or relocate

- **Gate-covered rules:** When a test, linter, hook, or engine gate enforces a rule, compress it to one line naming the gate or drop it.
- **Discoverable facts:** Omit architecture summaries, directory layouts, or conventions an agent can read directly from code or from the Annotation system (`clutch:meta` headers -- `kind`, `purpose`, `relates`, `owner` -- and `clutch context suggest`).
- **Subsystem-only rules:** Move high-detail rules that apply only to one directory or task type into a nested rule file, path-scoped rule, skill, or lazy pointer-on-demand (*"Before editing X, read Y"*). Never rely on eager `@import` to save context.
- **Cross-file parity:** Keep `CLAUDE.md` and `AGENTS.md` aligned and as near-identical as possible, differing only where provider mechanics or provider-specific keywords require it.
- **Protected regions:** Preserve extraction-marker blocks (such as `<!-- clutch:core begin -->` / `<!-- clutch:core end -->`) byte for byte; route changes inside them to their owning template.

Independent rule review ([RuleReview.md](../review/RuleReview.md)) owns the audit of budget, `0.0`--`1.0` force ranking, gate redundancy, discoverability, peer alignment, and scoping.
