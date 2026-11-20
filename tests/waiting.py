"""Condition waits for tests that share the machine with other pytest workers."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Condition waits for tests that share the machine with other pytest workers.
# relates: [clutch/seams.py]
# owner: clutch/seams.py
# verified: d7719818
# hash: 2f9b5010960515f67aed65871d3d88de6dff6979d652c532782e6372cda2fd27

import asyncio
import os
import time
from pathlib import Path

import clutch.seams as seams
from clutch.seams import SubprocessExec


async def wait_until(predicate):
    deadline = time.monotonic() + 60
    while not predicate():
        assert time.monotonic() < deadline, "condition did not become true within 60 seconds"
        await asyncio.sleep(0)


def group_exited(pgid):
    # Orphaned zombies may await init's reaper, but can no longer execute or write.
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
        except FileNotFoundError, ProcessLookupError:
            continue
        if int(fields[2]) == pgid and fields[0] != "Z":
            return False
    return True


def ready_before_returning_spawn(monkeypatch, ready):
    """Keep interpreter startup outside the seam's real timeout window."""
    spawn = seams._spawn

    async def started(*args, **kwargs):
        proc = await spawn(*args, **kwargs)
        try:
            await wait_until(ready)
        except BaseException:
            SubprocessExec().kill_group(proc.pid)
            os.wait4(proc.pid, 0)
            proc.returncode = -9
            for pipe in (proc.stdout, proc.stderr):
                if pipe is not None:
                    pipe.close()
            raise
        return proc

    monkeypatch.setattr(seams, "_spawn", started)
