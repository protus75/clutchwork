# Review: snag

The serve change is correct and fixes the prior duplicate `serve_failed` finding, but the shutdown-wait half of criterion 5 rests on a single `asyncio.sleep(0)` check that passes even without `wait_driver`, so it cannot fail.

## Findings

- [logic] tests/integration/test_serve_driver_overlap.py:98 In `test_one_pass_at_a_time_and_shutdown_waits`, the test calls `rig.owner.stop()`, yields once with `await asyncio.sleep(0)`, then asserts `not run.done()`. One event-loop tick is not enough for `Serve.run` to wake from its `asyncio.wait`, leave the loop, run cleanup and return, so the assertion holds even if `run` never waits for the pass. Releasing the pass afterwards and asserting a return code of 0 also passes without the wait. The test therefore cannot fail, and criterion 5's 'a stop requested while a pass is blocked does not let `Serve.run` return until the pass is released' is not checked. (do instead: After `rig.owner.stop()`, wait until `run` has demonstrably reached the shutdown wait, for example `await until(rig, lambda: rig.owner.driver_task is None)` (`wait_driver` clears the task before awaiting it), then assert `not run.done()` and that the driver task has not finished before setting `release_second`. Only then await `run` and assert it returns 0.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "991b1d764b2d5b7071bc9a805c063e473301f5fb",
  "stem": "dispatch-during-driver-pass",
  "reviewed_sha": "991b1d764b2d5b7071bc9a805c063e473301f5fb",
  "summary": "The serve change is correct and fixes the prior duplicate `serve_failed` finding, but the shutdown-wait half of criterion 5 rests on a single `asyncio.sleep(0)` check that passes even without `wait_driver`, so it cannot fail.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/integration/test_serve_driver_overlap.py",
      "line": 98,
      "message": "In `test_one_pass_at_a_time_and_shutdown_waits`, the test calls `rig.owner.stop()`, yields once with `await asyncio.sleep(0)`, then asserts `not run.done()`. One event-loop tick is not enough for `Serve.run` to wake from its `asyncio.wait`, leave the loop, run cleanup and return, so the assertion holds even if `run` never waits for the pass. Releasing the pass afterwards and asserting a return code of 0 also passes without the wait. The test therefore cannot fail, and criterion 5's 'a stop requested while a pass is blocked does not let `Serve.run` return until the pass is released' is not checked.",
      "paved_road": "After `rig.owner.stop()`, wait until `run` has demonstrably reached the shutdown wait, for example `await until(rig, lambda: rig.owner.driver_task is None)` (`wait_driver` clears the task before awaiting it), then assert `not run.done()` and that the driver task has not finished before setting `release_second`. Only then await `run` and assert it returns 0.",
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
