---
id: declined-box-000615-857a29fe
kind: declined
link: box-000615-857a29fe
reopen_after_days: 60
---
The seams-passed-not-built Implement run noted that three classes still build their own filesystem seam instead of having one passed in. `Journal` (`clutch/journal.py:164`) and `EngineLog` (`clutch/enginelog.py:21`) each call `LocalFileSystem()` themselves. `Driver.from_config` (`clutch/driver.py:190`) uses `LocalFileSystem()` only when the caller passes no `fs`. The note asks for all three to receive the seam from their caller.

This asks for a seam-purity refactor and reports no runtime fault. The note names no wrong output, failed run or test that needs a fake filesystem it cannot get. The Driver already accepts an injected `fs`, and builds `LocalFileSystem()` only as its production default. Registry record declined-box-000045-bc4b05d1 already declined moving EngineLog's own file I/O behind the seam until a fake-driven test needs it, and record declined-box-000017-8007f56c made the same call for the lockfile. The triage bar declines a cleanup or refactor unless it causes reachable incorrect runtime behavior. Reopen when a fake-driven test or a run fails because Journal, EngineLog or Driver cannot take an injected FileSystem, and cite that test or run.

- clutch/journal.py:164 self._fs = LocalFileSystem()
- clutch/enginelog.py:21 self._fs = LocalFileSystem()
- clutch/driver.py:190 fs or LocalFileSystem() (the Driver already accepts an injected fs)
- declined-box-000045-bc4b05d1: EngineLog seam use deferred until a fake-driven test needs it
- declined-box-000017-8007f56c: lockfile seam use deferred on the same grounds
- The message has stage implement, outcome ok, and no failure or test issue attached

Message: box-000615-857a29fe
