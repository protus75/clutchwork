---
id: declined-box-001061-e1c775ab
kind: declined
link: box-001061-e1c775ab
reopen_after_days: 30
---
An Implement run from implement-skips-full-suites said repo-wide Ruff reports E501 (line too long) on the generated `# purpose:` metadata line at tests/unit/test_driver_check_nesting.py:4. It asked for the meta generator or the lint handling to be fixed so this cannot recur. On current main, Ruff ignores E501 for the whole repository, so that line cannot fail the lint check.

The defect does not exist on current main. pyproject.toml sets `[tool.ruff.lint] ignore = ["E501"]` (and line-length = 200), so the hard `lint` check (`uv run ruff check .` in config.yaml) never reports E501. The long purpose line at tests/unit/test_driver_check_nesting.py:4 cannot turn lint red or make a run base_red. The report ended ok, shows no lint output, and names no run it harmed. It matches the earlier declined record 000961, which asked to cap the length of generated purpose lines without evidence. Reopen if a run's Check shows `ruff check .` failing on a generated clutch:meta line, with the lint output attached.

- pyproject.toml:66-69 `[tool.ruff.lint]` ignore = ["E501"]
- pyproject.toml:62 line-length = 200
- config.yaml:59 lint check is `uv run ruff check .`, which honors the pyproject ignore
- tests/unit/test_driver_check_nesting.py:4 is the purpose line in the meta block; E501 is not enforced for it
- declined-box-000961-18952ec8: earlier request to cap generated purpose-line length, declined for lack of evidence

Message: box-001061-e1c775ab
