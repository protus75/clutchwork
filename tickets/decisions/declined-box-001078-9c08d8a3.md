---
id: declined-box-001078-9c08d8a3
kind: declined
link: box-001078-9c08d8a3
reopen_after_days: 14
---
Check for retry-keeps-prior-branch ended base_red because the unit coverage gate (`clutch coverage gate` wrapping the parallel unit pytest run with branch coverage) also failed on merge base 7a286e39. The report asks for main to be fixed rather than the ticket. It does not say whether a test failed or a per-file coverage floor was missed, and it names no module, test, threshold or output. retry-keeps-prior-branch has since merged.

The report shows only that one Check command was red on one merge base. It does not say whether a unit test failed or a per-file coverage floor was missed, and it names no file, floor value, measured percentage, assertion or traceback. Without that, no single bounded repair can be specified or checked afterwards. The ticket that raised the report has since merged, so main was green for that gate at merge time. Earlier base_red reports with no named failure were declined for the same reason (record 000598 covers the integration suite). This one is a different command, so it is declined rather than tombstoned. Reopen if a later base_red or failure report on the unit coverage gate names the failing test or the module whose floor was missed, with measured and required coverage or the pytest output.

- message class failure_report, stage check, outcome base_red, origin retry-keeps-prior-branch, merge base 7a286e39
- summary gives only the wrapped command line; report, fixed_failure and test_issue are all null
- retry-keeps-prior-branch appears in the merged stems
- declined-box-000598-4be912da: same kind of base_red report with no failing test named (integration suite)

Message: box-001078-9c08d8a3
