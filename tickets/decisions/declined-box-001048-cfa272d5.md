---
id: declined-box-001048-cfa272d5
kind: declined
link: box-001048-cfa272d5
reopen_after_days: 30
---
`run_gate` in `clutch/covgate.py` (lines 146-148) returns the wrapped pytest exit code before it reads the coverage report. When any test fails on the first run, coverage thresholds are not checked on that run. Check's whole-command flake rerun is currently what enforces coverage for the unit entry. The note proposes that `run_gate` always evaluate the report and still exit nonzero, so the unit entry could also use `--clutch-select` failed-only reruns.

The code does what the note says, but nothing shows wrong behavior at runtime today. Merged ticket check-rerun-failed-only already handles this coupling: an entry with a `coverage` field reruns its full `entry.argv` with no `--clutch-select`, so the coverage gate still runs on the rerun and a coverage miss cannot get past Check. Its attempts 1 and 3 failed on this before it merged, and the merged design fixed that. What is left is a speed gain (failed-only reruns for the unit entry) and removing a hidden coupling. Both are refactoring or optimization, and no run has been shown to settle wrongly because of them. Reopen if a run shows a coverage-floor miss passing Check or merging, or if a measurement shows full unit-entry reruns costing a material amount of Check time or a run cycle (for example, a test failure and a coverage miss on the same candidate needing two separate Check cycles to surface).

- clutch/covgate.py:146-148: `rc = run(argv); if rc: return rc` comes before the gate and report are read, as the note says
- tickets/check-rerun-failed-only/ticket.md:42: entries with `coverage` rerun `entry.argv` unchanged; only entries without coverage get `--clutch-select`
- tickets/check-rerun-failed-only/review.md:3: approved diff keeps whole-command reruns for coverage entries
- check-rerun-failed-only is in the merged set; attempt 3's harvest paved road named this exact coverage-hiding risk, and the merged design avoided it

Message: box-001048-cfa272d5
