---
id: declined-box-000893-4c8a8e81
kind: declined
link: box-000893-4c8a8e81
reopen_after_days: 30
---
The index-build-r2 Implement run finished ok. It noted that `uv run clutch meta check` fails on its base commit because some files outside the ticket's fence have missing or out-of-date `# clutch:meta` blocks. It does not say which files, how many, or what the check printed.

The message shows no harmful runtime behavior. Meta drift is a soft gate by default: `meta_drift` is in `SOFT_GATE_DEFAULTS` in `clutch/gates.py`. `config.yaml` has no hard host check that runs `meta check`. So drift outside a fence does not block Check or merge, and the reporting run ended ok. The report names no files and gives no output, so it cannot be bounded to one buildable ticket with a measurable result. Fixing stale blocks would be cleanup across the tree. Reopen if `meta check` becomes a hard check, or if drifted blocks outside a fence make a run fail at Check or merge, with the files named and the gate output attached.

- clutch/gates.py:33 SOFT_GATE_DEFAULTS = {"meta_drift"}
- config.yaml has no hard host check that runs `meta check`
- The reporting run's outcome is ok, at the implement stage
- The message names no drifted files and includes no command output

Message: box-000893-4c8a8e81
