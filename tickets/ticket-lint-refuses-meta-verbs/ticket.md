---
state: confirmed
source: box:suggestion
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/tickets.py::lint_findings
- tests/unit/test_ticket_lint_verification_search.py

## On-demand
- clutch/docs/host-authoring.md

## Goal / Why
`clutch ticket lint` accepts a `## Verification` command or an acceptance criterion that runs one of the meta check, refresh or fill verbs. The Implement spec forbids those verbs, because Check owns the meta headers. A ticket that requires them is impossible to satisfy as written. This happened to a ticket whose attempt 0 ended in a recorded contradiction (its `harvest.json` and `diagnosis.json` for attempt 0), which cost an attempt, a premise bounce and a diagnosis. Diagnose named the class fix: refuse these verbs at authoring time.

After this ticket, lint exits nonzero on such a ticket and names the paved road. The authoring guide carries one bullet saying the same. This follows the pattern of `lint-refuses-grep-verification` and `lint-refuses-two-dot-git-diff-main`. It does not touch Implement's own conduct, which `implement-spec-meta-headers-from-verbs` and `check-owns-meta-headers` cover.

Decision on exceptions: there is none. A ticket whose deliverable is a meta verb proves it through a unit test, never by running the verb in `## Verification` or in a criterion that tells the implementer to run it.

## Boundary contract
### Ticket lint authoring rules
- disposition: extend
- owner: clutch/tickets.py
- consumers: `clutch ticket lint`, intake, and the Author and review stages that call `tickets.lint_findings`
- observable change: `lint_findings` adds one finding when a Verification argv, or an acceptance criterion, runs the meta verbs check, refresh or fill. The finding's paved road says to leave meta headers to Check and to drop the meta verb from Verification and criteria.
- compatibility: tickets that do not name these verbs lint exactly as before. Settled and rejected tickets are not re-linted.
- acceptance: a ticket with a meta check command in Verification gets a finding. The same ticket with that line removed gets none.
- tests: a new unit test file beside the existing lint-rule tests
- post-merge source of truth: clutch/tickets.py, with the rule described in clutch/docs/host-authoring.md

## Scope in / Scope out
Scope in:
- In `lint_findings` in `clutch/tickets.py`, add a check on each `ticket.verification` argv. It fires when the argv contains `clutch` as a program or argument and is followed, in order, by `meta` and then `check`, `refresh` or `fill`. This must also match the `uv run` prefixed form.
- In the same function, add a check on the Acceptance criteria text. It fires only on an instruction form: a criterion whose text has `clutch meta` followed by `check`, `refresh` or `fill` inside a backtick span (the check the criterion names). A criterion that spells the verbs in prose outside backticks, such as "the meta check verb", never fires. This ticket's own criteria therefore avoid backticked meta commands and lint clean; the test builds the backticked forms from string parts in the test file so the test source does not itself trip any scan.
- Add one bullet to the `Verification` entry in `clutch/docs/host-authoring.md`. It says Check owns meta headers, so Verification and criteria never run the meta check, refresh or fill verbs, and a ticket whose subject is a meta verb proves it with a unit test.
- Add a new test file `tests/unit/test_ticket_lint_meta_verbs.py`.

Scope out:
- The Implement spec and Check behavior.
- Existing tickets.
- Any exception list.
- Other meta subcommands.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- tests/unit/test_ticket_lint_meta_verbs.py

## Acceptance criteria
1. In `./dev.py test tests/unit/test_ticket_lint_meta_verbs.py`, a Verification running the meta check verb through `uv run` yields exactly one finding whose message names the meta verb and whose paved road mentions Check owning meta headers. The test fails if lint yields no finding.
2. The same test parametrizes check, refresh and fill, each of which yields a finding. It also covers the bare form with no `uv run` prefix.
3. The same test, run by `./dev.py test tests/unit/test_ticket_lint_meta_verbs.py`, puts a backticked meta check command in an acceptance criterion and expects a finding. A criterion that mentions the meta group only in prose or as a help request yields none.
4. The same test shows that the ticket with the meta line replaced by a `./dev.py test tests/x.py` line lints with zero findings, not a leftover finding.
5. `./dev.py test tests/unit` passes, including the existing lint tests, which prove that the rg/grep finding and the two-dot git diff finding are unchanged.

## Verification
```
./dev.py test tests/unit/test_ticket_lint_meta_verbs.py tests/unit/test_ticket_lint_verification_search.py tests/unit/test_ticket_lint_rules.py
```

## Definition of rejected
The rule lets a meta-verb Verification pass lint, or it flags a ticket that does not run a meta verb, including this ticket itself. A rule that adds an exception list or a flag, or that changes the Implement spec, also rejects the branch.

## Time budget
- expected: 15m
- stuck: 30m
