# Review: snag

The overlap change is correct and the tests cover it, but a driver pass that fails while serve's main loop is running logs `serve_failed` twice.

## Findings

- [logic] clutch/serve.py:672 When a pass fails while the main loop is running, the loop calls `self.driver_task.result()`, which raises before `self.driver_task = None` runs. The except branch then logs `serve_failed` and sets the code. Because the task is never cleared, the new `wait_driver()` awaits the same finished task, gets the same exception back, and logs `serve_failed` a second time for one failure. The `shutdown=False` case of `test_pass_failure_stops_serve` takes this path but only checks that at least one `serve_failed` event exists, so it does not catch the duplicate. (do instead: In the loop, clear the task before reading its result, for example `task, self.driver_task = self.driver_task, None; task.result()`, so `wait_driver()` only reports a failure that surfaces at the shutdown wait. Make the integration test assert exactly one `serve_failed` event in both parametrized cases.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "ff6f9ebefab7d26ff2d4d4ab66706bc661567382",
  "stem": "dispatch-during-driver-pass",
  "reviewed_sha": "ff6f9ebefab7d26ff2d4d4ab66706bc661567382",
  "summary": "The overlap change is correct and the tests cover it, but a driver pass that fails while serve's main loop is running logs `serve_failed` twice.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/serve.py",
      "line": 672,
      "message": "When a pass fails while the main loop is running, the loop calls `self.driver_task.result()`, which raises before `self.driver_task = None` runs. The except branch then logs `serve_failed` and sets the code. Because the task is never cleared, the new `wait_driver()` awaits the same finished task, gets the same exception back, and logs `serve_failed` a second time for one failure. The `shutdown=False` case of `test_pass_failure_stops_serve` takes this path but only checks that at least one `serve_failed` event exists, so it does not catch the duplicate.",
      "paved_road": "In the loop, clear the task before reading its result, for example `task, self.driver_task = self.driver_task, None; task.result()`, so `wait_driver()` only reports a failure that surfaces at the shutdown wait. Make the integration test assert exactly one `serve_failed` event in both parametrized cases.",
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
