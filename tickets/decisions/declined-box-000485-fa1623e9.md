---
id: declined-box-000485-fa1623e9
kind: declined
link: box-000485-fa1623e9
reopen_after_days: 30
---
Three rules in section A of CLAUDE.md and AGENTS.md repeat Engine conduct rules from the managed CORE_TEMPLATE block in different words: 'Simplest thing that satisfies the ticket.', 'File second problems; never fold them in.' and 'Read before write.' The proposal is to delete each repeat from both files, or cut it down to the part that applies only to this repo, keeping the two files in parity.

This is a cleanup to avoid a possible future problem, not a fix for something broken now. Each pair of rules says the same thing today. Both copies ask for the smallest change with an incident for every addition, both send second problems to the Suggestion Box and keep them out of the diff, and both require reading the owning artifact before writing a command, claim or test. So no agent, Review or Diagnose gets conflicting instructions, and no run, check or verdict goes wrong because of the duplication. The harm the note describes depends on a later edit changing one copy and not the other. Decisions 000474 and 000482 declined the same kind of drift worry, and the earlier 'Lean ticket frontmatter' contradiction was already fixed by conduct-files-parity. Reopen if a section A copy and its CORE_TEMPLATE counterpart start to disagree and a run, review or diagnosis follows the wrong one.

- CLAUDE.md section A 'Simplest thing that satisfies the ticket.' (no speculative features; every addition cites the incident that earned it) matches the managed block's 'HARD: Build the smallest change...' (every addition needs its earning incident).
- CLAUDE.md section A 'File second problems; never fold them in.' matches the managed block's 'File second problems in the Suggestion Box, never in this diff. Verify a pre-existing failure on the base commit before filing it.'
- CLAUDE.md section A 'Read before write.' matches the managed block's 'Read the owning artifact before writing a command, claim, or test.'
- The message reports no failed run, Review finding, Diagnose verdict or Reject-queue hold caused by these duplicates; the contradiction it cites ('Lean ticket frontmatter.') was already removed by merged conduct-files-parity.
- declined-box-000474-7b7f321a and declined-box-000482-8d69f3f5 declined similar requests whose only harm was that a future edit could make two copies drift.

Message: box-000485-fa1623e9
