# Review: snag

The rename and driver subject validation are correct, but one fenced test still reads the removed `LLMRequest.ticket` field, so the full suite (criterion 6) will fail.

## Findings

- [acceptance] clutch/llm.py:21 The rename of `ticket` to `subject` breaks `tests/integration/test_triage.py:81`, a fenced file the diff leaves unchanged. That line still runs `[(r.surface, r.tier, r.ticket) for r in llm.requests]` and expects `None` for every request. `LLMRequest` no longer has a `ticket` attribute, so the test raises AttributeError. The expected values are also stale: the triage and author requests now carry `message.id`, and requisition_review carries the authored stem. The new scan in `test_llm_request_subject.py` only matches `req`/`request`, so it misses this `r.ticket` read. Criterion 6 (`./dev.py test` passes on the full suite) is therefore unmet. (do instead: In tests/integration/test_triage.py, change `r.ticket` to `r.subject` and update the expected tuples to the labels the code now sends: each triage message's id, the authoring message's id for author, and the authored ticket stem for requisition_review.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "5fe62d637ac75fed55b72d98945da1a32332c903",
  "stem": "llm-request-subject",
  "reviewed_sha": "5fe62d637ac75fed55b72d98945da1a32332c903",
  "summary": "The rename and driver subject validation are correct, but one fenced test still reads the removed `LLMRequest.ticket` field, so the full suite (criterion 6) will fail.",
  "findings": [
    {
      "code": "acceptance",
      "path": "clutch/llm.py",
      "line": 21,
      "message": "The rename of `ticket` to `subject` breaks `tests/integration/test_triage.py:81`, a fenced file the diff leaves unchanged. That line still runs `[(r.surface, r.tier, r.ticket) for r in llm.requests]` and expects `None` for every request. `LLMRequest` no longer has a `ticket` attribute, so the test raises AttributeError. The expected values are also stale: the triage and author requests now carry `message.id`, and requisition_review carries the authored stem. The new scan in `test_llm_request_subject.py` only matches `req`/`request`, so it misses this `r.ticket` read. Criterion 6 (`./dev.py test` passes on the full suite) is therefore unmet.",
      "paved_road": "In tests/integration/test_triage.py, change `r.ticket` to `r.subject` and update the expected tuples to the labels the code now sends: each triage message's id, the authoring message's id for author, and the authored ticket stem for requisition_review.",
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
