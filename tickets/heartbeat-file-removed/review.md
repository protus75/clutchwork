# Review: snag

The heartbeat removal is correct, but both host-contract sentences now end their lists ungrammatically, and the notify restart wait was changed to the ready event instead of a maintenance-call count, which weakens that test.

## Findings

- [acceptance] clutch/docs/host-contract.md:142 Scope in requires dropping "and heartbeat" while "leaving the list grammatical". The sentence now reads "journal, box queue, quarantine ledgers, evidence captures, engine log. Relative paths...", so the list has lost its final "and". (do instead: Change it to "evidence captures and engine log.")
- [acceptance] clutch/docs/host-contract.md:459 Scope in requires the list to stay grammatical. The sentence now reads "State dir owns journal, box queue, quarantine ledgers, evidence captures, engine\nlog.", so the list has no "and" before its last item. (do instead: Change it to "evidence captures and engine log.")
- [acceptance] tests/integration/test_serve_notify.py:82 Scope in says to replace the three heartbeat-file waits in test_serve_notify.py with a wrapper that counts rig.owner.maintenance calls. In the restart half of test_serve_reconciles_notifications_at_startup_and_poll, the old wait needed a new heartbeat mtime, which meant at least one maintenance cycle after restart. The diff waits only for rig.owner.ready.is_set, and ready is set before any maintenance poll runs. The later checks that nothing is redelivered (`notifications.task is None`, 6 deliveries) therefore no longer cover a post-restart maintenance poll and can pass without one. (do instead: After building the restarted owner, wrap its maintenance with count_maintenance(rig, monkeypatch), then wait until ready is set and at least one maintenance cycle has completed before asserting.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e65fe0edafad8ea266b11ab729ed21b761b7046f",
  "stem": "heartbeat-file-removed",
  "reviewed_sha": "e65fe0edafad8ea266b11ab729ed21b761b7046f",
  "summary": "The heartbeat removal is correct, but both host-contract sentences now end their lists ungrammatically, and the notify restart wait was changed to the ready event instead of a maintenance-call count, which weakens that test.",
  "findings": [
    {
      "code": "acceptance",
      "path": "clutch/docs/host-contract.md",
      "line": 142,
      "message": "Scope in requires dropping \"and heartbeat\" while \"leaving the list grammatical\". The sentence now reads \"journal, box queue, quarantine ledgers, evidence captures, engine log. Relative paths...\", so the list has lost its final \"and\".",
      "paved_road": "Change it to \"evidence captures and engine log.\"",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "clutch/docs/host-contract.md",
      "line": 459,
      "message": "Scope in requires the list to stay grammatical. The sentence now reads \"State dir owns journal, box queue, quarantine ledgers, evidence captures, engine\\nlog.\", so the list has no \"and\" before its last item.",
      "paved_road": "Change it to \"evidence captures and engine log.\"",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_serve_notify.py",
      "line": 82,
      "message": "Scope in says to replace the three heartbeat-file waits in test_serve_notify.py with a wrapper that counts rig.owner.maintenance calls. In the restart half of test_serve_reconciles_notifications_at_startup_and_poll, the old wait needed a new heartbeat mtime, which meant at least one maintenance cycle after restart. The diff waits only for rig.owner.ready.is_set, and ready is set before any maintenance poll runs. The later checks that nothing is redelivered (`notifications.task is None`, 6 deliveries) therefore no longer cover a post-restart maintenance poll and can pass without one.",
      "paved_road": "After building the restarted owner, wrap its maintenance with count_maintenance(rig, monkeypatch), then wait until ready is set and at least one maintenance cycle has completed before asserting.",
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
