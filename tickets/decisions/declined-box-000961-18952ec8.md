---
id: declined-box-000961-18952ec8
kind: declined
link: box-000961-18952ec8
reopen_after_days: 30
---
An Implement run of ticket-write-serialization-proof that ended ok suggests limiting the length of lines the metadata generator writes, because a generated `purpose` line could go over the repository's lint line limit. It names no file, gives no measured line length, includes no lint output and describes no harm to the run.

Declined as speculative hardening. In `clutch/meta.py`, `render` trims only the `relates` line (to 160 characters, line 155) and leaves `purpose` uncapped, so an overlong purpose comment could in theory trip ruff E501 at the configured `line-length = 200`. But the reporting run ended ok, and the message shows no generated file, no lint failure, no failed Check and no spent attempt. That means it shows no current, materially harmful runtime behavior. Reopen if a Check or Implement attempt fails, or spends a retry, on a lint finding against a `# purpose:` line written by `clutch meta refresh` or `meta fill`, with the file and lint output attached.

- clutch/meta.py:155 caps only the `relates` line at 160 characters; nothing caps the purpose line
- pyproject.toml:62 sets ruff line-length = 200, which leaves wide headroom for a one-line purpose
- message outcome is `ok` and names no file, line length or lint output
- no open or merged ticket or registry record covers purpose-line length, so tombstone does not apply

Message: box-000961-18952ec8
