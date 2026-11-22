"""The serve rig uses the shared polling helpers without changing their contract."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that serve_rig reuses the shared fakes.turn/until polling helpers, keeps their fake-clock pacing and translates their timeout message.
# relates: [clutch/serve.py, tests/fakes.py, tests/integration/serve_rig.py]
# owner: engine
# verified: 543c80a2
# hash: 89ace906333ef500ed81ff8817e5baa941e24c7912383fdc3c5f1775c3606991

import inspect
from datetime import timedelta
from types import SimpleNamespace

import pytest

from clutch import serve
from tests import fakes
from tests.integration import serve_rig


def test_shared_helpers():
    assert serve_rig.turn is fakes.turn
    source = inspect.getsource(serve_rig.until)
    assert "fakes.until" in source
    assert "while" not in source


@pytest.mark.asyncio
async def test_until_pacing():
    clock = fakes.FakeClock()
    start = clock()
    polls = 0

    def predicate():
        nonlocal polls
        polls += 1
        return polls == 42

    await serve_rig.until(SimpleNamespace(time=clock), predicate)
    assert polls == 42
    assert clock() - start == 3 * timedelta(seconds=serve.SERVE_POLL_S)


@pytest.mark.asyncio
async def test_until_translates_timeout(monkeypatch):
    async def fail(*args, **kwargs):
        raise AssertionError("injected failure")

    monkeypatch.setattr(fakes, "until", fail)
    with pytest.raises(AssertionError) as caught:
        await serve_rig.until(SimpleNamespace(time=fakes.FakeClock()), lambda: False)
    assert str(caught.value) == "production graph did not reach the scripted boundary"
