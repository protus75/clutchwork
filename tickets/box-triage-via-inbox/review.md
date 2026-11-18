# Review: snag

The request kind, CLI submission, idle-point wiring, docs and prompt changes all match the ticket, but `settle_triage` drops accepted requests from any earlier lifecycle, so a request the CLI reported as submitted can be lost silently after a restart or handoff.

## Findings

- [logic] clutch/control.py:319 `settle_triage` skips every accepted decision whose `lifecycle_id` differs from `self.lifecycle_id`. Each drain or serve process builds a fresh uuid lifecycle (`build_control`), including after a crash restart or a self-upgrade re-exec handoff. So a triage request that `consume` accepted and journaled before the process ended, but that never reached an idle point, is never applied: the operator was told `triage submitted: <id>` and the pass never runs. The ticket says settle mirrors `settle_admissions` (which applies accepted requests regardless of lifecycle) and relies on the `triage/<request_id>` Effects key so that 'a repeated settle or a restart never runs it twice'. That wording assumes an accepted, unapplied request survives a restart. Lifecycle staleness is already enforced at `consume`, which journals requests from other lifecycles as `stale`, so the extra filter only drops valid accepted work. (do instead: Drop the `body["lifecycle_id"] != self.lifecycle_id` condition in `settle_triage`, as `settle_admissions` does, and let the `triage/<request_id>` effect key give once-only application. Add a unit case where a decision accepted under lifecycle `old` is settled exactly once by an inbox whose lifecycle is `live`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "2a38bfb4e01dd1b37a71627b364261522f98e8c1",
  "stem": "box-triage-via-inbox",
  "reviewed_sha": "2a38bfb4e01dd1b37a71627b364261522f98e8c1",
  "summary": "The request kind, CLI submission, idle-point wiring, docs and prompt changes all match the ticket, but `settle_triage` drops accepted requests from any earlier lifecycle, so a request the CLI reported as submitted can be lost silently after a restart or handoff.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/control.py",
      "line": 319,
      "message": "`settle_triage` skips every accepted decision whose `lifecycle_id` differs from `self.lifecycle_id`. Each drain or serve process builds a fresh uuid lifecycle (`build_control`), including after a crash restart or a self-upgrade re-exec handoff. So a triage request that `consume` accepted and journaled before the process ended, but that never reached an idle point, is never applied: the operator was told `triage submitted: <id>` and the pass never runs. The ticket says settle mirrors `settle_admissions` (which applies accepted requests regardless of lifecycle) and relies on the `triage/<request_id>` Effects key so that 'a repeated settle or a restart never runs it twice'. That wording assumes an accepted, unapplied request survives a restart. Lifecycle staleness is already enforced at `consume`, which journals requests from other lifecycles as `stale`, so the extra filter only drops valid accepted work.",
      "paved_road": "Drop the `body[\"lifecycle_id\"] != self.lifecycle_id` condition in `settle_triage`, as `settle_admissions` does, and let the `triage/<request_id>` effect key give once-only application. Add a unit case where a decision accepted under lifecycle `old` is settled exactly once by an inbox whose lifecycle is `live`.",
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
