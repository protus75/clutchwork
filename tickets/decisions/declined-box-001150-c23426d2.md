---
id: declined-box-001150-c23426d2
kind: declined
link: box-001150-c23426d2
reopen_after_days: 30
---
A session proposes an authoring rule that ticket drafts must never tell the requisition reviewer to grep the repository or read HEAD. The trigger is three drafts rejected on that premise: requisition-review-collection-policy, requisition-review-exact-edit-doc-limit and requisition-review-decomposed-string-closure. The requisition review spec tells the reviewer to judge only the supplied ticket and Context and not to search the repository.

The reviewer did what its spec says. clutch/specs/requisition_review.md line 16 forbids searching the repository, so a draft that asks for a search is an authoring defect that review already catches and its author can fix. No engine or runtime behavior is wrong. The request is extra authoring guidance or a lint rule, and recent session proposals of the same kind (declined-box-001148-cee5d96b, which would refuse Scope-in text that searches at run time, and declined-box-001149-463dd139) were declined on the same grounds. The cost here was three draft rejections caught at authoring. No run spent caps and no ticket merged wrong. One related point is worth noting: line 18 of the same spec still says to check stated preconditions 'against HEAD', which sits awkwardly with the no-search rule on line 16. Reopen if: (a) Author-stage or roadmap-driven drafts keep making this mistake after the authoring guide is re-read, and it costs dispatched runs or caps rather than chat-time review rounds; or (b) the HEAD-precondition wording on line 18 causes a reviewer to give contradictory verdicts on the same ticket.

- clutch/specs/requisition_review.md:16 says to judge only the supplied ticket and Context and not to search the repository for callers, importers, tests, siblings or dependents.
- clutch/specs/requisition_review.md:18 says to check every stated repo-state precondition against HEAD. This is a possible wording tension with line 16 but is not shown to cause wrong verdicts.
- The three named drafts were rejected at authoring and review time. The message reports no dispatched run, spent cap, or wrong merge.
- Precedent: declined-box-001148-cee5d96b and declined-box-001149-463dd139 declined similar session-proposed authoring and lint rules that each came from a single requisition-review parking.
- The neighbors index was unavailable (index_unreadable), so it gives no evidence either way.

Message: box-001150-c23426d2
