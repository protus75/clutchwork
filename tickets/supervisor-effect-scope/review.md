# Review: snag

The scoping is implemented correctly and unscoped keys are unchanged, but the Driver test does not check the journal `run_seq` part of acceptance criterion 8.

## Findings

- [acceptance] tests/unit/test_key_scope.py:67 Acceptance criterion 8 requires `tests/unit/test_key_scope.py` to check that the journal `run_seq` stays the integer `<seq>` in both the scoped and unscoped `Driver.run` calls. `test_driver_scoped_effect_and_integer_sequence` only checks the `effect_completion` keys. It never reads the `run_seq` field on the journaled stage events (`Driver._run` passes `run_seq=seq` to `self.stage(...)`). A change that put `key_seq` into the journal would still pass this test. (do instead: After `asyncio.run(run())`, read the journal events for the two stage runs that carry `run_seq` and assert that each one is the int `0` (`type(...) is int` and `== 0`), not `"sup-0"`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ecbb2e26343c810c3c7d7dffb99077806bdbf8aa",
  "stem": "supervisor-effect-scope",
  "reviewed_sha": "ecbb2e26343c810c3c7d7dffb99077806bdbf8aa",
  "summary": "The scoping is implemented correctly and unscoped keys are unchanged, but the Driver test does not check the journal `run_seq` part of acceptance criterion 8.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_key_scope.py",
      "line": 67,
      "message": "Acceptance criterion 8 requires `tests/unit/test_key_scope.py` to check that the journal `run_seq` stays the integer `<seq>` in both the scoped and unscoped `Driver.run` calls. `test_driver_scoped_effect_and_integer_sequence` only checks the `effect_completion` keys. It never reads the `run_seq` field on the journaled stage events (`Driver._run` passes `run_seq=seq` to `self.stage(...)`). A change that put `key_seq` into the journal would still pass this test.",
      "paved_road": "After `asyncio.run(run())`, read the journal events for the two stage runs that carry `run_seq` and assert that each one is the int `0` (`type(...) is int` and `== 0`), not `\"sup-0\"`.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
