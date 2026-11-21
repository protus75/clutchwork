# Review: snag

The production changes in requisition.py, driver.py, panel.py and rework.py implement every outcome in the ticket correctly, but the tests for criteria 1 and 4 check only some of the exact values those criteria require.

## Findings

- [acceptance] tests/unit/test_requisition_panel.py:98 Criterion 1 requires the size-0 and size-1 runs to record exactly the expected values written out in the test: the full `llm_call` keyword arguments, the `begin_watch` arguments and the returned `RequisitionVerdict`. `test_single` checks only `(run_seq, call_seq)` pairs, the spool names, verdict/calls and the watch count. A regression in the other `llm_call` keywords (ticket, stem, attempt, the request surface) or in the `begin_watch` arguments on the unchanged path would pass this test. (do instead: Assert the full recorded `llm_call` kwargs (excluding only the opaque effects/llm/redactor objects, or compare them to the stand-ins), the full `begin_watch` kwargs dict, and the stage_start/stage_end event payloads as exact expected values.)
- [acceptance] tests/unit/test_requisition_panel.py:120 Criterion 4 requires the `panel_facts` event of the snag/approve case to equal the worked example exactly. The test checks only member_count, verdict_counts, agreement_kind, merged agreement/members and dropped. It never checks `combiner == "findings-union"`, `kept_index is None`, the `members` entries, or the event_context fields (`stem`, `attempt`, `run_seq`, `surface="requisition_review"`) that the ticket says the event carries. (do instead: Compare the whole `panel_facts` kwargs dict against an exact expected dict built from the worked example, including combiner, kept_index, members and the stem/attempt/run_seq/surface context.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "cedb74ca0a02eafb4db833772418ca4818fad910",
  "stem": "review-panel-stage-use-requisition",
  "reviewed_sha": "cedb74ca0a02eafb4db833772418ca4818fad910",
  "summary": "The production changes in requisition.py, driver.py, panel.py and rework.py implement every outcome in the ticket correctly, but the tests for criteria 1 and 4 check only some of the exact values those criteria require.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_requisition_panel.py",
      "line": 98,
      "message": "Criterion 1 requires the size-0 and size-1 runs to record exactly the expected values written out in the test: the full `llm_call` keyword arguments, the `begin_watch` arguments and the returned `RequisitionVerdict`. `test_single` checks only `(run_seq, call_seq)` pairs, the spool names, verdict/calls and the watch count. A regression in the other `llm_call` keywords (ticket, stem, attempt, the request surface) or in the `begin_watch` arguments on the unchanged path would pass this test.",
      "paved_road": "Assert the full recorded `llm_call` kwargs (excluding only the opaque effects/llm/redactor objects, or compare them to the stand-ins), the full `begin_watch` kwargs dict, and the stage_start/stage_end event payloads as exact expected values.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_requisition_panel.py",
      "line": 120,
      "message": "Criterion 4 requires the `panel_facts` event of the snag/approve case to equal the worked example exactly. The test checks only member_count, verdict_counts, agreement_kind, merged agreement/members and dropped. It never checks `combiner == \"findings-union\"`, `kept_index is None`, the `members` entries, or the event_context fields (`stem`, `attempt`, `run_seq`, `surface=\"requisition_review\"`) that the ticket says the event carries.",
      "paved_road": "Compare the whole `panel_facts` kwargs dict against an exact expected dict built from the worked example, including combiner, kept_index, members and the stem/attempt/run_seq/surface context.",
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
