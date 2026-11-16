---
id: declined-box-000488-0f8b055b
kind: declined
link: box-000488-0f8b055b
reopen_after_days: 30
---
An integration test runs the core_drift input gatherer against the live checkout root instead of a fixture repo. The gatherer, `hostfiles.committed_core`, leaves out any routed conduct file whose working bytes differ from its HEAD blob and adds a core_drift finding for it. So when a ticket edits CLAUDE.md or AGENTS.md (or CORE_TEMPLATE and re-renders them), the test fails until the edit is committed. The note proposes moving the test to a temporary repo or documenting a commit-first step.

The mechanism is real, but the harm is small and recovered from every time it has happened. The test fails only while a conduct edit is uncommitted. Implement commits before Check, so Check and merge always see matching bytes, and no gate result or merge decision goes wrong. Both runs the note cites, conduct-files-parity and contention-authoring-rules, ended `ok` on their first attempt. Each run record says the first full-suite run failed for this reason and passed after the commit, so no attempt, premise_bounce, Diagnose call or retry was spent. As things stand, this is a test-only improvement with no wrong runtime behavior and no measured pipeline cost. Moving the test to a temporary repo would also stop it checking that this repo's own committed conduct passes core_drift, which is what it is for. Reopen if an Implement attempt ends `premise_failed` or another non-ok outcome, or spends a Diagnose call or a retry, and its findings or run record cite `test_core_activation_committed_conduct` or uncommitted conduct bytes.

- tests/integration/test_gates.py:299-315 sets root = Path(__file__).resolve().parents[2], calls hostfiles.committed_core(root, ...), and asserts set(core_files) == {'CLAUDE.md','AGENTS.md'} and a core_drift pass
- clutch/hostfiles.py:193-207 compares sha1('blob <len>\0'+working bytes) with git rev-parse HEAD:<rel>; on a mismatch it adds a core_drift finding and leaves the file out of core_files
- tickets/conduct-files-parity/run.md: Outcome ok; 'The full suite initially failed because it checks committed conduct files; it passed after commit.'
- tickets/contention-authoring-rules/run.md: Outcome ok; 'The first full-suite run failed because the conduct files had not yet been committed; the final verification pass succeeded after committing.'
- Neither ticket directory has an attempts/ entry or diagnosis.json, so neither run spent a retry or a premise_bounce
- Implement commits on the ticket branch before Check, so Check and merge read working bytes that match HEAD

Message: box-000488-0f8b055b
