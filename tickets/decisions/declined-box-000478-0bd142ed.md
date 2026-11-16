---
id: declined-box-000478-0bd142ed
kind: declined
link: box-000478-0bd142ed
reopen_after_days: 60
---
The proposal is to move redaction into the outbox lift. clutch/stages.py lift_outbox writes each lifted outbox file to main without scrubbing it. It relies on each writer to scrub first, and the redact.py writer checklist is the only guard against a new writer that forgets. The idea is to run every lifted file's text through ctx.driver.redactor before the write, plus a unit test that a configured secret lands as [REDACTED:NAME].

No current leak is shown. The incident behind this, redaction-harvest-seam, is merged: runner.py harvest now scrubs harvest.json before the lift. Every writer that reaches lift_outbox today already scrubs. Review and diagnosis come from llm_call text, which is scrubbed. The run.md fields come from that scrubbed reply (record 000108). checks.json tails and findings go through ctx.driver.redactor. Verification and regression child processes run under child_env and never get a provider key. The only file the agent writes that gets lifted is the schema-validated review_baseline report. What is left is protection against a future writer that forgets to scrub, which counts as speculative hardening. The proposal also has gaps. lift_outbox is not the only way onto main: Retro.commit_report, Author tickets and decision records commit directly, so the seam would not cover every ticket-plane writer. Scrubbing at lift would also break _lift_files' byte-equality check: an unscrubbed outbox file would never match its scrubbed canonical copy, so it would be lifted again, which risks an empty-commit GitError (see record 000121). And it would still miss secrets that JSON escapes inside .json artifacts (see record 000047). Records 000008 and 000044 already turned down a similar single-choke-point scrub because the producers scrub. Reopen when a configured secret is found unredacted in a committed tickets/ artifact on main, or when a writer that reaches main merges without being added to the redact.py checklist.

- clutch/stages.py:501-525 lift_outbox writes src.read_bytes() unscrubbed; its callers are diagnosis (441), run-record (673, 686), checks (1444), review (1533) and harvest (runner.py:482)
- clutch/runner.py:481 harvest scrubs model_dump_json with ctx.driver.redactor before lift_outbox (redaction-harvest-seam merged)
- clutch/redact.py:7 checklist lists the harvest writer as built
- clutch/stages.py:716, 824, 868 run Verification and regression children with child_env; 'verification never inherits a provider key'
- clutch/stages.py:56-58 KNOWN_ARTIFACTS holds only REVIEW_BASELINE_REPORT, so the only agent-written lifted file is schema-validated
- clutch/retro.py:300 commit_report writes to main outside lift_outbox, so lift_outbox is not the only ticket-plane lane
- clutch/stages.py:358 _lift_files skips a file byte-equal to its canonical copy; scrubbing at lift breaks that equality for any file that holds a secret
- Records declined-box-000008-2cd1c599 and declined-box-000044-79b4ca8b turned down a central scrub point because producers already scrub

Message: box-000478-0bd142ed
