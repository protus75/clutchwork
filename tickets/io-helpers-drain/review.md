# Review: snag

The helper module and the import rewrites match the ticket, but 25 importer files also hand-edit their clutch:meta `purpose` and/or `owner` lines; `clutch/meta.py` refresh never makes those changes, and the ticket allows importers to change only their import line.

## Findings

- [scope] tests/integration/test_harvest.py:5 The importer rewrites its meta `purpose` text (line 5) and changes `owner: engine` to `owner: clutch/runner.py` (line 7). The ticket allows only the import line to change, and `clutch/meta.py` refresh rewrites only `verified` and `hash` for a non-empty owner. (do instead: Restore the original `purpose` and `owner` lines; keep only the import change and the regenerated `verified`/`hash`.)
- [scope] tests/integration/test_hot_paths_snapshot.py:4 The importer rewrites `purpose` (line 4) and changes `owner: engine` to `clutch/observe.py` (line 6), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)
- [scope] tests/integration/test_inbox.py:5 The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/inbox.py` (line 7), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)
- [scope] tests/integration/test_intake_keeps_draft.py:4 The importer rewrites `purpose` (line 4) and changes `owner: engine` to `clutch/tickets.py` (line 6), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)
- [scope] tests/integration/test_intake_scope.py:4 The importer rewrites `purpose` (line 4) and changes `owner: engine` to `clutch/tickets.py` (line 6), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)
- [scope] tests/integration/test_kill_cli_activation.py:5 The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/control.py` (line 7), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)
- [scope] tests/integration/test_ladder.py:5 The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/caps.py` (line 7), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)
- [scope] tests/integration/test_merge.py:5 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_open_tickets_closed.py:4 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_paved_roads.py:4 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_requisition_gate.py:5 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_requisition_identity_record.py:5 The importer rewrites its meta `purpose` line and drops '64-hex' from it, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_retro.py:5 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_retro_box.py:5 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_review_command.py:5 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_roadmap_start_gates.py:4 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_scorecard.py:7 The importer changes `owner: engine` to `clutch/scorecard.py`, which is outside its import line. (do instead: Restore `owner: engine`.)
- [scope] tests/integration/test_snapshot_cache_facts.py:6 The importer changes `owner: engine` to `clutch/observe.py`, which is outside its import line. (do instead: Restore `owner: engine`.)
- [scope] tests/integration/test_snapshot_merged_cap.py:4 The importer rewrites its meta `purpose` line, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/integration/test_ticket_write_serialization.py:4 The importer rewrites its meta `purpose` line and drops the failed-edit lock-release clause, which is outside its import line. (do instead: Restore the original `purpose` line.)
- [scope] tests/regress_drain_detach.py:7 The importer changes `owner: engine` to `clutch/__main__.py`, which is outside its import line. (do instead: Restore `owner: engine`.)
- [scope] tests/regress_drain_park_findings.py:7 The importer changes `owner: engine` to `clutch/__main__.py`, which is outside its import line. (do instead: Restore `owner: engine`.)
- [scope] tests/regress_drain_signals.py:7 The importer changes `owner: engine` to `clutch/__main__.py`, which is outside its import line. (do instead: Restore `owner: engine`.)
- [scope] tests/regress_stale_running.py:5 The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/runner.py` (line 7), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)
- [scope] tests/snapshot_scale_fixture.py:5 The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/observe.py` (line 7), which is outside its import line. (do instead: Restore the original `purpose` and `owner` lines.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ea34ad05835f4ead1e6703a0e7b4a73fc5ccf2d4",
  "stem": "io-helpers-drain",
  "reviewed_sha": "ea34ad05835f4ead1e6703a0e7b4a73fc5ccf2d4",
  "summary": "The helper module and the import rewrites match the ticket, but 25 importer files also hand-edit their clutch:meta `purpose` and/or `owner` lines; `clutch/meta.py` refresh never makes those changes, and the ticket allows importers to change only their import line.",
  "findings": [
    {
      "code": "scope",
      "path": "tests/integration/test_harvest.py",
      "line": 5,
      "message": "The importer rewrites its meta `purpose` text (line 5) and changes `owner: engine` to `owner: clutch/runner.py` (line 7). The ticket allows only the import line to change, and `clutch/meta.py` refresh rewrites only `verified` and `hash` for a non-empty owner.",
      "paved_road": "Restore the original `purpose` and `owner` lines; keep only the import change and the regenerated `verified`/`hash`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_hot_paths_snapshot.py",
      "line": 4,
      "message": "The importer rewrites `purpose` (line 4) and changes `owner: engine` to `clutch/observe.py` (line 6), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_inbox.py",
      "line": 5,
      "message": "The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/inbox.py` (line 7), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_intake_keeps_draft.py",
      "line": 4,
      "message": "The importer rewrites `purpose` (line 4) and changes `owner: engine` to `clutch/tickets.py` (line 6), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_intake_scope.py",
      "line": 4,
      "message": "The importer rewrites `purpose` (line 4) and changes `owner: engine` to `clutch/tickets.py` (line 6), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_kill_cli_activation.py",
      "line": 5,
      "message": "The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/control.py` (line 7), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ladder.py",
      "line": 5,
      "message": "The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/caps.py` (line 7), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_merge.py",
      "line": 5,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_open_tickets_closed.py",
      "line": 4,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_paved_roads.py",
      "line": 4,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_requisition_gate.py",
      "line": 5,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_requisition_identity_record.py",
      "line": 5,
      "message": "The importer rewrites its meta `purpose` line and drops '64-hex' from it, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_retro.py",
      "line": 5,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_retro_box.py",
      "line": 5,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_review_command.py",
      "line": 5,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_roadmap_start_gates.py",
      "line": 4,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_scorecard.py",
      "line": 7,
      "message": "The importer changes `owner: engine` to `clutch/scorecard.py`, which is outside its import line.",
      "paved_road": "Restore `owner: engine`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_snapshot_cache_facts.py",
      "line": 6,
      "message": "The importer changes `owner: engine` to `clutch/observe.py`, which is outside its import line.",
      "paved_road": "Restore `owner: engine`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_snapshot_merged_cap.py",
      "line": 4,
      "message": "The importer rewrites its meta `purpose` line, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/integration/test_ticket_write_serialization.py",
      "line": 4,
      "message": "The importer rewrites its meta `purpose` line and drops the failed-edit lock-release clause, which is outside its import line.",
      "paved_road": "Restore the original `purpose` line.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/regress_drain_detach.py",
      "line": 7,
      "message": "The importer changes `owner: engine` to `clutch/__main__.py`, which is outside its import line.",
      "paved_road": "Restore `owner: engine`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/regress_drain_park_findings.py",
      "line": 7,
      "message": "The importer changes `owner: engine` to `clutch/__main__.py`, which is outside its import line.",
      "paved_road": "Restore `owner: engine`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/regress_drain_signals.py",
      "line": 7,
      "message": "The importer changes `owner: engine` to `clutch/__main__.py`, which is outside its import line.",
      "paved_road": "Restore `owner: engine`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/regress_stale_running.py",
      "line": 5,
      "message": "The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/runner.py` (line 7), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
      "kind": null,
      "unit": null
    },
    {
      "code": "scope",
      "path": "tests/snapshot_scale_fixture.py",
      "line": 5,
      "message": "The importer rewrites `purpose` (line 5) and changes `owner: engine` to `clutch/observe.py` (line 7), which is outside its import line.",
      "paved_road": "Restore the original `purpose` and `owner` lines.",
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
