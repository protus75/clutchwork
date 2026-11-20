# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test seams unwind capture
# relates: [clutch/seams.py]
# owner: clutch/seams.py
# verified: 9a610809
# hash: 0cc80df75311621e599916343fbfbcbc385ee0db4c792287b487f10ab910cd0c
import asyncio
from types import SimpleNamespace

import pytest

from clutch import seams


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_unwind_captures_read_and_drained_bytes(monkeypatch, tmp_path, cancel):
    ready = asyncio.Event()
    proc = SimpleNamespace(pid=123, stdout=object(), stderr=object())

    async def spawn(*args, **kwargs):
        return proc

    async def reap(*args):
        await asyncio.Event().wait()

    async def kill_and_wait(process):
        process._clutch_wait.cancel()
        await asyncio.gather(process._clutch_wait, return_exceptions=True)
        return b"out remainder", b"err remainder"

    async def connect(factory, pipe):
        protocol = factory()
        reader = protocol._stream_reader
        reader.feed_data(b"out prefix\n" if pipe is proc.stdout else b"err prefix\n")
        return None, protocol

    monkeypatch.setattr(seams, "_spawn", spawn)
    monkeypatch.setattr(seams, "_reap", reap)
    monkeypatch.setattr(seams, "_kill_and_wait", kill_and_wait)
    monkeypatch.setattr(seams.shutil, "which", lambda *args, **kwargs: "fake")
    monkeypatch.setattr(asyncio.get_running_loop(), "connect_read_pipe", connect)
    task = asyncio.create_task(seams.SubprocessExec().run(["fake"], cwd=tmp_path, env={}, timeout=0.05 if not cancel else 10, on_stdout_line=lambda line: ready.set()))
    await asyncio.wait_for(ready.wait(), 1)
    if cancel:
        task.cancel()
    with pytest.raises(asyncio.CancelledError if cancel else TimeoutError) as caught:
        await task
    assert caught.value.process_capture == ("out prefix\nout remainder", "err prefix\nerr remainder")
