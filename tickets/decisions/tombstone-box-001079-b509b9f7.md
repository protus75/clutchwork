---
id: tombstone-box-001079-b509b9f7
kind: tombstone
link: declined-box-001078-9c08d8a3
reopen_after_days: 14
---
Check for gemini-provider-configured ended base_red because the unit coverage gate (`clutch coverage gate` wrapping the parallel unit pytest run with branch coverage) also failed on merge base b6f6b67a. The report asks for main to be fixed instead of the ticket. It does not name a failing test, module, coverage floor or output, and gemini-provider-configured has since merged.

Registry record 001078 already declined the same report: a base_red unit coverage gate failure with no failing test, module, threshold or output named. This message repeats that report from another ticket and merge base and adds no new evidence. The ticket it came from, gemini-provider-configured, is in the merged set, so nothing is still blocked. Reopen if a report names the failing unit test or the per-file coverage floor missed on main, with the gate output.

- message: class failure_report, stage check, outcome base_red, origin gemini-provider-configured, merge base b6f6b67a, command `clutch coverage gate -- ... tests/unit ... --cov-branch ...`
- decision declined-box-001078-9c08d8a3: the same base_red unit coverage gate report, with no test, module, threshold or output named
- merged stems include gemini-provider-configured
- neighbors: unavailable (index_unreadable)

Message: box-001079-b509b9f7
