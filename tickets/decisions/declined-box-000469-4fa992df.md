---
id: declined-box-000469-4fa992df
kind: declined
link: box-000469-4fa992df
reopen_after_days: 30
---
The snapshot and `clutch status` mark a ticket invalid only when `parse_ticket` raises (`load_tickets` in `clutch/observe.py`). A committed ticket that `lint_findings` would flag, for a carried prefix outside the fence or a coverage-floored file with no `tests/unit/` fence, still shows as ready, while `clutch lint` exits 1 on it. The note asks whether the snapshot should carry lint findings through one validity source shared with lint.

No current harmful gap is shown. Intake (`_intake_plan_stem`, `clutch/tickets.py:714`) and requisition review (`review_target`, `clutch/requisition.py:81`) already refuse a ticket that has lint findings. A committed ticket can only pick one up later, when `test-gate.toml` floors or a lint rule change after the commit. In that case the drain still dispatches it, because its scan uses the same `parse_ticket`. So 'ready' in the snapshot matches the drain's real admission and does not misstate it. The note cites no run where a ticket shown ready later failed because of a lint finding, and it is worded as an open design question ('decide whether'). The orphaned-stem case depends on a lint rule that is not merged, and the orphan incident was already declined (box-000467). The shared-admission idea also repeats the declined box-000141 (one admission check for run and drain). Reopen if a committed ticket shown ready with a standing `lint_findings` finding is dispatched and loses a paid attempt to that finding. Then the repair would be for the drain admission and the snapshot to both use one shared lint-inclusive predicate.

- clutch/observe.py:454-465 load_tickets catches TicketInvalid from parse_ticket only
- clutch/tickets.py:562-591 lint_findings covers carried-file, carried-prefix-outside-fence and unit-coverage-floor rules
- clutch/tickets.py:714 intake refuses a ticket with lint_findings before commit
- clutch/requisition.py:78-83 review_target refuses a ticket with lint_findings
- declined-box-000141-981e19ef: shared admission check for run and drain declined
- declined-box-000467-215903ca: orphaned-stem incident declined

Message: box-000469-4fa992df
