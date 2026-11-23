# Review: snag

The signal move and the scorecard fold look correct, but in all three updated panel test files the checks that no signal is written still only watch the engine-log fake; that log never receives panel_facts now, so those checks cannot fail and AC3 is not actually tested.

## Findings

- [acceptance] tests/unit/test_triage_panel_use.py:79 AC3 requires that a size-1 triage pass and a pass whose members all fail append no signal. The fixture now gives the driver a FakeJournal, but the negative checks for the size-1, timeout, all-dropped and failed-member passes (lines 98, 104, 177, 180, 184) still only call `d.log.event.assert_not_called()`. panel_facts no longer goes to the engine log, so these checks pass even if `_settle_pass` writes a signal on those paths. (do instead: At each of those points also assert `d.journal.events == []`, or that no `signal` event has body `signal == "panel_facts"`.)
- [logic] tests/unit/test_review_panel_use.py:60 The Recording fake now journals panel_facts, but the negative checks for the single-member and non-ok paths still look only at the engine log: `assert driver.log.events == []` (line 109), `not driver.log.events` (lines 209, 219) and `all(name != "panel_facts" for name, _ in driver.log.events)` (line 279). Since the signal never reaches the log, these checks cannot fail, so nothing tests the Definition-of-rejected rule that a size-1 stage or a failed panel writes no signal. (do instead: In those assertions, also assert that the driver's journal holds no `signal` event with `signal == "panel_facts"`.)
- [logic] tests/unit/test_diagnosis_panel_use.py:38 The Driver fake now has a FakeJournal, but the single-model and failure checks still assert only on the engine-log list: `driver.events == []` (line 88), `not driver.events` (line 92), and `not d.events` (lines 159, 171). The panel_facts signal now goes to `driver.journal`, so these checks can no longer catch a size-1 or failed diagnose panel that writes a signal. (do instead: Next to those checks, assert that `driver.journal.events` (or `d.journal.events`) holds no panel_facts `signal` event.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ecada1be8dea814c5b70ab5fe965eb3893c59c63",
  "stem": "panel-facts-journal-signal",
  "reviewed_sha": "ecada1be8dea814c5b70ab5fe965eb3893c59c63",
  "summary": "The signal move and the scorecard fold look correct, but in all three updated panel test files the checks that no signal is written still only watch the engine-log fake; that log never receives panel_facts now, so those checks cannot fail and AC3 is not actually tested.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_triage_panel_use.py",
      "line": 79,
      "message": "AC3 requires that a size-1 triage pass and a pass whose members all fail append no signal. The fixture now gives the driver a FakeJournal, but the negative checks for the size-1, timeout, all-dropped and failed-member passes (lines 98, 104, 177, 180, 184) still only call `d.log.event.assert_not_called()`. panel_facts no longer goes to the engine log, so these checks pass even if `_settle_pass` writes a signal on those paths.",
      "paved_road": "At each of those points also assert `d.journal.events == []`, or that no `signal` event has body `signal == \"panel_facts\"`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/unit/test_review_panel_use.py",
      "line": 60,
      "message": "The Recording fake now journals panel_facts, but the negative checks for the single-member and non-ok paths still look only at the engine log: `assert driver.log.events == []` (line 109), `not driver.log.events` (lines 209, 219) and `all(name != \"panel_facts\" for name, _ in driver.log.events)` (line 279). Since the signal never reaches the log, these checks cannot fail, so nothing tests the Definition-of-rejected rule that a size-1 stage or a failed panel writes no signal.",
      "paved_road": "In those assertions, also assert that the driver's journal holds no `signal` event with `signal == \"panel_facts\"`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/unit/test_diagnosis_panel_use.py",
      "line": 38,
      "message": "The Driver fake now has a FakeJournal, but the single-model and failure checks still assert only on the engine-log list: `driver.events == []` (line 88), `not driver.events` (line 92), and `not d.events` (lines 159, 171). The panel_facts signal now goes to `driver.journal`, so these checks can no longer catch a size-1 or failed diagnose panel that writes a signal.",
      "paved_road": "Next to those checks, assert that `driver.journal.events` (or `d.journal.events`) holds no panel_facts `signal` event.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
