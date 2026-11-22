# Review: snag

The engine, roadmap, release-ship and doc changes match the ticket, but the edited plan-ticket-drain prompt test still requires the removed `clutch release bump --minor` phrase, so criteria 6 and 8 cannot pass.

## Findings

- [acceptance] tests/integration/test_ask_plan_drain.py:44 `test_plan_ticket_drain_prompt_content` still lists "clutch release bump --minor" among the phrases that must be present. The diff deletes the only place that phrase appeared in clutch/specs/ask/plan-ticket-drain.md, the Before you start bullet. The new Closing text says only "never run `clutch release bump`, ...", with no `--minor`. The assertion therefore fails, so `./dev.py test tests/integration/test_ask_plan_drain.py` (criterion 6) and the full suite (criterion 8) fail. Criterion 6 also forbids any instruction to run `clutch release bump`, so pinning that phrase works against the ticket. (do instead: Remove "clutch release bump --minor" from the required-phrase list in this test. Optionally assert that the rendered prompt has no instruction to run `clutch release bump --minor`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "6a80b410b70409b696591c1f79793616cfe0628c",
  "stem": "serve-no-roadmap",
  "reviewed_sha": "6a80b410b70409b696591c1f79793616cfe0628c",
  "summary": "The engine, roadmap, release-ship and doc changes match the ticket, but the edited plan-ticket-drain prompt test still requires the removed `clutch release bump --minor` phrase, so criteria 6 and 8 cannot pass.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/integration/test_ask_plan_drain.py",
      "line": 44,
      "message": "`test_plan_ticket_drain_prompt_content` still lists \"clutch release bump --minor\" among the phrases that must be present. The diff deletes the only place that phrase appeared in clutch/specs/ask/plan-ticket-drain.md, the Before you start bullet. The new Closing text says only \"never run `clutch release bump`, ...\", with no `--minor`. The assertion therefore fails, so `./dev.py test tests/integration/test_ask_plan_drain.py` (criterion 6) and the full suite (criterion 8) fail. Criterion 6 also forbids any instruction to run `clutch release bump`, so pinning that phrase works against the ticket.",
      "paved_road": "Remove \"clutch release bump --minor\" from the required-phrase list in this test. Optionally assert that the rendered prompt has no instruction to run `clutch release bump --minor`.",
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
