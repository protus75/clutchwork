---
id: declined-box-000688-17debde0
kind: declined
link: box-000688-17debde0
reopen_after_days: 60
---
Merged ticket engine-callerless-code deleted `Timers.wait_next`, so the `sleep` argument that the `Timers` constructor takes is no longer read anywhere. The note proposes removing that argument and updating its eight construction sites in the CLI entry point, the eval harness, eval diagnose, and five test modules. It should wait until evidence-rusage-capture merges, because that ticket fences one of those test modules.

This is a dead-parameter cleanup. An unread constructor argument causes no incorrect runtime behavior: timers still fire, nothing is mis-scheduled, and no run fails or produces wrong output because of it. The triage bar says cleanup and refactors are declined unless they are tied to reachable incorrect behavior, and the note claims none. Reopen if the unread `sleep` argument causes a real defect, for example if a caller depends on an injected sleep that `Timers` silently ignores and a test or run then waits in real time or misbehaves. Also reopen if a ticket already editing `clutch/timers.py` can drop the argument as part of work it is required to do.

- The message is a `suggestion` from a session and names no failure, stage or outcome.
- It describes a constructor parameter that became unused after merged ticket engine-callerless-code removed `Timers.wait_next`.
- The proposed change removes the parameter and edits eight construction sites in clutch/__main__.py, eval/harness.py, eval/diagnose.py and five test modules. That is a refactor that changes no behavior.
- No open or merged ticket or registry record covers removing this parameter, so a tombstone does not apply.

Message: box-000688-17debde0
