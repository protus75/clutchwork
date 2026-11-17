# Review: snag

The prompt, guide and conduct-file edits meet the ticket, but the diff drops a guard in test_prompt_bounds_box_triage that the change did not require removing.

## Findings

- [logic] tests/integration/test_ask_drain_loop_agent.py:70 The diff removes "never triage or dismiss" from the must-not-appear list. The new drain-loop text says "Never triage or dismiss a `roadmap_row` message" with a capital N, and Python's `in` is case-sensitive, so the old assertion would still pass on the new text. The removal was not needed. It also drops the test's guard against a blanket ban on triage coming back. The ticket's Definition of rejected forbids weakening a test beyond the assertion updates named in Scope in, and this edit goes beyond them. (do instead: Restore the `for phrase in ("never triage or dismiss", "left for the owner"):` not-in assertion. Keep the two added positive phrases, `the tick it appears` and `roadmap_row`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ec2021377dc5b5d520ae08bed67da61662924cf3",
  "stem": "plan-drain-author-in-parallel",
  "reviewed_sha": "ec2021377dc5b5d520ae08bed67da61662924cf3",
  "summary": "The prompt, guide and conduct-file edits meet the ticket, but the diff drops a guard in test_prompt_bounds_box_triage that the change did not require removing.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/integration/test_ask_drain_loop_agent.py",
      "line": 70,
      "message": "The diff removes \"never triage or dismiss\" from the must-not-appear list. The new drain-loop text says \"Never triage or dismiss a `roadmap_row` message\" with a capital N, and Python's `in` is case-sensitive, so the old assertion would still pass on the new text. The removal was not needed. It also drops the test's guard against a blanket ban on triage coming back. The ticket's Definition of rejected forbids weakening a test beyond the assertion updates named in Scope in, and this edit goes beyond them.",
      "paved_road": "Restore the `for phrase in (\"never triage or dismiss\", \"left for the owner\"):` not-in assertion. Keep the two added positive phrases, `the tick it appears` and `roadmap_row`.",
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
