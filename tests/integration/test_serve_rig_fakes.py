"""The serve rig uses the shared polling helpers without changing their contract."""

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
    times = iter([0, 0, 61])
    monkeypatch.setattr(fakes, "time", SimpleNamespace(monotonic=lambda: next(times)))
    with pytest.raises(AssertionError) as caught:
        await serve_rig.until(SimpleNamespace(time=fakes.FakeClock()), lambda: False)
    assert str(caught.value) == "production graph did not reach the scripted boundary"
