---
id: declined-box-000955-917a40bc
kind: declined
link: box-000955-917a40bc
reopen_after_days: 30
---
The note says requisition review failed a sound ticket, merge-dirty-checkout-never-blocks, on 2026-11-21 with 'extra dependent' errors. The Sonnet reviewer had listed every test that touches the fenced module, and a validator in clutch/requisition.py required that list to match the engine's expected dependent set exactly. Four calls failed and the ticket was parked premise_failed. The note asks for the validator to accept extra fenced or read-only dependents, or for the prompt to say to list none when there are no coverage dependents.

Current main no longer has this behaviour. clutch/requisition.py has no `dependent_errors` validator and no exact-match check. The only mention of dependents there is the `dependents: list[Dependent]` field, which defaults to an empty list, and no code produces an 'extra dependent' error. The current requisition review spec (clutch/specs/requisition_review.md, version 3.28) tells the reviewer `dependents` is always `[]`. It also says not to search the repository for callers, importers, tests, siblings or dependents. That is the prompt change the note asks for. merge-dirty-checkout-never-blocks is also in the merged set, so the blocked ticket has landed. No current failure is left to repair. Reopen if a requisition review again fails or parks a ticket because of a mismatch in the reviewer's dependents list.

- Searching clutch/ for 'dependent_errors', 'extra dependent' and 'missing dependent' finds nothing
- clutch/requisition.py:44 `dependents: list[Dependent] = Field(default_factory=list)` is the only reference to dependents in that file
- clutch/specs/requisition_review.md:75 says "`dependents` is always `[]`."
- clutch/specs/requisition_review.md:16 tells the reviewer not to search the repository for callers, importers, tests, siblings or dependents
- merge-dirty-checkout-never-blocks is in the merged stems list

Message: box-000955-917a40bc
