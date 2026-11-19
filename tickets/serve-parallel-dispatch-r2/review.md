# Review: snag

The run-set and exclusive-gate design matches the ticket and the call sites move as required, but the new admission release paths now await a contended Condition lock in `finally` blocks where the old `Lock.release()` was synchronous, so a repeated cancellation can permanently leak a slot or leave the exclusive gate held.

## Findings

- [logic] clutch/daemon.py:655 `dispatch`'s outer `finally: await self._release_run()` acquires `self._condition`, which suspends when the lock is contended (for example by waiters re-acquiring after `notify_all`). In the cancellation path this finally runs after `raise`. A second cancel of the caller during that await (the code above explicitly expects repeated caller cancellation) skips `self._holding -= 1`, so the slot leaks for good. With `max_runs` 1 every later dispatch, and every exclusive gate (which waits for `_holding == 0`), then deadlocks. The old `async with self._slot` released synchronously and could not be interrupted. (do instead: Make slot release impossible to cancel: decrement `_holding` synchronously and notify without awaiting (for example, track waiters with futures or Events you can set synchronously), or run the release through `_protected_cleanup(asyncio.create_task(self._release_run()))` as `waiting_for_merge` already does for reacquire. Add a unit test that cancels the caller twice while the release is contended and then asserts the next dispatch is admitted.)
- [logic] clutch/daemon.py:595 `exclusive()`'s exit `finally: async with self._condition: self._exclusive = False` awaits the condition lock. If the gate holder (a `mutations()` task cancelled by `Serve.abort`, startup, or the sweep) is cancelled again while that acquire is suspended, `_exclusive` stays True forever. All run admission and every later exclusive gate then deadlock. The old `_slot` released synchronously. (do instead: Clear `_exclusive` synchronously before any await, or protect the exit with `_protected_cleanup` so a repeated cancellation cannot skip it. Cover this with a test that cancels a gate holder during a contended exit.)
- [logic] clutch/serve.py:301 Watch publication releases the gate with `await gate.__aexit__(None, None, None)` in a `finally`, replacing the synchronous `self.core.admission._slot.release()`. Cancelling the watch loop while that exit waits on the condition lock leaves `_exclusive` set, which blocks all later dispatch and maintenance. This is the same defect as `exclusive()`'s exit, reached through this caller. (do instead: Once `exclusive()`'s exit cannot be cancelled (previous finding), keep this call. Otherwise wrap the exit so cancellation cannot interrupt it.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "a88e38adad59d87a537a7d3fd7a36527979f1131",
  "stem": "serve-parallel-dispatch-r2",
  "reviewed_sha": "a88e38adad59d87a537a7d3fd7a36527979f1131",
  "summary": "The run-set and exclusive-gate design matches the ticket and the call sites move as required, but the new admission release paths now await a contended Condition lock in `finally` blocks where the old `Lock.release()` was synchronous, so a repeated cancellation can permanently leak a slot or leave the exclusive gate held.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/daemon.py",
      "line": 655,
      "message": "`dispatch`'s outer `finally: await self._release_run()` acquires `self._condition`, which suspends when the lock is contended (for example by waiters re-acquiring after `notify_all`). In the cancellation path this finally runs after `raise`. A second cancel of the caller during that await (the code above explicitly expects repeated caller cancellation) skips `self._holding -= 1`, so the slot leaks for good. With `max_runs` 1 every later dispatch, and every exclusive gate (which waits for `_holding == 0`), then deadlocks. The old `async with self._slot` released synchronously and could not be interrupted.",
      "paved_road": "Make slot release impossible to cancel: decrement `_holding` synchronously and notify without awaiting (for example, track waiters with futures or Events you can set synchronously), or run the release through `_protected_cleanup(asyncio.create_task(self._release_run()))` as `waiting_for_merge` already does for reacquire. Add a unit test that cancels the caller twice while the release is contended and then asserts the next dispatch is admitted.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/daemon.py",
      "line": 595,
      "message": "`exclusive()`'s exit `finally: async with self._condition: self._exclusive = False` awaits the condition lock. If the gate holder (a `mutations()` task cancelled by `Serve.abort`, startup, or the sweep) is cancelled again while that acquire is suspended, `_exclusive` stays True forever. All run admission and every later exclusive gate then deadlock. The old `_slot` released synchronously.",
      "paved_road": "Clear `_exclusive` synchronously before any await, or protect the exit with `_protected_cleanup` so a repeated cancellation cannot skip it. Cover this with a test that cancels a gate holder during a contended exit.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/serve.py",
      "line": 301,
      "message": "Watch publication releases the gate with `await gate.__aexit__(None, None, None)` in a `finally`, replacing the synchronous `self.core.admission._slot.release()`. Cancelling the watch loop while that exit waits on the condition lock leaves `_exclusive` set, which blocks all later dispatch and maintenance. This is the same defect as `exclusive()`'s exit, reached through this caller.",
      "paved_road": "Once `exclusive()`'s exit cannot be cancelled (previous finding), keep this call. Otherwise wrap the exit so cancellation cannot interrupt it.",
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
