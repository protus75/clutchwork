---
id: declined-box-000755-ffe0b54f
kind: declined
link: box-000755-ffe0b54f
reopen_after_days: 30
---
The note says engine preflight lets a drain start when a routed provider CLI cannot run, because `cli_status` and preflight ignore the exit code of `--version`. It asks preflight to refuse when `--version` exits nonzero or prints no version. The trigger was a project-local claude whose pnpm postinstall never ran (2026-11-18). Its install-side fix, provider-install-verifies-binary, has already merged.

The premise does not match current code. `ProviderLLM.preflight` in `clutch/providers.py` does more than compare versions. After the version notice, it sends a real probe call (`adapter.invoke(PROBE_PROMPT)`) to every routed (provider, model) pair. Any exception from a probe becomes a refusal that names the road `clutch provider install <provider>`, and `session.preflight_passed()` runs only when no probe failed. A claude binary that exits 1 with 'native binary not installed' fails its probe the same way, so preflight already refuses before any claude-routed stage runs. `cli_status` only reports status for the install and doctor display; it is not the gate. The install side is covered by merged provider-install-verifies-binary. Reopen within 30 days if a journal or engine log shows a drain or serve passing preflight and then failing claude-routed stages because the CLI could not run, which would mean the probe path misses this failure.

- clutch/providers.py:925-973 ProviderLLM.preflight probes every routed (provider, model) through adapter.invoke and appends a refusal with the road 'clutch provider install <provider>' for each failed probe
- clutch/providers.py:943-944 the version comparison only adds to preflight_notices; it is not the refusal path
- clutch/providers.py:874-881 cli_status is a status reporter, not the preflight gate
- provider-install-verifies-binary is in the merged set (instance fix)

Message: box-000755-ffe0b54f
