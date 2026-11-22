# Review: snag

The selected rerun works for a bare pytest command, but it breaks Check for the unit host entry wrapped in `clutch coverage gate` and stops quarantine release whenever a rerun happens.

## Findings

- [logic] clutch/stages.py:1295 The rerun appends `--clutch-select` to `entry.argv` and runs only the failed ids. config.yaml's unit entry is `clutch coverage gate -- ... pytest ...`. After that command exits 0, `run_gate` (clutch/covgate.py:140-164) checks repository and per-file coverage thresholds. A run of one test cannot meet them, so the gate exits nonzero even when the flaky test passes. Line 1342 `if result.rc != 0 and "failed" not in last.values(): findings.extend(report.findings)` then adds the rerun's command-failure finding, so every flaky unit test now fails Check. It used to be classified as a flake, which breaks the ticket's promise that flake detection is unchanged. (do instead: In stages.py, judge a selected rerun by its recorded outcomes, not by the wrapper's exit code. If every selected id is recorded and none failed, do not add the rerun command's rc findings. If any selected id is missing from the rerun results, return invalid() or add a finding. Add a test where the rerun records the selected id as passed but exits nonzero, and assert the test is classified as flaky with no extra finding.)
- [logic] clutch/stages.py:1295 Once the rerun is selected, `last` holds only the first run's failed ids. The quarantine-release loop after the rerun block (`for identity in flake.quarantine().active.values(): if last.get(identity.test_id) != "passed": continue`) used to see every test's rerun outcome. Now, when any test fails and triggers a rerun, a quarantined test that passed is missing from `last`, so its release is silently skipped. Before this change it would have been released. That changes quarantine behavior, which the ticket's boundary contract says stays unchanged. (do instead: For the release check, merge the outcomes, e.g. `outcomes = {**first, **last}`, and test `outcomes.get(identity.test_id) != "passed"`. Keep `last` (only the rerun results) for the flaky and `failed on rerun` logic. Add a test that a passing quarantined test with a merged fix is still released when an unrelated test triggers a rerun.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "14c2d934a98da0e76837c3bf3ab9accbb9ee2bcb",
  "stem": "check-rerun-failed-only",
  "reviewed_sha": "14c2d934a98da0e76837c3bf3ab9accbb9ee2bcb",
  "summary": "The selected rerun works for a bare pytest command, but it breaks Check for the unit host entry wrapped in `clutch coverage gate` and stops quarantine release whenever a rerun happens.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/stages.py",
      "line": 1295,
      "message": "The rerun appends `--clutch-select` to `entry.argv` and runs only the failed ids. config.yaml's unit entry is `clutch coverage gate -- ... pytest ...`. After that command exits 0, `run_gate` (clutch/covgate.py:140-164) checks repository and per-file coverage thresholds. A run of one test cannot meet them, so the gate exits nonzero even when the flaky test passes. Line 1342 `if result.rc != 0 and \"failed\" not in last.values(): findings.extend(report.findings)` then adds the rerun's command-failure finding, so every flaky unit test now fails Check. It used to be classified as a flake, which breaks the ticket's promise that flake detection is unchanged.",
      "paved_road": "In stages.py, judge a selected rerun by its recorded outcomes, not by the wrapper's exit code. If every selected id is recorded and none failed, do not add the rerun command's rc findings. If any selected id is missing from the rerun results, return invalid() or add a finding. Add a test where the rerun records the selected id as passed but exits nonzero, and assert the test is classified as flaky with no extra finding.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/stages.py",
      "line": 1295,
      "message": "Once the rerun is selected, `last` holds only the first run's failed ids. The quarantine-release loop after the rerun block (`for identity in flake.quarantine().active.values(): if last.get(identity.test_id) != \"passed\": continue`) used to see every test's rerun outcome. Now, when any test fails and triggers a rerun, a quarantined test that passed is missing from `last`, so its release is silently skipped. Before this change it would have been released. That changes quarantine behavior, which the ticket's boundary contract says stays unchanged.",
      "paved_road": "For the release check, merge the outcomes, e.g. `outcomes = {**first, **last}`, and test `outcomes.get(identity.test_id) != \"passed\"`. Keep `last` (only the rerun results) for the flaky and `failed on rerun` logic. Add a test that a passing quarantined test with a merged fix is still released when an unrelated test triggers a rerun.",
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
