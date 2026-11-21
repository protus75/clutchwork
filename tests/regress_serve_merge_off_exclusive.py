"""Merge work and a new run must start beside a held implementation slot."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce merge polling blocking run slots.
# relates: [clutch/daemon.py, clutch/serve.py]
# owner: engine
# verified: 407dfd0f
# hash: f0e17db7e478de4eae72d1dfea1002a76a5d61c8f76e5ca648f524c200b2cf07

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clutch.daemon import DaemonAdmission  # noqa: E402
from clutch.serve import Serve  # noqa: E402


async def reproduce():
    release, processing, finish = asyncio.Event(), asyncio.Event(), asyncio.Event()
    started = {stem: asyncio.Event() for stem in ("first", "second")}

    async def dispatch(ticket):
        started[ticket.stem].set()
        await release.wait()

    async def process():
        processing.set()
        await finish.wait()

    class Response:
        async def wait(self, work):
            return await work

    owner = Serve.__new__(Serve)
    admission = DaemonAdmission(dispatch, max_runs=2)
    owner.core = SimpleNamespace(admission=admission)
    owner.responses = [None, Response()]
    owner.queue = SimpleNamespace(process=process, deliveries=[])
    owner.check_upgrade = AsyncMock()
    owner.merge_work = lambda: True
    owner.stopping = False
    owner.control = SimpleNamespace(poll=lambda: None, projection=SimpleNamespace(kill_requested=False))
    first = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="first")))
    await started["first"].wait()
    merge = asyncio.create_task(owner.merge())
    for _ in range(10):
        await asyncio.sleep(0)
    second = asyncio.create_task(admission.dispatch(SimpleNamespace(stem="second")))
    for _ in range(10):
        await asyncio.sleep(0)
    passed = processing.is_set() and started["second"].is_set() and not admission.exclusive_pending()
    merge.cancel()
    release.set()
    await asyncio.gather(first, second, merge, return_exceptions=True)
    return passed


if __name__ == "__main__":
    passed = asyncio.run(reproduce())
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    sys.exit(0 if passed else 1)
