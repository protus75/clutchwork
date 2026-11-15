---
id: tombstone-box-000463-de326d00
kind: tombstone
link: declined-box-000453-bef5312c
reopen_after_days: 30
---
After a verb crashes, `.clutch/state/clutch.lock` still records the dead holder's verb, pid and start time. Someone supervising cannot tell from the file alone whether the lock is held, so they have to check the pid by hand. The note asks for a stale-lock finding in `clutch doctor`, or for acquire to reclaim the file and journal that it did.

Registry record declined-box-000453-bef5312c already covers this. It was about the same lock file keeping the last holder's identity after that process died, which forced an operator to run `ps` on the recorded pid. It asked for status to test the lock and label the recorded identity as the last holder. This message describes the same gap and proposes a different fix (a doctor finding, or reclaim on acquire). The runtime behavior is still harmless. `clutch/lockfile.py` takes the lock with a non-blocking `fcntl.flock`, and the kernel releases that lock when its holder dies. The next acquire succeeds whatever the file says, and the reporter confirms that the snapshot correctly showed the lock as free. A file with a dead pid therefore blocks nothing, and reclaiming it would change nothing. Reopen if a stale record causes wrong runtime behavior, such as a verb refusing or a surface reporting the lock as held when no process holds the flock.

- clutch/lockfile.py:3 says correctness comes from flock alone and the kernel frees the lock when the holder dies
- clutch/lockfile.py:53 and :122 acquire with fcntl.LOCK_EX | fcntl.LOCK_NB, so a dead holder's leftover file does not block acquisition
- The message reports that the snapshot correctly showed the lock as free (engine false) while the stale file was present
- Registry record declined-box-000453-bef5312c reported the same last-holder identity left after the holder died and the same need for a manual pid check

Message: box-000463-de326d00
