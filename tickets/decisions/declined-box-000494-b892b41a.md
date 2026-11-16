---
id: declined-box-000494-b892b41a
kind: declined
link: box-000494-b892b41a
reopen_after_days: 60
---
The suggestion asks for a unit test that ties the flag column of the verb table in docs/how-clutch-works.md section 2.1 to `clutch/__main__.py::_parser`. It also asks for one declared list of state_dir paths that both the writers in clutch/*.py and the file table in section 10.1 must match, so a new flag or state file cannot ship without being documented. It is filed as the cause fix behind the merged docs-truth-sweep instance fix.

This is a test-only guard against prose drift in a design document. It does not fix a runtime behavior gap. The instance rows it cites are already fixed on main: section 2.1 lists `drain [--detach] [--parked STEM] [--deadline ISO]` and `--extension` on confirm and reject, and section 10.1 lists drain.out, coverage-map.json and the `.base/` and `.regression-base/` scratch worktrees. The message names no run, operator decision or agent action that went wrong because of a missing row. The operator-facing verb surface, clutch/docs/host-running.md, is already pinned to the parser by tests/unit/test_host_running.py::test_verb_table_matches_parser. The proposed state_dir path registry would add a production abstraction whose only consumer is a docs test. The registry has declined the same kind of request before: a parity test for conduct files (000482), one home for a duplicated rule (000474), and verb-table wording drift (000493). Reopen if a stale row in section 2.1 or 10.1 is shown to cause a failed or misdirected run, for example an agent or operator building a wrong command or path from that table, or if a run record or review finding shows a stale-row incident recurring after docs-truth-sweep.

- docs/how-clutch-works.md:62 already documents `drain [--detach] [--parked STEM] [--deadline ISO]` and `<state_dir>/drain.out`
- docs/how-clutch-works.md:73-74 already document `--extension` on confirm and reject
- docs/how-clutch-works.md:691-698 already list drain.out, coverage-map.json and worktrees/.base/ and .regression-base/
- docs-truth-sweep and docs-truth-sweep-code-strings are in the merged set; the cited drift instances are closed
- tests/unit/test_host_running.py::test_verb_table_matches_parser already pins the operator run guide's verb rows to the parser
- Prior declines of doc/rule-parity test requests: declined-box-000482-8d69f3f5, declined-box-000474-7b7f321a, declined-box-000493-bc44dcf5

Message: box-000494-b892b41a
