---
id: declined-box-001039-ad05ab5b
kind: declined
link: box-001039-ad05ab5b
reopen_after_days: 14
---
An Implement run of regression-command-program-lint said that the unit test `test_lint_verb_prints_carried_file_finding` (tests/unit/test_ticket_lint_rules.py) fails on its base commit. Its `repo` fixture replaces `Path.read_text` with an in-memory dict lookup, and the run blamed that fake for breaking DuckDB's package-metadata import under Python 3.14.

The report has no traceback, no command and no proof that the failure happens in the gate that matters. `duckdb` is imported at module level in `clutch/__main__.py`, which the test module loads before the fixture patches `Path.read_text`. So any failure must come from a lazy metadata read that depends on test order or on running the test alone. That is not shown. The originating ticket, regression-command-program-lint, has since merged, so Check's unit suite passed with this test in place, and no later Check reports it as base_red or gate_failed. That leaves no reachable harm to runs today. Reopen if a Check or unit gate on main fails on this test with a traceback that shows `importlib.metadata` or DuckDB reading through the patched `Path.read_text`. The repair would then be to scope the fake to the fixture's own paths and pass every other path to the real method.

- tests/unit/test_ticket_lint_rules.py:66 patches Path.read_text globally to `lambda p: files[p]`, so any other path raises KeyError
- clutch/__main__.py:22 imports duckdb at module level, before the fixture patch applies
- pyproject.toml requires-python >=3.14
- regression-command-program-lint appears in the merged set, so its Check, including the unit suite, passed
- The message has no traceback, no command and no failing gate output

Message: box-001039-ad05ab5b
