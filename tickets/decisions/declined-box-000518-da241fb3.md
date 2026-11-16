---
id: declined-box-000518-da241fb3
kind: declined
link: box-000518-da241fb3
reopen_after_days: 14
---
The 'Gate to start' column in docs/roadmap.md section 1 is prose only, and none of the planned roadmap-driver pieces read it. release-gates-as-commands adds ship-gate blocks only. roadmap-table-parser's choose makes a later master table's rows ready as soon as the earlier tables finish, and row 35 (re-measure) has no stem, so the parser skips it. Once those tickets and the driver loop merge, the conditional journal-window rows (journal-query-layer and its ports) and the training release rows would become ready even if their start conditions (journal reads still dominate after re-measurement; evidence store has captured one full drain) were never checked.

This gap is in unmerged design, not in current runtime behavior. clutch/roadmap.py does not exist. release-gates-as-commands, roadmap-table-parser, roadmap-author and driver-loop are all unmerged, so nothing reads docs/roadmap.md or makes any row ready today, and no run can author a row past an unchecked start gate. The parallel/graphics start gate is already enforced by table order, because its dedup rows sit in an earlier release's table. Its Gemini A0 fact 7 condition affects only the conditional row (56), which the parser skips. The real exposure is the journal window and the training release, and that exposure starts only when the driver authors rows unattended. Reopen when roadmap-table-parser and release-gates-as-commands have merged and choose still makes a release's rows ready with no start-gate check, or earlier if the owner wants start-gate blocks added to those open tickets before they run.

- docs/roadmap.md:23-29: section 1 table has separate 'Gate to start' and 'Gate to ship' columns; 0.3.0 (conditional) starts only if re-measurement shows journal reads still dominate; 0.5.0 starts once the evidence store has captured one full drain
- docs/roadmap.md:346: row 35 '(re-measure)' has no backticked stem; tickets/roadmap-table-parser/ticket.md:38 says the parser skips it as a non-ticket row
- tickets/roadmap-table-parser/ticket.md:44: choose readies a later master table's rows once earlier tables have no unfinished rows; start gates are not mentioned
- tickets/release-gates-as-commands/ticket.md:41,59: gate blocks encode each release's ship gate only
- docs/roadmap-driver-plan.md:67: roadmap author picks rows by Depends on and release order only
- Glob clutch/roadmap*.py: no files; the roadmap reader does not exist on main

Message: box-000518-da241fb3
