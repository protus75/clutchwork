---
id: tombstone-box-001153-ca46f396
kind: tombstone
link: declined-box-001078-9c08d8a3
reopen_after_days: 14
---
Check for ui-shared-renderers ended base_red. The unit coverage gate (`clutch coverage gate` wrapping the parallel unit pytest run with branch coverage) also failed on merge base 1b9e96e3, so the report asks for main to be fixed instead of the ticket. It does not say whether a test failed or a per-file coverage floor was missed, and it gives no module, test, threshold or output.

This is the same kind of report that registry record 001078 already declined, and record 001079 already tombstoned a repeat of it. In each case Check reported that the unit coverage gate was base_red on the merge base, with no failing test, module, floor or output. This message has the same shape and adds no new evidence. A base_red outcome means the gate still runs and the ticket's own change is not blamed, so the report shows no harm the gate failed to catch. Reopen the question if a later report names the failing test or the coverage floor missed on main, with its output.

- Message class failure_report, stage check, outcome base_red, origin ui-shared-renderers, merge base 1b9e96e3
- The command is the unit coverage gate: `clutch coverage gate -- ... --cov=clutch --cov-branch ... -n auto`
- The report gives no failing test name, module, coverage threshold or output
- Registry declined-box-001078-9c08d8a3 declined the same report about the unit coverage gate being base_red on 7a286e39
- Registry tombstone-box-001079-b509b9f7 tombstoned the same report on b6f6b67a and linked it to 001078

Message: box-001153-ca46f396
