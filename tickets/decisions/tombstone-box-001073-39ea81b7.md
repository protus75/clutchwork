---
id: tombstone-box-001073-39ea81b7
kind: tombstone
link: declined-box-001061-e1c775ab
reopen_after_days: 14
---
Check for serve-live-keep-single-verdict ended base_red because the repo-wide `uv run ruff check .` also failed on merge base a2600ead. The report asks for main to be fixed, not the ticket. It names no rule, file or output. This is the same base-red ruff report that records 001066 and 001068 already sent to declined record 001061. That failure came from E501 on a generated `# purpose:` metadata line, and main now ignores E501 for the whole repository.

This repeats the base-red ruff report already settled by declined-box-001061-e1c775ab and tombstoned twice more (001066, 001068). The report gives no rule, file or ruff output, so nothing points to a cause other than the E501 failure already settled. pyproject.toml on current main sets `ignore = ["E501"]` under `[tool.ruff.lint]`, so the known cause is gone. serve-live-keep-single-verdict has since merged, so no run is still blocked. Reopen if a Check on a merge base that already has the E501 ignore reports a ruff base_red failure with the rule and file named.

- pyproject.toml:69 `ignore = ["E501"]` under ruff lint config on current main
- declined-box-001061-e1c775ab: repo-wide ruff E501 on generated purpose line; main ignores E501
- tombstone-box-001066-95f2ae54 and tombstone-box-001068-31b5eeba: identical base-red ruff reports linked to 001061
- serve-live-keep-single-verdict is in the merged set
- message carries no rule, file, or ruff output

Message: box-001073-39ea81b7
