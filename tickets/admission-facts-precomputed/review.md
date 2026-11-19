# Review: approve

The diff adds `AdmissionFacts`/`admission_facts` as the contract specifies, moves all seven admissions and every in-repo caller (including the `MENU` tables, `ticket_menu_inputs`, `_review`/`_lint`/`_order`, and `verdict_locked`/`_admit`) to facts with outcomes unchanged (the `interrupted` overlay matches the old appended-`abandoned` behavior in `reject_queue`), and adds reference-copy parity, no-recompute and shared-facts tests that cover every acceptance criterion within the fence.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4629dc0f59250fb672a0a18665bc8a2ce7bbf636",
  "stem": "admission-facts-precomputed",
  "reviewed_sha": "4629dc0f59250fb672a0a18665bc8a2ce7bbf636",
  "summary": "The diff adds `AdmissionFacts`/`admission_facts` as the contract specifies, moves all seven admissions and every in-repo caller (including the `MENU` tables, `ticket_menu_inputs`, `_review`/`_lint`/`_order`, and `verdict_locked`/`_admit`) to facts with outcomes unchanged (the `interrupted` overlay matches the old appended-`abandoned` behavior in `reject_queue`), and adds reference-copy parity, no-recompute and shared-facts tests that cover every acceptance criterion within the fence.",
  "findings": [],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
