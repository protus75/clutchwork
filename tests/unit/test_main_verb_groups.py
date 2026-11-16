"""Plain argument seams for the shared refusal and writer lock plumbing."""

import asyncio
from datetime import UTC, datetime

import pytest

from clutch import __main__ as entry
from clutch import runner
from clutch.lockfile import LockHeld


def test_refusal_printer(capsys):
    # A success/implicit return and a missing prefix/message each give different values.
    result = entry._fail("dismiss", "writer held -- wait for triage")
    assert result == runner.EXIT_REFUSED
    assert capsys.readouterr().err == "clutch dismiss: writer held -- wait for triage\n"


@pytest.mark.parametrize("exceptional", [False, True])
def test_writer_lock_excludes_and_releases(tmp_path, exceptional):
    async def exercise():
        def lock():
            return entry._locked(tmp_path, "triage", instance_id="unit-holder", clock=lambda: datetime(2026, 1, 1, tzinfo=UTC))

        class WorkFailed(Exception):
            pass

        async def work():
            async with lock():
                # Omitting acquire lets this second entry succeed.
                with pytest.raises(LockHeld, match='"verb": "triage"'):
                    async with lock():
                        pass
                if exceptional:
                    raise WorkFailed

        if exceptional:
            with pytest.raises(WorkFailed):
                await work()
        else:
            await work()
        # Omitting release (including on exceptional exit) refuses this third entry.
        async with lock():
            pass

    asyncio.run(exercise())
