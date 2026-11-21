# Review: snag

The one-call review, spec trim, plan-prompt edits, panel accessor removal and test updates are correct, but the new integration test does not prove criterion 5's "no dependents instruction" because it checks a phrase the removed bullet never contained.

## Findings

- [acceptance] tests/integration/test_requisition_brief_check.py:19 Criterion 5 says the test must prove the shipped Task has no "dependents" instruction. The test only checks that the phrase "dependents accounting" is absent. The removed accounting bullet read "Account for every listed dependent exactly once in `dependents`" and never contained that phrase. Only the separately deleted "Redo dependents accounting" sentence did. If the accounting bullet came back, this assertion would still pass, so the dependents half of criterion 5 can't fail. (do instead: Assert that the Task section has neither "Account for every listed dependent" nor "`dependents`". The new "do not search ... dependents" sentence has the bare word but not the backticked field name, so it still passes. Keep the existing "Trace the reference closure" and "grep `tests/`" checks.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "b2eb03ee720a859d29e0c22268d00116a1f0b09a",
  "stem": "requisition-contract-review-comparison",
  "reviewed_sha": "b2eb03ee720a859d29e0c22268d00116a1f0b09a",
  "summary": "The one-call review, spec trim, plan-prompt edits, panel accessor removal and test updates are correct, but the new integration test does not prove criterion 5's \"no dependents instruction\" because it checks a phrase the removed bullet never contained.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/integration/test_requisition_brief_check.py",
      "line": 19,
      "message": "Criterion 5 says the test must prove the shipped Task has no \"dependents\" instruction. The test only checks that the phrase \"dependents accounting\" is absent. The removed accounting bullet read \"Account for every listed dependent exactly once in `dependents`\" and never contained that phrase. Only the separately deleted \"Redo dependents accounting\" sentence did. If the accounting bullet came back, this assertion would still pass, so the dependents half of criterion 5 can't fail.",
      "paved_road": "Assert that the Task section has neither \"Account for every listed dependent\" nor \"`dependents`\". The new \"do not search ... dependents\" sentence has the bare word but not the backticked field name, so it still passes. Keep the existing \"Trace the reference closure\" and \"grep `tests/`\" checks.",
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
