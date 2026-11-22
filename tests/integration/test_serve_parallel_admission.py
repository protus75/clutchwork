"""Continuous serve admits idle capacity while preserving maintenance ownership."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that continuous serve admits parallel runs within capacity and fence overlap, and handles control confirm and stop requests during dispatch
# relates: [clutch/config.py, clutch/control.py, clutch/journal.py, clutch/llm.py, clutch/scheduler.py, tests/integration/serve_rig.py]
# owner: clutch/serve.py
# verified: 58c46bba
# hash: 2e3adb59e559dd9b59dbf0cd3aa7540b34347ec24e12d2feb2ea7ae0de3dcc30

import asyncio
import json
from dataclasses import replace

import pytest

from clutch.config import load_config
from clutch.control import AdmissionRequest, publish_request
from clutch.journal import EventType
from clutch.llm import FakeLLM
from clutch.scheduler import Scheduler
from tests.cli_helpers import root
from tests.config_fixture import amend_config
from tests.integration.serve_rig import admission_ticket, finish, request, start_admission, until
from tests.loop_helpers import admission_graph, terminals

pytestmark = pytest.mark.disk_io_skip


def stage_events(rig):
    path = rig.checkout.config.state_dir / "engine.log"
    return [(e["event"], e["stem"]) for line in path.read_text().splitlines() if (e := json.loads(line)).get("surface") == "implement" and e["event"] in {"stage_start", "stage_end"}]


async def parallel_rig(root, monkeypatch, max_runs):
    rig = await admission_graph(root, monkeypatch, {}, endings={"one": "noop", "two": "noop"})
    path = root / "config.yaml"
    amend_config(root, scheduler={"parallel": {"enabled": True, "max_runs": max_runs}, "max_unmerged": 4})
    rig.checkout = replace(rig.checkout, config=load_config(path, cwd=root))
    return rig


@pytest.mark.asyncio
@pytest.mark.parametrize("max_runs,overlap", [(2, False), (1, False), (2, True)])
async def test_parallel_implementations(root, monkeypatch, max_runs, overlap):
    rig = await parallel_rig(root, monkeypatch, max_runs)
    entered = {stem: asyncio.Event() for stem in ("one", "two")}
    release = {stem: asyncio.Event() for stem in entered}
    call = FakeLLM.call
    allow_second = asyncio.Event()
    choices = []
    dispatch_next = Scheduler.dispatch_next

    async def ordered_dispatch(scheduler):
        if "one" in scheduler.flying and not allow_second.is_set():
            return None
        result = await dispatch_next(scheduler)
        if "one" in scheduler.flying and allow_second.is_set():
            choices.append(result.stem if result is not None else None)
        return result

    monkeypatch.setattr(Scheduler, "dispatch_next", ordered_dispatch)

    async def blocked(model, req):
        if req.surface == "implement":
            entered[req.subject].set()
            await release[req.subject].wait()
        return await call(model, req)

    monkeypatch.setattr(FakeLLM, "call", blocked)
    admission_ticket(root, "one", paths=("docs/one",), priority="P0")
    admission_ticket(root, "two", paths=("docs/one" if overlap else "docs/two",), priority="P1")
    run = await start_admission(rig, monkeypatch)
    try:
        await until(rig, entered["one"].is_set)
        # Force scan after mark_running and before waking the next dispatch tick.
        await rig.owner.scan()
        allow_second.set()
        if max_runs == 2 and not overlap:
            await until(rig, entered["two"].is_set)
            # Serializing idle polls or ending one early changes these records.
            assert stage_events(rig) == [("stage_start", "one"), ("stage_start", "two")]
            # Starting stages without the durable running transitions loses two.
            assert {e.ticket for e in rig.journal.read() if e.type == EventType.STATE_TRANSITION and e.body.get("to") == "running"} == {"one", "two"}
        else:
            await until(rig, lambda: choices)
            # Ignoring capacity or fence overlap selects two at this exact probe.
            assert (choices[0], stage_events(rig)) == (None, [("stage_start", "one")])
            release["one"].set()
            await until(rig, entered["two"].is_set)
            # Starting two before one ends, or losing the end event, changes order.
            assert stage_events(rig) == [("stage_start", "one"), ("stage_end", "one"), ("stage_start", "two")]
        release["one"].set()
        release["two"].set()
        await until(rig, lambda: terminals(rig, "one") and terminals(rig, "two"))
    finally:
        for event in release.values():
            event.set()
        await finish(rig, run)


@pytest.mark.asyncio
async def test_dispatch_consumed_confirm_and_stop(root, monkeypatch):
    rig = await parallel_rig(root, monkeypatch, 2)
    entered, release, consumed = (asyncio.Event() for _ in range(3))
    call = FakeLLM.call

    async def blocked(model, req):
        if req.surface == "implement":
            entered.set()
            await release.wait()
        return await call(model, req)

    monkeypatch.setattr(FakeLLM, "call", blocked)
    admission_ticket(root, "one", paths=("docs/one",))
    admission_ticket(root, "two", paths=("docs/two",))
    # Draft remains queued until the real accepted request effect commits confirmation.
    path = root / "tickets/two/ticket.md"
    path.write_text(path.read_text().replace("state: confirmed", "state: draft"))
    run = await start_admission(rig, monkeypatch)
    try:
        await until(rig, entered.is_set)
        # Publish inside dispatch's control poll, with merge's probe held behind it.
        original = rig.owner.merge_work
        rig.owner.merge_work = lambda: False if not consumed.is_set() else original()
        control_poll = rig.owner.control.poll

        def dispatch_consumes():
            dispatching = asyncio.current_task() is rig.owner.workers[0]
            if dispatching and not consumed.is_set():
                publish_request(rig.checkout.config.state_dir, AdmissionRequest("confirm-two", rig.owner.control.projection.lifecycle_id, "confirm", "two", None, "operator"), rig.fs)
                control_poll()
                consumed.set()
            else:
                control_poll()

        rig.owner.control.poll = dispatch_consumes
        await until(rig, consumed.is_set)
        await until(rig, lambda: "state: confirmed" in path.read_text())
        # The verdict commits while the implementation remains held.
        assert not release.is_set()
        request(rig, "stop", "stop-held")
        await until(rig, lambda: rig.owner.control.projection.stop_requested)
        release.set()
        await until(rig, run.done)
        # Dropping graceful stop or returning an error changes this result.
        assert await run == 0
        effects = [e for e in rig.journal.read() if e.key == "ticket-plane/two/confirm/confirm-two"]
        # Reapplying the accepted request produces duplicate effect records.
        assert [e.type for e in effects] == [EventType.EFFECT_INTENT, EventType.EFFECT_COMPLETION]
        # Recording completion without applying the verdict leaves draft content.
        assert "state: confirmed" in path.read_text()
        # Ignoring stop after the confirm would admit the newly confirmed ticket.
        assert not any(e.ticket == "two" and e.body.get("to") == "running" for e in rig.journal.read())
    finally:
        release.set()
        if not run.done():
            await finish(rig, run)
