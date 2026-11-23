---
id: tombstone-box-001066-95f2ae54
kind: tombstone
link: declined-box-001061-e1c775ab
reopen_after_days: 14
---
Check for implement-skips-full-suites ended base_red because the repo-wide `uv run ruff check .` also failed on merge base 52b3101c. The report asks for main to be fixed rather than the ticket, but it names no rule, file or output. The same run already reported the cause: E501 (line too long) on the generated `# purpose:` line in tests/unit/test_driver_check_nesting.py. Main now ignores that rule for the whole repository.

This is the same Ruff failure from the same origin run (implement-skips-full-suites) that record declined-box-001061-e1c775ab already decided, and tombstone-box-001063 repeats it. pyproject.toml on current main sets `[tool.ruff.lint] ignore = ["E501"]`, so the reported line-too-long finding can no longer fail `ruff check`. implement-skips-full-suites has merged, so no run is still held by this. Reopen if `uv run ruff check .` fails on current main with a finding other than E501, and attach its output.

- pyproject.toml:69 `ignore = ["E501"]` under [tool.ruff.lint]
- declined-box-001061-e1c775ab: the same run reported E501 on tests/unit/test_driver_check_nesting.py:4; Ruff ignores E501 on main
- tombstone-box-001063-34871813 already tombstoned a repeat of this Ruff report to 001061
- implement-skips-full-suites is in the merged set
- The message names no failing file, rule or check output

Message: box-001066-95f2ae54
