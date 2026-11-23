---
id: declined-box-001145-0983ceb4
kind: declined
link: box-001145-0983ceb4
reopen_after_days: 30
---
After implement-context-unresolved-selector-notice merged, Implement shows a notice when a `## Context` selector does not resolve, but ticket lint still refuses it. The sentence in docs/how-clutch-works.md saying lint renders each Context entry exactly as Implement does is therefore slightly out of date for unresolved selectors.

This is only a mismatch between documentation wording and the code. The code behaves correctly: lint stays the stricter gate, and Implement's notice is the behavior the merged ticket intended. The report names no run that went wrong because of the sentence, so there is no harmful runtime behavior to repair. Records 000403, 000998 and 001007 declined the same kind of stale-sentence note about docs/how-clutch-works.md. Reopen if an author or agent relies on this sentence and writes a ticket or diff that fails lint or Check, or once a docs-truth sweep is in scope that can take the one-line correction.

- message class suggestion, origin implement-context-unresolved-selector-notice, outcome ok, proposed_paths empty
- implement-context-unresolved-selector-notice is in the merged set
- declined-box-000403-d925564b, declined-box-000998-620886e1 and declined-box-001007-c547823e declined similar stale-sentence reports about docs/how-clutch-works.md
- neighbors index unavailable (index_unreadable); not used as grounds

Message: box-001145-0983ceb4
