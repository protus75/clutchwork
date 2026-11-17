---
id: declined-box-000602-8ec884ea
kind: declined
link: box-000602-8ec884ea
reopen_after_days: 14
---
The roadmap-status-stuck-rows Check stage reported that the whole parallel integration suite also failed on merge base a433d181, so the run was recorded as base_red. The report does not name a failing test and gives no output. The ticket has since merged.

Nothing here shows a current failure that one bounded ticket could repair. The report names no failing test and carries no assertion, traceback or captured output, so there is no specific defect on main to reproduce. roadmap-status-stuck-rows is in the merged set. Its committed checks.json shows the integration check with 0 failures and base_red false, so the red base did not block it. Record declined-box-000598-4be912da declined the same kind of report: a whole-suite base_red with no test named, seen on a different base. This report is not tombstoned to that record because the failing test may differ. Reopen if a later report names the failing test and includes output showing it fails on current main.

- Message: class failure_report, origin roadmap-status-stuck-rows, stage check, outcome base_red, base a433d181; no test name or output
- roadmap-status-stuck-rows is listed in the merged stems
- tickets/roadmap-status-stuck-rows/checks.json: failed 0, base_red false
- declined-box-000598-4be912da: the same kind of whole-suite base_red report with no test named, declined

Message: box-000602-8ec884ea
