---
id: declined-box-000482-8d69f3f5
kind: declined
link: box-000482-8d69f3f5
reopen_after_days: 30
---
The note asks for a unit test that fails when the repo-specific engine-conduct rules in AGENTS.md stop matching section A of CLAUDE.md, outside the managed clutch:core block. It follows the merged conduct-files-parity ticket, which fixed a drift where AGENTS.md lacked three rules and the preamble sentence about compressing a rule to one line. Today the rule that both files change together is enforced only by prose.

The drift that motivated this is already fixed. The merged conduct-files-parity ticket restored the missing rules, and AGENTS.md now has 'The plan is the seed.', 'Phase order.' and the 'compress it to one line' preamble sentence, in the same order as CLAUDE.md section A. What remains is a proposed test that stops the drift from coming back. The note shows no current incorrect runtime behavior: it names no codex Implement run that broke a rule because AGENTS.md lacked it. Under the triage bar, prevention that adds only a test is declined unless it is tied to reachable harm. This also matches declined-box-000474-7b7f321a, which declined a test that two copies of a rule stay equal for the same reason. Reopen if CLAUDE.md section A and AGENTS.md '## Engine conduct' differ again on main and a codex-routed run is shown to break a rule that was missing from AGENTS.md, or if drift happens a second time after this decision.

- tickets/conduct-files-parity has run.md, checks.json and review.md, and the stem is in the merged set, so the reported instance is resolved.
- AGENTS.md:53 has the 'When a rule gains its gate, compress it to one line in the same change.' preamble, and AGENTS.md:84 and AGENTS.md:105 have 'The plan is the seed.' and 'Phase order.'.
- AGENTS.md:55-106 '## Engine conduct' lists the same rules in the same order as CLAUDE.md '## A. Engine conduct' on current main.
- No test under tests/ compares AGENTS.md and CLAUDE.md outside the managed block. tests/integration/test_hostfiles.py:74-75 only uses their project bytes as fixtures for core adoption.
- The message names no run where an agent behaved wrongly because AGENTS.md lacked a rule.
- Precedent: declined-box-000474-7b7f321a declined a test that two copies of a rule stay equal, because no current behavior gap was shown.

Message: box-000482-8d69f3f5
