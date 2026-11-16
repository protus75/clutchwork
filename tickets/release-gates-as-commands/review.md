# Review: snag

The implementation, docs and gate blocks match the ticket, but test_run_gate_refusals checks for no exec calls and an empty journal only in the unknown-release case, not in the missing-roadmap case that criterion 5 also requires.

## Findings

- [acceptance] tests/unit/test_roadmap_gate.py:96 Acceptance criterion 5 says that in both refusal cases (no docs/roadmap.md, and unknown release 9.9.9) the fake exec records no call and the journal is empty. The test reassigns `c` at this line before asserting, so the missing-roadmap checkout's `exec_.calls` and `journal.events` are never checked. Only the unknown-release case is pinned. (do instead: Assert `c.exec_.calls == [] and c.journal.events == []` right after the missing-roadmap `pytest.raises` block, before `c` is reassigned to the second checkout.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "672a76b00ffd04f8132350bda0dd7b687a6d32dd",
  "stem": "release-gates-as-commands",
  "reviewed_sha": "672a76b00ffd04f8132350bda0dd7b687a6d32dd",
  "summary": "The implementation, docs and gate blocks match the ticket, but test_run_gate_refusals checks for no exec calls and an empty journal only in the unknown-release case, not in the missing-roadmap case that criterion 5 also requires.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_roadmap_gate.py",
      "line": 96,
      "message": "Acceptance criterion 5 says that in both refusal cases (no docs/roadmap.md, and unknown release 9.9.9) the fake exec records no call and the journal is empty. The test reassigns `c` at this line before asserting, so the missing-roadmap checkout's `exec_.calls` and `journal.events` are never checked. Only the unknown-release case is pinned.",
      "paved_road": "Assert `c.exec_.calls == [] and c.journal.events == []` right after the missing-roadmap `pytest.raises` block, before `c` is reassigned to the second checkout.",
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
