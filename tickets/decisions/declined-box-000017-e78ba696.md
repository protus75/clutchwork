---
id: declined-box-000017-e78ba696
kind: declined
link: box-000017-e78ba696
reopen_after_days: 90
---
A bootstrap note says two things about `clutch/lockfile.py`. First, `Lockfile` receives `instance_id` from its caller, and the first caller should work it out. Second, the lockfile reads and writes its file with raw `os`/`fcntl` calls instead of going through the FileSystem seam. The note says the seam would need a lock verb only if a fake-driven test ever has to simulate lock contention.

The first half is already done: every caller (serve, drain, runner, and the CLI verbs) passes `instance_id=await git.describe(repo)`. These callers do not check for an installed release tag first. That matters little, because `git.py` says the value is used only for diagnostics, so nothing behaves incorrectly. The second half is speculative hardening. The note itself makes it conditional on a future test needing it, and it points to no wrong runtime behavior. This is not a duplicate of any open ticket.

- clutch/serve.py:492, clutch/drain.py:204, clutch/runner.py:454 and clutch/__main__.py:403 all build Lockfile with instance_id=await git.describe(repo)
- clutch/git.py:140 docstring: 'Diagnostics only: derives the lockfile instance_id for an untagged dev instance.'
- clutch/lockfile.py:30 takes instance_id as a keyword argument; no caller fakes lock contention

Message: box-000017-e78ba696
