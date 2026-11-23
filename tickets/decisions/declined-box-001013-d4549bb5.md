---
id: declined-box-001013-d4549bb5
kind: declined
link: box-001013-d4549bb5
reopen_after_days: 14
---
The Check stage for merge-dirty-checkout-never-blocks ended base_red. The full parallel integration suite also failed on merge base 934f97b8, and the report says main should be fixed instead of the ticket. It does not name a failing test and includes no output, assertion or suspected cause. merge-dirty-checkout-never-blocks has since merged.

Nothing here can be built into a ticket. The report names no failing test, assertion, traceback or cause, so no repair can be scoped or checked. The ticket that reported it has merged, so this failure no longer blocks anything. The same Implement run's own notes point to intermittent serve-admission integration timeouts as the likely source. Records 000983 and 001010 already declined or tombstoned those timeouts for having no output, and records 000598 and 000602 declined similar base_red reports that named no test. Reopen within 14 days if a base_red report names the failing integration test and includes its assertion or timeout output, and the same test fails on main again.

- message class failure_report, stage check, outcome base_red, origin merge-dirty-checkout-never-blocks, no failing test or output
- merge-dirty-checkout-never-blocks is in the merged set
- declined-box-000598-4be912da and declined-box-000602-8ec884ea: earlier whole-suite base_red reports with no named test, declined
- declined-box-000983-96a0ff93 and tombstone-box-001010-220843ef: serve-admission integration timeouts in this same run, reported without output
- neighbors index unavailable; no neighbor evidence either way

Message: box-001013-d4549bb5
