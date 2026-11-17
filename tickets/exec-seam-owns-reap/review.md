# Review: snag

The spawn move, wait4 reap, rusage helpers, waiting.py patch and doc line match the ticket, but the reap runs on asyncio's shared, bounded default executor, so a bounded run can hang past its timeout behind other runs' waits.

## Findings

- [logic] clutch/seams.py:153 `wait()` reaps through `asyncio.to_thread(os.wait4, proc.pid, 0)`, which uses the loop's shared default ThreadPoolExecutor, capped at min(32, cpu_count+4) workers. Each running child holds one worker in a blocking wait4 until it exits, and unbounded callers such as `clutch/covmap.py:24` (`timeout=None`) can hold one for a very long time. Once enough children are running, a new run's wait task stays queued without a thread. When that run times out, `_kill_and_wait` kills the group and then awaits the queued `proc._clutch_wait`, so `run` blocks well past its timeout and the killed child stays a zombie until another worker frees up. The old asyncio watcher had no such shared cap. The 20-way test passes only because its children exit at once. (do instead: Reap without the shared default executor. Either wait on a pidfd (`os.pidfd_open(proc.pid)` plus `loop.add_reader`, then a non-blocking `os.wait4(pid, 0)` once it is readable), or run the blocking `os.wait4` in a dedicated thread per child (for example a `threading.Thread` that resolves a future with `loop.call_soon_threadsafe`), as the ticket's 'a pidfd reader or a dedicated thread' allows.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "af97e5683e16ee00d76c73e41926326e1f3fde51",
  "stem": "exec-seam-owns-reap",
  "reviewed_sha": "af97e5683e16ee00d76c73e41926326e1f3fde51",
  "summary": "The spawn move, wait4 reap, rusage helpers, waiting.py patch and doc line match the ticket, but the reap runs on asyncio's shared, bounded default executor, so a bounded run can hang past its timeout behind other runs' waits.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/seams.py",
      "line": 153,
      "message": "`wait()` reaps through `asyncio.to_thread(os.wait4, proc.pid, 0)`, which uses the loop's shared default ThreadPoolExecutor, capped at min(32, cpu_count+4) workers. Each running child holds one worker in a blocking wait4 until it exits, and unbounded callers such as `clutch/covmap.py:24` (`timeout=None`) can hold one for a very long time. Once enough children are running, a new run's wait task stays queued without a thread. When that run times out, `_kill_and_wait` kills the group and then awaits the queued `proc._clutch_wait`, so `run` blocks well past its timeout and the killed child stays a zombie until another worker frees up. The old asyncio watcher had no such shared cap. The 20-way test passes only because its children exit at once.",
      "paved_road": "Reap without the shared default executor. Either wait on a pidfd (`os.pidfd_open(proc.pid)` plus `loop.add_reader`, then a non-blocking `os.wait4(pid, 0)` once it is readable), or run the blocking `os.wait4` in a dedicated thread per child (for example a `threading.Thread` that resolves a future with `loop.call_soon_threadsafe`), as the ticket's 'a pidfd reader or a dedicated thread' allows.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
