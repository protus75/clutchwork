---
id: declined-box-000475-4d3dbe7a
kind: declined
link: box-000475-4d3dbe7a
reopen_after_days: 30
---
The note asks for one function, next to caps.capability, that decides the (tier, effort) pair for every model call. The engine call sites and watch would all use it, and SpecMeta.tier would either be honored or removed from the eight prompt specs. The goal is that no display or new surface can predict a different pair from the one the engine sends.

The harm this note cites is already fixed. The watch tier/effort mismatch it uses as evidence was the instance ticket watch-surface-tier-truth, which has merged. At HEAD, clutch/observe.py::capability no longer reads spec frontmatter tier for non-implement surfaces. It folds the ticket's agent_tier/agent_effort or the latest retry rung after the last operator keep, which is the same window as caps.lineage. It pairs requisition_review with that spec's effort, as requisition.review_ticket does. No surface today shows or uses a pair that differs from what the engine passes. What remains is structural: the rung fold is copied in observe.py, call sites choose their own pair, and SpecMeta.tier is a field nothing reads except retro. That is a refactor and dead-field cleanup with no reachable incorrect runtime behavior, so it fails the admission bar. Reopen if a display or engine surface is shown to report or send a (tier, effort) that differs from the pair the engine passes, for example observe.capability drifting from caps.lineage, or a new snapshot field that predicts a tier. Also reopen if a run is shown where an operator edit to a spec's tier: was expected to take effect and silently did not.

- tickets/watch-surface-tier-truth is in the merged set; its Scope out deferred the single-owner function and the SpecMeta.tier decision to this note
- clutch/observe.py:238-251 at HEAD: capability folds the ticket frontmatter or the retry rung after the last operator keep for every surface, and overrides only effort for requisition_review from clutch/specs/requisition_review.md
- clutch/caps.py:21-32 lineage and :77-84 capability use the same last-operator-keep window and the same retry-rung selection as observe.capability
- tickets/watch-surface-tier-truth/evidence/watch-tier-mismatch.txt shows the mismatch at pre-fix HEAD 34b1dd36, where observe.capability returned spec tier/effort for non-implement surfaces; that branch is gone
- clutch/specs/*.md all declare tier:, but only clutch/retro.py:457 reads spec.meta.tier; the field has no effect anywhere else, and no incident is cited

Message: box-000475-4d3dbe7a
