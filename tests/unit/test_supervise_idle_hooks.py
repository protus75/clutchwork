"""Serve and drain supervise only at idle boundaries, with lazy preparation."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests checking that serve and drain run idle supervision only at idle boundaries, inside the mutation lock and after retro, and prepare context only when eligible work exists
# relates: [clutch/config.py, clutch/drain.py, clutch/journal.py, clutch/serve.py, clutch/triage.py, tests/unit/test_supervise_idle_point.py]
# owner: engine
# verified: 45e4e081
# hash: 73850da6886d48cc1d92a87a55bcfbfed544a69c783dde57147e83f5c0f78cad

from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import drain, serve, triage
from clutch.config import Caps
from clutch.journal import EventType
from tests.unit.test_supervise_idle_point import Journal, arrival, rig


class EndPoll(Exception):
    pass


@dataclass(frozen=True)
class Checkout:
    repo: object
    journal: object
    config: object
    control: object = None
    git: object = None
    fs: object = None


def serve_rig(tmp_path, monkeypatch, checkout, ctx):
    s = object.__new__(serve.Serve)
    s.checkout = checkout
    s.control = SimpleNamespace(
        inbox=SimpleNamespace(settle_triage=AsyncMock()), poll=lambda: None, load_config=lambda: checkout.config, projection=SimpleNamespace(kill_requested=False, stop_requested=False, pause_id=None)
    )
    s.stopping = False
    s.upgrade_idle = lambda: True
    s.check_upgrade = AsyncMock()
    s.prepare = AsyncMock(return_value=SimpleNamespace(ctx=ctx))
    s.core = SimpleNamespace(admission=SimpleNamespace(busy=lambda: False, exclusive_pending=lambda: False), scheduler=SimpleNamespace(dispatch_next=AsyncMock(), raise_failure=lambda: None))
    s.stop = lambda: setattr(s, "stopping", True)
    s.locked = False

    @asynccontextmanager
    async def mutations():
        s.locked = True
        if getattr(s, "on_lock", None) is not None:
            s.on_lock()
        try:
            yield
        finally:
            s.locked = False

    async def wait(work):
        return await work

    async def sleep(_):
        raise EndPoll

    s.responses = [SimpleNamespace(wait=wait)]
    s.mutations = mutations
    s.checkout = SimpleNamespace(**checkout.__dict__, sleep=sleep)
    # replace() in lazy preparation needs the real dataclass checkout.
    monkeypatch.setattr(serve, "replace", lambda c, **kwargs: Checkout(c.repo, c.journal, kwargs["config"]))
    monkeypatch.setattr(serve, "snapshot_config", lambda c: c)
    return s


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["idle", "busy", "stopping", "paused", "stop", "kill", "stop_on_lock", "pause_on_lock", "kill_on_lock", "stopping_on_lock"])
async def test_serve_dispatch_guard_and_order(tmp_path, monkeypatch, mode):
    c = Checkout(tmp_path, Journal(), SimpleNamespace(caps=Caps()))
    s = serve_rig(tmp_path, monkeypatch, c, None)
    s.upgrade_idle = lambda: mode != "busy"
    s.stopping = mode == "stopping"
    s.control.projection.pause_id = "pause" if mode == "paused" else None
    s.control.projection.stop_requested = mode == "stop"
    s.control.projection.kill_requested = mode == "kill"
    if mode == "stop_on_lock":
        s.on_lock = lambda: setattr(s.control.projection, "stop_requested", True)
    elif mode == "pause_on_lock":
        s.on_lock = lambda: setattr(s.control.projection, "pause_id", "pause")
    elif mode == "kill_on_lock":
        s.on_lock = lambda: setattr(s.control.projection, "kill_requested", True)
    elif mode == "stopping_on_lock":
        s.on_lock = lambda: setattr(s, "stopping", True)
    calls = []

    async def supervise(checkout, make_ctx):
        calls.append(("supervise", s.locked))

    async def dispatch():
        calls.append(("dispatch", s.locked))

    monkeypatch.setattr(serve, "supervise_idle", supervise)
    s.core.scheduler.dispatch_next.side_effect = dispatch
    with pytest.raises(EndPoll):
        await s.dispatch()
    # Wrong: supervise while busy/stopped/paused, outside the lock, or after dispatch.
    assert calls == (
        [("supervise", True), ("dispatch", False)] if mode == "idle" else [("dispatch", False)] if mode in {"busy", "stop", "stop_on_lock", "pause_on_lock", "kill_on_lock", "stopping_on_lock"} else []
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("eligible", [False, True])
async def test_serve_preparation_is_lazy(tmp_path, monkeypatch, eligible):
    c, ctx, _, apply = rig(tmp_path, monkeypatch, history=arrival() if eligible else [])
    s = serve_rig(tmp_path, monkeypatch, Checkout(c.repo, c.journal, c.config), ctx)
    with pytest.raises(EndPoll):
        await s.dispatch()
    # Wrong: preflight every idle poll, or fail to await make_ctx for eligible work.
    assert s.prepare.await_count == apply.await_count == int(eligible)


def drain_rig(tmp_path, monkeypatch, checkout, dispatch):
    d = drain._Drain.__new__(drain._Drain)
    d.c, d.dispatch, d.before_dispatch = checkout, dispatch, None
    d.report, d.retro = object(), None
    d.provider_deadlines, d.storm_waiting = [], False
    d.last_dispatched = "work"
    d._stopping = lambda: False
    d._offer_material = lambda: None
    d._scan = AsyncMock(return_value=SimpleNamespace(tickets={}))
    d._select = lambda *args: (None, False)
    d._settle = lambda *args: None
    monkeypatch.setattr(drain, "intake", AsyncMock())
    monkeypatch.setattr(triage, "report_intake", lambda c: None)
    return d


@pytest.mark.asyncio
@pytest.mark.parametrize("between", [False, True])
async def test_drain_boundary_order(tmp_path, monkeypatch, between):
    history = arrival() if between else [arrival(to="gate_failed")[0]]
    c = Checkout(
        tmp_path,
        Journal(history),
        SimpleNamespace(caps=Caps()),
        SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), projection=SimpleNamespace(stop_requested=False, retro_id=None), storm_holds=lambda: {}),
    )
    d = drain_rig(tmp_path, monkeypatch, c, object())
    calls = []
    d.retro = object()
    d.served_retro_id = None
    d._run_retro = AsyncMock(side_effect=lambda **kwargs: calls.append("retro"))
    c.control.projection.retro_id = "requested"

    async def supervise(checkout, make_ctx):
        calls.append("supervise")

    monkeypatch.setattr(drain, "supervise_idle", supervise)
    await d.run()
    # Wrong: interrupt a retry cycle or supervise before retro.
    assert calls == (["retro", "supervise"] if between else [])


@pytest.mark.asyncio
@pytest.mark.parametrize("prepared,eligible", [(False, True), (True, False), (True, True)])
async def test_drain_lazy_context(tmp_path, monkeypatch, prepared, eligible):
    c, ctx, _, apply = rig(tmp_path, monkeypatch, history=arrival() if eligible else [])
    control = SimpleNamespace(inbox=SimpleNamespace(settle_triage=AsyncMock()), load_config=lambda: c.config, projection=SimpleNamespace(stop_requested=False))
    dispatch = SimpleNamespace(prepare=AsyncMock(), callback=SimpleNamespace(ctx=ctx)) if prepared else object()
    checkout = Checkout(c.repo, c.journal, c.config, control)
    d = drain_rig(tmp_path, monkeypatch, checkout, dispatch)
    d.last_dispatched = None
    monkeypatch.setattr("clutch.config.snapshot_config", lambda c: c)
    before = c.journal.read()
    await d.run()
    # Wrong: omit supervision after preparation, or attempt without prepare support.
    assert apply.await_count == int(prepared and eligible)
    if prepared:
        # Wrong: eagerly prepare for an empty Reject queue.
        assert dispatch.prepare.await_count == int(eligible)
    if not prepared:
        # Wrong: journal attempt or create worktree even though make_ctx returned None.
        assert c.journal.read() == before
        assert ctx.git.calls == []
