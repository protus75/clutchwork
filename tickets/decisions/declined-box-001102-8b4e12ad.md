---
id: declined-box-001102-8b4e12ad
kind: declined
link: box-001102-8b4e12ad
reopen_after_days: 30
---
After claude-session-names merged and began adding the session name to the Claude provider argv, the Implement run noted that two budget assertions in tests/integration/test_providers.py are currently skipped. If they were re-enabled, they would need updating to expect the added session-name argument.

This is a test-only improvement. The two assertions are skipped, so they fail no run and block no gate, and the note describes no wrong runtime behavior in the provider argv or the budget handling. The run that filed it ended ok, and claude-session-names is merged. Reopen if those assertions are re-enabled and fail at Check, or if evidence shows the session-name argument breaks budget flags in a real provider call.

- Message class suggestion, origin claude-session-names, stage implement, outcome ok
- claude-session-names is in the merged set
- The summary says the two assertions are skipped, so they cannot fail a Check today
- No open ticket or registry record covers this, and no runtime harm is described

Message: box-001102-8b4e12ad
