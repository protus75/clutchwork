---
id: declined-box-001157-4d6a9f8b
kind: declined
link: box-001157-4d6a9f8b
reopen_after_days: 30
---
The ticket-lint-refuses-meta-verbs Implement run ended ok. It noted that the planning document docs/antigravity-plan.md lists `meta check` among the commands a ticket's Verification may run. The new lint rule now refuses that. The file was outside the ticket's scope fence, so the run left it unchanged.

This is a wording mismatch in a forward-looking planning document. It names no wrong runtime behavior. Ticket lint enforces the rule whatever the plan says. A ticket author who copied the plan's example would get a lint refusal with a paved road, not a bad run. Earlier records already declined stale plan-document wording left behind by merged changes, for example 001154, which covered the same file, and 001130. Reopen within 30 days if a ticket authored from docs/antigravity-plan.md loses a run or a review cycle because it follows that wording.

- ticket-lint-refuses-meta-verbs is in the merged set, so lint already refuses meta verbs in Verification
- message outcome is ok; no failed run, no lost attempt cited
- declined-box-001154-a6e797fc declined stale wording in the same docs/antigravity-plan.md as plan-only drift
- neighbors index unavailable; no open ticket covers this

Message: box-001157-4d6a9f8b
