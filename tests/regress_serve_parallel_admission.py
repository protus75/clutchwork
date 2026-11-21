"""Idle scan must not queue exclusive maintenance behind a held run slot."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce idle poll blocking parallel admission.
# relates: [clutch/daemon.py, clutch/serve.py, tests/fakes.py]
# owner: engine
# verified: 4296219b
# hash: 936e7758f629e13c101fe5982c0dd892fdd023adc275925ac1af5102f03dfb6a

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clutch.daemon import DaemonAdmission  # noqa: E402
from clutch.serve import Serve  # noqa: E402
from tests.fakes import FakeFileSystem, FakeJournal  # noqa: E402


async def reproduce():
    starts = []
    release = asyncio.Event()

    async def dispatch(ticket):
        starts.append(ticket.stem)
        await release.wait()

    admission = DaemonAdmission(dispatch, max_runs=2)
    owner = Serve.__new__(Serve)
    owner.core = SimpleNamespace(admission=admission)
    owner.stopping = False
    owner.read, owner.stems = lambda stem: None, lambda: []
    owner.scan_snapshot, owner.scanned = None, {}
    with tempfile.TemporaryDirectory() as directory:
        owner.checkout = SimpleNamespace(
            repo=Path(directory),
            fs=FakeFileSystem(),
            journal=FakeJournal(),
            git=SimpleNamespace(status_porcelain=AsyncMock(return_value=""), rev_parse=AsyncMock(return_value="head"), main_write=asyncio.Lock),
        )
        with patch("clutch.serve.intake", AsyncMock()):
            await owner.scan()
            first = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="first")))
            for _ in range(10):
                await asyncio.sleep(0)
            poll = asyncio.create_task(owner.scan())
            for _ in range(10):
                await asyncio.sleep(0)
            second = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="second")))
            for _ in range(10):
                await asyncio.sleep(0)
            passed = starts == ["first", "second"] and poll.done()
            poll.cancel()
            release.set()
            await asyncio.gather(first, second, poll, return_exceptions=True)
            return passed


if __name__ == "__main__":
    passed = asyncio.run(reproduce())
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    sys.exit(0 if passed else 1)
