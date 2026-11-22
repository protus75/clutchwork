# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests `box triage` submitting to a running drain or serve, refusal while a non-engine verb holds the lock, direct passes without the lock, and that only the requested messages are triaged
# relates: [clutch/__main__.py, clutch/box.py, clutch/control.py, clutch/drain.py, clutch/journal.py, clutch/llm.py, clutch/lockfile.py, clutch/seams.py]
# owner: clutch/control.py
# verified: 7abfadd2
# hash: 19e510b15ff833a0e759a8f9d67c7f7908b5fbb3dadb908be17f23d493017d6f
from pathlib import Path

import pytest

from clutch import control
from clutch.__main__ import main
from clutch.box import Box
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM
from clutch.lockfile import Lockfile
from clutch.seams import LocalFileSystem
from tests.cli_helpers import ENV, root
from tests.drain_helpers import Clock
from tests.loop_helpers import enqueue, reply, root_with_box

pytestmark = pytest.mark.disk_io_skip


def test_prompt_bounds():
    lines = (Path(__file__).resolve().parents[2] / "clutch/specs/ask/drain-loop.md").read_text().splitlines()
    assert any("clutch box triage" in line and "inbox" in line for line in lines)
    assert any("clutch box dismiss" in line and "between drains" in line for line in lines)
    assert not any("clutch box triage" in line and "clutch box dismiss" in line and "take the writer lock" in line for line in lines)
    assert not any("Triage or dismiss" in line and "only between drains" in line for line in lines)


def test_submit_and_non_engine_refusal(tmp_path, capsys):
    root, box = root_with_box(tmp_path)
    message = enqueue(box, "inbox request")
    state = root / ".clutch/state"
    control.write_active(state, control.ControlProjection("life"), LocalFileSystem(), hold_id=None)
    for verb, expected in [("drain", 0), ("release", 2)]:
        lock = Lockfile(state, verb=verb, instance_id="test", clock=Clock())
        lock.acquire()
        try:
            assert main(["box", "triage", message], cwd=root, env=ENV, clock=Clock()) == expected
        finally:
            lock.release()
        out, err = capsys.readouterr()
        if verb == "drain":
            assert "triage submitted:" in out
            requests = list((state / "control/inbox").glob("*.json"))
            assert len(requests) == 1
        else:
            assert "writer lock held by release" in err
            assert list((state / "control/inbox").glob("*.json")) == requests


def test_lock_free_pass(tmp_path, monkeypatch, capsys):
    root, box = root_with_box(tmp_path)
    message = enqueue(box, "direct pass")
    monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *args, **kwargs: FakeLLM([reply("declined")]))
    assert main(["box", "triage", message], cwd=root, env=ENV, clock=Clock()) == 0
    out = capsys.readouterr().out
    assert f"{message}: declined" in out and "triage submitted:" not in out
    assert box.get(message).resolution is not None
    assert not list((root / ".clutch/state/control/inbox").glob("*.json"))
    assert sum(e.body.get("signal") == "triage_pass" for e in Journal(root / ".clutch/state", Clock()).read() if e.type == EventType.SIGNAL) == 1


def test_serve_processes_only_requested_triage(root, monkeypatch):
    import asyncio

    from tests.integration.serve_rig import finish, until
    from tests.loop_helpers import graph

    async def exercise():
        rig = await graph(root, monkeypatch)
        first = rig.owner.box.enqueue(message_class="suggestion", origin="test", summary="first requested", occurrence_id="first")[0]
        second = rig.owner.box.enqueue(message_class="suggestion", origin="test", summary="second pending", occurrence_id="second")[0]
        run = asyncio.create_task(rig.owner.run())
        try:
            await until(rig, rig.owner.ready.is_set)
            assert not any(e.body.get("signal") == "triage_pass" for e in rig.journal.read())
            control.publish_request(rig.checkout.config.state_dir, control.TriageRequest("request", rig.owner.control.projection.lifecycle_id, "triage", [first], None, "operator"), rig.fs)
            await until(rig, lambda: rig.owner.box.get(first).resolution is not None)
            await until(rig, lambda: any(e.type == EventType.EFFECT_COMPLETION and e.key == "triage/request" for e in rig.journal.read()))
            assert rig.owner.box.get(second).resolution is None
            assert sum(e.body.get("signal") == "triage_pass" for e in rig.journal.read()) == 1
        finally:
            await finish(rig, run)

    asyncio.run(exercise())


def test_real_drain_accepts_and_settles_request(root, monkeypatch, capsys):
    import asyncio

    from clutch.drain import drain
    from tests.drain_helpers import NoChild, pause_checkout

    async def exercise():
        checkout = pause_checkout(root)
        box = Box(checkout.config.state_dir / "box", checkout.fs)
        message = enqueue(box, "drain request")
        entered, release = asyncio.Event(), asyncio.Event()
        calls = 0

        async def before():
            nonlocal calls
            calls += 1
            if calls == 1:
                entered.set()
                await release.wait()

        class Dispatch:
            async def __call__(self, ticket):
                raise AssertionError("no tickets should be dispatched")

            async def abort_current(self):
                pass

        monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *args, **kwargs: FakeLLM([reply("declined")]))
        task = asyncio.create_task(drain(checkout, Dispatch(), reexec=NoChild(), before_dispatch=before))
        try:
            await asyncio.wait_for(entered.wait(), 5)
            assert not any(e.body.get("signal") == "triage_pass" for e in checkout.journal.read())
            assert await asyncio.to_thread(main, ["box", "triage", message], cwd=root, env=ENV, clock=checkout.clock) == 0
            assert "triage submitted:" in capsys.readouterr().out
            release.set()
            await asyncio.wait_for(task, 10)
            assert box.get(message).resolution is not None
            assert sum(e.body.get("signal") == "triage_pass" for e in checkout.journal.read()) == 1
        finally:
            release.set()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())
