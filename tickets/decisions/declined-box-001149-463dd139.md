---
id: declined-box-001149-463dd139
kind: declined
link: box-001149-463dd139
reopen_after_days: 30
---
The session proposes a new authoring-guide or ticket-lint rule. A ticket that deletes a test assertion would also have to say that it removes any import the deletion leaves unused. The trigger was requisition review parking implement-spec-version-single-pin over a `load_spec` import that the removed assertion would have left unused.

This is preventive authoring hardening, not a current runtime gap. In the one cited case, requisition review caught the defect before Implement ran, which is the review working as designed. That ticket has since merged, so nothing is still blocked. The note cites no run where an unused import got past review, failed Check, or used up caps. A leftover unused import is also a lint or autofix matter that the host ruff checks already cover at Check. The registry has already declined several similar one-incident requests for authoring-guide or lint rules (for example 001054, 001094 and 001148). Reopen if two or more tickets lose an Implement or Check attempt, or end premise_failed, because an import left unused by a removed test assertion was neither fenced nor named.

- implement-spec-version-single-pin is in the merged set, so the triggering ticket is no longer blocked
- requisition review caught the defect at authoring time, before any Implement attempt or cap was spent
- declined-box-001148-cee5d96b, declined-box-001054-f24123a4 and declined-box-001094-9d305e08 declined similar single-incident authoring or lint rule proposals

Message: box-001149-463dd139
