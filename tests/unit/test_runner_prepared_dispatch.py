# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test runner prepared dispatch
# relates: [clutch/runner.py]
# owner: clutch/runner.py
# verified: 9a610809
# hash: f44c1a36d799d4bd80094467a065aa633981dd3ef5df3d3dd2ffb28d63a32bb6
from dataclasses import dataclass

import pytest

from clutch import runner


@dataclass
class Checkout:
    config: object
    control: object


class Control:
    value = "first"

    def load_config(self):
        return self.value


@pytest.mark.asyncio
async def test_snapshot_cache_single_use_and_abort(monkeypatch):
    control = Control()
    built = []
    monkeypatch.setattr(runner, "snapshot_config", lambda value: value)

    class Callback:
        def __init__(self, config):
            self.config = config
            self.stages = ["stage", config]
            self.aborts = 0

        async def __call__(self, ticket):
            if ticket == "raise":
                raise ValueError("failed")
            return (self.config, ticket)

        async def abort_current(self):
            self.aborts += 1

    async def prepare(local):
        callback = Callback(local.config)
        built.append(callback)
        return callback

    monkeypatch.setattr(runner, "prepare_pipeline", prepare)
    dispatch = runner.pipeline(Checkout("original", control))
    await dispatch.abort_current()
    await dispatch.prepare()
    await dispatch.prepare()
    assert len(built) == 1
    assert dispatch.stages == ["stage", "first"]
    control.value = "second"
    await dispatch.prepare()
    assert [c.config for c in built] == ["first", "second"]
    assert dispatch.stages == ["stage", "second"]
    await dispatch.abort_current()
    assert built[-1].aborts == 1
    assert await dispatch("ticket") == ("second", "ticket")
    assert len(built) == 2
    assert await dispatch("next") == ("second", "next")
    assert len(built) == 3
    with pytest.raises(ValueError, match="failed"):
        await dispatch("raise")
    assert len(built) == 4
    assert await dispatch("after") == ("second", "after")
    assert len(built) == 5
