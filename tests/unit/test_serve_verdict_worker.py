"""Verdict polling does not enter the admission exclusion."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test checking that Serve's verdict worker polls control and settles admissions with apply_verdict without entering the admission exclusion.
# relates: [clutch/serve.py, tests/unit/test_serve_idle_poll.py]
# owner: engine
# verified: 8107f6ac
# hash: 5c81ea50f4ef2621b66ddb95b5539d0dc6e02783fadb91addae59bbf13fc5af6

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch.serve import Serve
from tests.unit.test_serve_idle_poll import PollFinished, Response, stop_poll


@pytest.mark.asyncio
async def test_verdict_worker_polls_and_settles_without_admission():
    owner = Serve.__new__(Serve)
    owner.responses = [Response() for _ in range(5)]
    owner.stopping = False
    owner.checkout = SimpleNamespace(sleep=stop_poll)
    owner.apply_verdict = object()
    owner.control = SimpleNamespace(poll=AsyncMock(), projection=SimpleNamespace(kill_requested=False), inbox=SimpleNamespace(settle_admissions=AsyncMock()))
    owner.control.poll = lambda: None
    with pytest.raises(PollFinished):
        await owner.verdicts()
    owner.control.inbox.settle_admissions.assert_awaited_once_with(owner.apply_verdict)
