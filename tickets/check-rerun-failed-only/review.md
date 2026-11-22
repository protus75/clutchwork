# Review: snag

The selected rerun works and both prior findings are fixed, but deleting the rerun's rc-findings line means a ticket with one flaky test now skips the whole-suite coverage gate, and a test_host_mechanical case was changed so the test suite no longer catches that.

## Findings

- [logic] clutch/stages.py:1345 The diff deletes `if result.rc != 0 and "failed" not in last.values(): findings.extend(report.findings)` and builds the report from per-test findings only. config.yaml's unit entry wraps pytest in `clutch coverage gate`. `run_gate` (clutch/covgate.py:146-148) returns pytest's nonzero rc before it evaluates coverage thresholds, so the first run with a failed test never checks coverage. Before this diff, the full-suite rerun evaluated the gate, and a coverage drop added a finding through the deleted line. Now the rerun runs only the selected ids, its gate result is thrown away, and nothing else checks coverage. A ticket that lowers coverage below `test-gate.toml` thresholds and hits one flaky test passes Check with no finding. Any other non-test cause of a nonzero exit on the rerun is also ignored. This weakens a gate, which the ticket does not allow (only the rerun's scope may change). (do instead: In stages.py, when a selected rerun turns every failed id into a pass, still enforce the whole-suite gate, for example: evaluate the first run's coverage report against the gate with the existing `clutch.covgate` functions, or run the full command once when the first run's rc may have hidden a gate failure. Add a test where the first run fails one test and also misses coverage, the selected rerun passes, and Check still reports a finding.)
- [logic] tests/integration/test_host_mechanical.py:396 The `test_results_fail_closed` case `[(1, {"a": "failed"}), (1, {"a": "passed"}), (0, {})]` asserted that a rerun exiting nonzero while recording passes fails closed. The diff replaces it with a missing-results case `(1, {})` instead of keeping that property. The ticket did not ask for this change (criterion 5 only requires the existing file to pass). It hides the gate bypass described in the previous finding. (do instead: Restore the original fail-closed case, or a version of it that fits the selected rerun, so that a nonzero rerun exit caused by something other than a recorded test failure (such as a coverage gate) still produces a finding. Keep the missing-results case as an additional parameter.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "32ad8a0d932332e80ed2489c9195543cf2f7140a",
  "stem": "check-rerun-failed-only",
  "reviewed_sha": "32ad8a0d932332e80ed2489c9195543cf2f7140a",
  "summary": "The selected rerun works and both prior findings are fixed, but deleting the rerun's rc-findings line means a ticket with one flaky test now skips the whole-suite coverage gate, and a test_host_mechanical case was changed so the test suite no longer catches that.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/stages.py",
      "line": 1345,
      "message": "The diff deletes `if result.rc != 0 and \"failed\" not in last.values(): findings.extend(report.findings)` and builds the report from per-test findings only. config.yaml's unit entry wraps pytest in `clutch coverage gate`. `run_gate` (clutch/covgate.py:146-148) returns pytest's nonzero rc before it evaluates coverage thresholds, so the first run with a failed test never checks coverage. Before this diff, the full-suite rerun evaluated the gate, and a coverage drop added a finding through the deleted line. Now the rerun runs only the selected ids, its gate result is thrown away, and nothing else checks coverage. A ticket that lowers coverage below `test-gate.toml` thresholds and hits one flaky test passes Check with no finding. Any other non-test cause of a nonzero exit on the rerun is also ignored. This weakens a gate, which the ticket does not allow (only the rerun's scope may change).",
      "paved_road": "In stages.py, when a selected rerun turns every failed id into a pass, still enforce the whole-suite gate, for example: evaluate the first run's coverage report against the gate with the existing `clutch.covgate` functions, or run the full command once when the first run's rc may have hidden a gate failure. Add a test where the first run fails one test and also misses coverage, the selected rerun passes, and Check still reports a finding.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/integration/test_host_mechanical.py",
      "line": 396,
      "message": "The `test_results_fail_closed` case `[(1, {\"a\": \"failed\"}), (1, {\"a\": \"passed\"}), (0, {})]` asserted that a rerun exiting nonzero while recording passes fails closed. The diff replaces it with a missing-results case `(1, {})` instead of keeping that property. The ticket did not ask for this change (criterion 5 only requires the existing file to pass). It hides the gate bypass described in the previous finding.",
      "paved_road": "Restore the original fail-closed case, or a version of it that fits the selected rerun, so that a nonzero rerun exit caused by something other than a recorded test failure (such as a coverage gate) still produces a finding. Keep the missing-results case as an additional parameter.",
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
