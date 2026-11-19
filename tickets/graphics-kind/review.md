# Review: snag

The diff covers criteria 1-10, but the new Goal / Why exemption also lets graphics tickets in command mode skip the required section with no finding.

## Findings

- [logic] clutch/tickets.py:408 The required-section loop now skips the empty-body check for `## Goal / Why` on every `kind: graphics` ticket. The only replacement check is the lint rule 'generate render has no input or prompt', which runs only when `mode: generate`. So a `mode: command` graphics ticket with an empty `## Goal / Why` parses and lints with no finding. That is an unrequested loosening of a required section. The ticket only asks that a generate ticket with no input and no prompt yield a finding (criterion 7). (do instead: Skip the empty Goal / Why parse check only for generate-mode Render blocks, or keep the parse-time requirement for command mode (for example, check the parsed Render mode before skipping). Add a test that an empty Goal / Why on a `mode: command` graphics ticket still raises `TicketInvalid` or yields a finding.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "48992052fc053dea21141087cc6de190a7978079",
  "stem": "graphics-kind",
  "reviewed_sha": "48992052fc053dea21141087cc6de190a7978079",
  "summary": "The diff covers criteria 1-10, but the new Goal / Why exemption also lets graphics tickets in command mode skip the required section with no finding.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/tickets.py",
      "line": 408,
      "message": "The required-section loop now skips the empty-body check for `## Goal / Why` on every `kind: graphics` ticket. The only replacement check is the lint rule 'generate render has no input or prompt', which runs only when `mode: generate`. So a `mode: command` graphics ticket with an empty `## Goal / Why` parses and lints with no finding. That is an unrequested loosening of a required section. The ticket only asks that a generate ticket with no input and no prompt yield a finding (criterion 7).",
      "paved_road": "Skip the empty Goal / Why parse check only for generate-mode Render blocks, or keep the parse-time requirement for command mode (for example, check the parsed Render mode before skipping). Add a test that an empty Goal / Why on a `mode: command` graphics ticket still raises `TicketInvalid` or yields a finding.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
