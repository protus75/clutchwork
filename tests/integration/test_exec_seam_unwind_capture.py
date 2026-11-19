import asyncio
import os
import sys

import pytest

from clutch.seams import SubprocessExec


@pytest.mark.asyncio
async def test_timeout_captures_stdout_and_stderr(tmp_path):
    code = 'import sys,time; print("first\\nsecond", flush=True); print("error text", file=sys.stderr, flush=True); time.sleep(60)'
    with pytest.raises(TimeoutError) as caught:
        await SubprocessExec().run([sys.executable, "-c", code], cwd=tmp_path, env=os.environ, timeout=1)
    assert caught.value.process_capture == ("first\nsecond\n", "error text\n")


@pytest.mark.asyncio
async def test_cancellation_captures_lines(tmp_path):
    printed = asyncio.Event()
    code = 'import time; print("cancel line", flush=True); time.sleep(60)'
    task = asyncio.create_task(SubprocessExec().run([sys.executable, "-c", code], cwd=tmp_path, env=os.environ, timeout=10, on_stdout_line=lambda line: printed.set()))
    await asyncio.wait_for(printed.wait(), 5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError) as caught:
        await task
    assert caught.value.process_capture == ("cancel line\n", "")
