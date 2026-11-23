---
id: tombstone-box-001075-ef63f0ff
kind: tombstone
link: declined-box-001061-e1c775ab
reopen_after_days: 14
---
Check for reconcile-spares-confirming-draft ended base_red because the repo-wide `uv run ruff check .` also failed on merge base a84781db. The report asks for main to be fixed instead of the ticket. It names no rule, file or output. reconcile-spares-confirming-draft has since merged.

This is the same base-red repo-wide ruff report already covered by declined record 001061. Records 001066, 001068 and 001073 sent the same kind of report there from other merge bases. That failure came from E501 on a generated `# purpose:` metadata line, and main now ignores E501 for the whole repository. The report gives no new rule, file or output, and the ticket it came from has merged. Reopen if a later report names a specific ruff rule and file that fails on current main.

- message: class failure_report, stage check, outcome base_red, origin reconcile-spares-confirming-draft, merge base a84781db, no rule or file named
- declined-box-001061-e1c775ab: repo-wide ruff E501 on the generated purpose line, which main now ignores
- tombstone-box-001066, 001068 and 001073: the same base-red ruff report, linked to 001061
- reconcile-spares-confirming-draft is in the merged set

Message: box-001075-ef63f0ff
