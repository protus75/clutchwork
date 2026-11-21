"""A changed scan must not wait for a held implementation slot."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression script reproducing that Serve.scan completes without waiting on a held DaemonAdmission implementation slot or leaving an exclusive request pending.
# relates: [clutch/daemon.py, clutch/serve.py, tests/fakes.py]
# owner: engine
# verified: 4296219b
# hash: eeb277344e378d82e173521e745f0d775c37fabb5ea7e5786ea30df1fa4bc3f8

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
    release, started = asyncio.Event(), asyncio.Event()

    async def dispatch(ticket):
        started.set()
        await release.wait()

    admission = DaemonAdmission(dispatch, max_runs=2)
    owner = Serve.__new__(Serve)
    owner.core = SimpleNamespace(admission=admission)
    owner.stopping = False
    owner.read, owner.stems = lambda stem: "changed", lambda: ["new"]
    owner.scan_snapshot, owner.scanned = None, {}
    with tempfile.TemporaryDirectory() as directory:
        owner.checkout = SimpleNamespace(
            repo=Path(directory),
            fs=FakeFileSystem(),
            journal=FakeJournal(),
            git=SimpleNamespace(status_porcelain=AsyncMock(return_value=""), rev_parse=AsyncMock(return_value="head"), main_write=asyncio.Lock),
        )
        first = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="first")))
        await started.wait()
        with patch("clutch.serve.intake", AsyncMock()):
            scan = asyncio.create_task(owner.scan())
            for _ in range(10):
                await asyncio.sleep(0)
            passed = scan.done() and not admission.exclusive_pending()
            scan.cancel()
            release.set()
            await asyncio.gather(first, scan, return_exceptions=True)
            return passed


if __name__ == "__main__":
    passed = asyncio.run(reproduce())
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    sys.exit(0 if passed else 1)
