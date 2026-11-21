# Review: snag

The store and `capture_key` code meet the ticket, but the refused-key test wraps `put_capture` around `capture_key`, so several of the criterion-4 cases would still pass if `capture_key` returned a key instead of raising.

## Findings

- [logic] tests/unit/test_evidence_capture_keys.py:50 `with pytest.raises(ValueError): store.put_capture(*capture_key(slot, attempt, name), b"payload")` passes whether `capture_key` raises or `put_capture` refuses the key it returned. For refused-attempt (`-1`, `True`, `"0"`) and refused-spool-stem (`""`, `"/8"`, `"Work/1"`), the store's own validation would also raise. So the test cannot fail if `capture_key` stopped refusing these inputs and returned a key. Criterion 4 requires each refused outcome to raise from `capture_key`, "not a returned key". (do instead: Call `capture_key(slot, attempt, name)` alone inside `pytest.raises(ValueError)`, so the test proves `capture_key` itself refuses. Then assert `not store.fs.files` as before, or drop the store from this test.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "3a0d10ef269e9ebe3662e377223b0d04b6a8c4e8",
  "stem": "spools-capture-keys",
  "reviewed_sha": "3a0d10ef269e9ebe3662e377223b0d04b6a8c4e8",
  "summary": "The store and `capture_key` code meet the ticket, but the refused-key test wraps `put_capture` around `capture_key`, so several of the criterion-4 cases would still pass if `capture_key` returned a key instead of raising.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/unit/test_evidence_capture_keys.py",
      "line": 50,
      "message": "`with pytest.raises(ValueError): store.put_capture(*capture_key(slot, attempt, name), b\"payload\")` passes whether `capture_key` raises or `put_capture` refuses the key it returned. For refused-attempt (`-1`, `True`, `\"0\"`) and refused-spool-stem (`\"\"`, `\"/8\"`, `\"Work/1\"`), the store's own validation would also raise. So the test cannot fail if `capture_key` stopped refusing these inputs and returned a key. Criterion 4 requires each refused outcome to raise from `capture_key`, \"not a returned key\".",
      "paved_road": "Call `capture_key(slot, attempt, name)` alone inside `pytest.raises(ValueError)`, so the test proves `capture_key` itself refuses. Then assert `not store.fs.files` as before, or drop the store from this test.",
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
