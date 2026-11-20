# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test dispatch settle
# relates: [tests/dispatch_settle.py]
# owner: tests/dispatch_settle.py
# verified: 0a308920
# hash: a26c1419a36cb359a29a91c982a017396ade007919d976e1fe8fc3e04fee78ea
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.dispatch_settle import dispatch_settled


@pytest.mark.asyncio
async def test_none_does_not_wait(monkeypatch):
    async def unexpected_turn():
        pytest.fail("waited without a ticket")

    monkeypatch.setattr("tests.dispatch_settle.turn", unexpected_turn)
    scheduler = SimpleNamespace(dispatch_next=AsyncMock(return_value=None), flying={"other": object()})
    assert await dispatch_settled(scheduler) is None
    scheduler.dispatch_next.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_waits_for_dispatched_stem_and_uses_current_dispatch(monkeypatch):
    ticket = SimpleNamespace(stem="chosen")
    scheduler = SimpleNamespace(dispatch_next=AsyncMock(side_effect=AssertionError("stale dispatch")), flying={"chosen": ticket, "other": object()})
    scheduler.dispatch_next = AsyncMock(return_value=ticket)
    turns = []

    async def settle():
        turns.append(scheduler.flying["chosen"])
        if len(turns) == 3:
            del scheduler.flying["chosen"]

    monkeypatch.setattr("tests.dispatch_settle.turn", settle)
    assert await dispatch_settled(scheduler) is ticket
    assert turns == [ticket, ticket, ticket]
    assert list(scheduler.flying) == ["other"]
    scheduler.dispatch_next.assert_awaited_once_with()
