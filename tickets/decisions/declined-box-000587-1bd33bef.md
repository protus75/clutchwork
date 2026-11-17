---
id: declined-box-000587-1bd33bef
kind: declined
link: box-000587-1bd33bef
reopen_after_days: 7
---
This is a planned follow-up to the open tickets plan-drain-prompts and roadmap-accept. Once both merge, step 6 'Closing each phase' of clutch/specs/ask/plan-ticket-drain.md should name `clutch roadmap accept <release>`, and the prompt-content test should require that name. Until then the kickoff prompt describes the phase-closing review without naming the verb.

The gap cannot happen yet. Both preconditions are still open tickets: plan-drain-prompts has not added clutch/specs/ask/plan-ticket-drain.md, and roadmap-accept has not built the `clutch roadmap accept` verb. Naming that verb now would break the prompt rule that only existing verbs may be named (test_prompts_name_only_existing_verbs). plan-drain-prompts leaves the verb out on purpose and points to this message as the follow-up. With nothing to fix on the current code, this is speculative and is declined for now. Reopen when both plan-drain-prompts and roadmap-accept have merged and the plan-ticket-drain prompt still describes the phase-closing acceptance review without naming `clutch roadmap accept`.

- tickets/plan-drain-prompts/ticket.md:93 step 6 'Closing each phase' describes the review without a verb
- tickets/plan-drain-prompts/ticket.md:163 leaves `clutch roadmap accept` out on purpose because roadmap-accept has not merged at its base, and says a follow-up box message will name the verb
- tickets/plan-drain-prompts/ticket.md:169 test_prompts_name_only_existing_verbs requires that no prompt names `roadmap accept` yet
- plan-drain-prompts, roadmap-accept and release-acceptance-review are all in the open-tickets list and none is in the merged set

Message: box-000587-1bd33bef
