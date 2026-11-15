---
id: declined-box-000453-bef5312c
kind: declined
link: box-000453-bef5312c
reopen_after_days: 30
---
The suggestion says a supervising session cannot tell from the status output whether the checkout writer lock is held right now. `clutch/state/clutch.lock` keeps the identity of the last holder after that process dies, so twice an operator had to run `ps` on the recorded pid. It asks status to test the lock with a non-blocking flock and to label the recorded identity as the last holder when nobody holds the lock.

No harmful behavior gap is shown, because the answer is already available from existing verbs. `clutch doctor` runs `inspect_lock` (`clutch/doctor.py:20-32`). That function tries a non-blocking flock on the existing `clutch.lock` without writing an identity. It reports `writer lock is available` when nobody holds the lock, and a `LockHeld` failure that names the holder when someone does. This is the check the suggestion asks for, so no `ps` is needed. The snapshot behind the extension's merged engine-lock indicator also treats a dead recorded pid as no holder (`clutch/observe.py:120-137`, `lock_holder`). The lockfile docstring says the leftover identity is expected and harmless, because correctness comes from flock alone. The note reports no wrong action, lost run, or blocked verb, only the extra effort of finding the right check. Adding a second lock probe to status would duplicate doctor. Reopen if an operator or supervising session takes a wrong action, such as a stop, kill, or unneeded wait, because the leftover lock identity misled them even though `clutch doctor` was run, or if `clutch doctor` reports the lock wrongly.

- clutch/doctor.py:20-32 inspect_lock tries a non-blocking LOCK_EX on clutch.lock and reports 'writer lock is available', or raises LockHeld with the holder's identity
- clutch/doctor.py:57-65 doctor reports that probe as its 'lock' row
- clutch/observe.py:120-137 lock_holder returns None when the recorded pid no longer exists ('A killed drain leaves its lockfile behind')
- clutch/lockfile.py:1-6 says correctness comes from flock alone and the recorded identity is residue by design
- clutch/status.py has no lock line; the note reports only that status does not show it, not a wrong action caused by that

Message: box-000453-bef5312c
