# Review: snag

The serve.py change, the docs edit and the updated existing tests match the ticket, but both new test files carry two `clutch:meta` headers, the reproducer's header was copied from another file, and the tests for criteria 2 and 3 do not fully show what those criteria require.

## Findings

- [acceptance] tests/integration/test_serve_scan_watch_overlap.py:11 This file has two `clutch:meta` headers, at lines 2-9 and again at lines 11-18, and their hashes differ (71f7dd71... and 50f211d0...). Scope in requires the file to start with one header from `clutch meta refresh` with only `purpose` edited by hand. The second block is a stale extra copy that `meta` does not parse as the header. (do instead: Delete the duplicate block at lines 11-18 and run `uv run clutch meta refresh tests/integration/test_serve_scan_watch_overlap.py`, so the file carries exactly one header with a current hash.)
- [acceptance] tests/unit/test_serve_scan_watch_locks.py:11 This file also has two `clutch:meta` headers, at lines 2-9 and lines 11-18, with different hashes (07424e10... and 2cb6fab7...). The extra block is a stale copy left in the module. (do instead: Delete the duplicate block at lines 11-18 and run `uv run clutch meta refresh tests/unit/test_serve_scan_watch_locks.py`.)
- [acceptance] tests/regress_serve_scan_watch_off_exclusive.py:5 The reproducer's header was copied from tests/regress_serve_parallel_admission.py: its purpose reads "Reproduce idle poll blocking parallel admission.", and the docstring calls it an idle scan. The script actually reproduces a changed-snapshot scan entering the exclusive section while a run holds a slot. Scope in requires a header from `clutch meta refresh` with a `purpose` that describes this file. (do instead: Regenerate the header with `uv run clutch meta refresh tests/regress_serve_scan_watch_off_exclusive.py`. Then set `purpose` and the docstring to say a changed scan must not wait on a held run slot.)
- [acceptance] tests/integration/test_serve_scan_watch_overlap.py:63 Criterion 2 requires the stop request made while a run is held to be honored, not dropped. The test only waits until `control.projection.stop_requested` is set. Its `finally` then calls `finish`, which calls `rig.owner.stop()` itself. So serve shutting down is never shown to come from the held-time request: a request that is projected but never acted on would still pass. (do instead: After the request is projected, assert that no new implementation starts. Then set `release` and wait until `run.done()` without calling `owner.stop()`, so serve ends because of the stop request itself. Check the exit code and active.json the way `finish` does.)
- [acceptance] tests/unit/test_serve_scan_watch_locks.py:30 Criterion 3 requires showing `scan` with one run holding a slot. `test_scan_lock_and_stop` runs against the fixture's recording admission and never holds a run slot. So it never shows that a changed scan finishes while a run is held. (do instead: Hold a run slot before the changed scan, either through a real `DaemonAdmission` dispatch blocked on an event or by marking the fixture admission as holding. Then assert that `scan` completes, `owner.entries == []`, and the reads happen under `main_write()`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "eaed50e270579cc3cb68fb8f9e872fd337008cc6",
  "stem": "serve-scan-watch-off-exclusive",
  "reviewed_sha": "eaed50e270579cc3cb68fb8f9e872fd337008cc6",
  "summary": "The serve.py change, the docs edit and the updated existing tests match the ticket, but both new test files carry two `clutch:meta` headers, the reproducer's header was copied from another file, and the tests for criteria 2 and 3 do not fully show what those criteria require.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/integration/test_serve_scan_watch_overlap.py",
      "line": 11,
      "message": "This file has two `clutch:meta` headers, at lines 2-9 and again at lines 11-18, and their hashes differ (71f7dd71... and 50f211d0...). Scope in requires the file to start with one header from `clutch meta refresh` with only `purpose` edited by hand. The second block is a stale extra copy that `meta` does not parse as the header.",
      "paved_road": "Delete the duplicate block at lines 11-18 and run `uv run clutch meta refresh tests/integration/test_serve_scan_watch_overlap.py`, so the file carries exactly one header with a current hash.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_serve_scan_watch_locks.py",
      "line": 11,
      "message": "This file also has two `clutch:meta` headers, at lines 2-9 and lines 11-18, with different hashes (07424e10... and 2cb6fab7...). The extra block is a stale copy left in the module.",
      "paved_road": "Delete the duplicate block at lines 11-18 and run `uv run clutch meta refresh tests/unit/test_serve_scan_watch_locks.py`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/regress_serve_scan_watch_off_exclusive.py",
      "line": 5,
      "message": "The reproducer's header was copied from tests/regress_serve_parallel_admission.py: its purpose reads \"Reproduce idle poll blocking parallel admission.\", and the docstring calls it an idle scan. The script actually reproduces a changed-snapshot scan entering the exclusive section while a run holds a slot. Scope in requires a header from `clutch meta refresh` with a `purpose` that describes this file.",
      "paved_road": "Regenerate the header with `uv run clutch meta refresh tests/regress_serve_scan_watch_off_exclusive.py`. Then set `purpose` and the docstring to say a changed scan must not wait on a held run slot.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_serve_scan_watch_overlap.py",
      "line": 63,
      "message": "Criterion 2 requires the stop request made while a run is held to be honored, not dropped. The test only waits until `control.projection.stop_requested` is set. Its `finally` then calls `finish`, which calls `rig.owner.stop()` itself. So serve shutting down is never shown to come from the held-time request: a request that is projected but never acted on would still pass.",
      "paved_road": "After the request is projected, assert that no new implementation starts. Then set `release` and wait until `run.done()` without calling `owner.stop()`, so serve ends because of the stop request itself. Check the exit code and active.json the way `finish` does.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_serve_scan_watch_locks.py",
      "line": 30,
      "message": "Criterion 3 requires showing `scan` with one run holding a slot. `test_scan_lock_and_stop` runs against the fixture's recording admission and never holds a run slot. So it never shows that a changed scan finishes while a run is held.",
      "paved_road": "Hold a run slot before the changed scan, either through a real `DaemonAdmission` dispatch blocked on an event or by marking the fixture admission as holding. Then assert that `scan` completes, `owner.entries == []`, and the reads happen under `main_write()`.",
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
