# Review: snag

The diff does what the ticket asks and cites only real MCP tool names and CLI flags, but in plan-ticket-serve.md the reworded line about a wedging pending message now stops the serve daemon without restarting it and names no stop tool.

## Findings

- [logic] clutch/specs/ask/plan-ticket-serve.md:35 The old line was "run `clutch engine stop` (the running ticket finishes first), take the message through the no-engine Suggestion Box step, then start serve again". The new line is "stop the engine and report it; follow the phase-end triage cadence unless the owner explicitly asks otherwise". It drops the restart, so an unattended run that hits a wedging message leaves the daemon stopped. Nothing else in the prompt restarts it, since the only restart rule is tied to the Reject-queue edit, dismiss and doctor steps. The run is also unattended ('nothing waits for a person'), so it may never recover. The line also names no stop path, unlike every other stop in the diff, which says `clutch_engine_control(action="stop")` or `clutch engine stop`. The ticket's scope covers the triage cadence, not dropping the restart. (do instead: Keep the stop-then-restart order and name both paths. For example: 'For a pending message whose cause wedges the engine or wastes runs, run `clutch_engine_control(action="stop")` or `clutch engine stop` (the running ticket finishes first), take that message through the no-engine Suggestion Box step as an exception to the phase-end triage cadence, then start serve again with `clutch_engine_start(mode="serve")` or `clutch engine serve --detach`.')

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ddfa9b799b83e1f3709a1bd76a41b1c5ef1b161e",
  "stem": "ask-specs-mcp-supervision",
  "reviewed_sha": "ddfa9b799b83e1f3709a1bd76a41b1c5ef1b161e",
  "summary": "The diff does what the ticket asks and cites only real MCP tool names and CLI flags, but in plan-ticket-serve.md the reworded line about a wedging pending message now stops the serve daemon without restarting it and names no stop tool.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/specs/ask/plan-ticket-serve.md",
      "line": 35,
      "message": "The old line was \"run `clutch engine stop` (the running ticket finishes first), take the message through the no-engine Suggestion Box step, then start serve again\". The new line is \"stop the engine and report it; follow the phase-end triage cadence unless the owner explicitly asks otherwise\". It drops the restart, so an unattended run that hits a wedging message leaves the daemon stopped. Nothing else in the prompt restarts it, since the only restart rule is tied to the Reject-queue edit, dismiss and doctor steps. The run is also unattended ('nothing waits for a person'), so it may never recover. The line also names no stop path, unlike every other stop in the diff, which says `clutch_engine_control(action=\"stop\")` or `clutch engine stop`. The ticket's scope covers the triage cadence, not dropping the restart.",
      "paved_road": "Keep the stop-then-restart order and name both paths. For example: 'For a pending message whose cause wedges the engine or wastes runs, run `clutch_engine_control(action=\"stop\")` or `clutch engine stop` (the running ticket finishes first), take that message through the no-engine Suggestion Box step as an exception to the phase-end triage cadence, then start serve again with `clutch_engine_start(mode=\"serve\")` or `clutch engine serve --detach`.'",
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
