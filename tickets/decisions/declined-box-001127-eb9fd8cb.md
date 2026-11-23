---
id: declined-box-001127-eb9fd8cb
kind: declined
link: box-001127-eb9fd8cb
reopen_after_days: 30
---
After io-helpers-misc merged, line 102 of the planning document docs/roadmap.md still says test_drain.py imports commit_lock from test_git.py. The helper now comes from tests.misc_helpers, so the sentence is stale.

This is stale wording in a forward-looking planning document. It causes no incorrect behavior at runtime and harms no run. The registry has declined the same kind of report many times, for example 001112, 001101 and 000656. Reopen only if a ticket, prompt or gate reads this roadmap sentence as authority and acts on it wrongly.

- message class suggestion, origin io-helpers-misc, stage implement, outcome ok
- io-helpers-misc is in the merged set
- declined-box-001112-ce4cf299 and declined-box-001101-6a71b927 declined stale roadmap.md helper-location wording for the same reason

Message: box-001127-eb9fd8cb
