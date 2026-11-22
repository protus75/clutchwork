# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that non-ticket main commits do not block parallel admission and that a HEAD change retries a refused ticket intake
# relates: [clutch/llm.py, clutch/scheduler.py, clutch/seams.py, clutch/serve.py, tests/fakes.py, tests/integration/serve_rig.py, tests/integration/test_cli.py]
# owner: engine
# verified: ae1a5a3b
# hash: 14543a325437b357b3104eb37a153c9779abd42d5ee83e15bd068427f8f92fe3
import asyncio

import pytest

from clutch import serve
from clutch.llm import FakeLLM
from clutch.scheduler import Scheduler
from clutch.seams import LocalFileSystem
from tests.cli_helpers import root
from tests.integration.serve_rig import admission_ticket, finish, start_admission, terminals, until
from tests.integration.test_serve_parallel_admission import parallel_rig

pytestmark = pytest.mark.disk_io_skip


@pytest.mark.asyncio
async def test_main_commits_preserve_parallel_admission_and_retry_refusal(root, monkeypatch):
    rig = await parallel_rig(root, monkeypatch, 2)
    monkeypatch.setattr(rig.fs, "entries", LocalFileSystem().entries)
    entered = {stem: asyncio.Event() for stem in ("one", "two")}
    release, allow_second = asyncio.Event(), asyncio.Event()
    call, dispatch = FakeLLM.call, Scheduler.dispatch_next

    async def blocked(model, req):
        if req.surface == "implement" and req.ticket in entered:
            entered[req.ticket].set()
            await release.wait()
        return await call(model, req)

    async def ordered(scheduler):
        if "one" in scheduler.flying and not allow_second.is_set():
            return None
        return await dispatch(scheduler)

    monkeypatch.setattr(FakeLLM, "call", blocked)
    monkeypatch.setattr(Scheduler, "dispatch_next", ordered)
    admission_ticket(root, "one", paths=("docs/one",), priority="P0")
    admission_ticket(root, "two", paths=("docs/two",), priority="P1")
    # Pre-create the roadmap parent before the held run; ticket listing stays fixed.
    (root / "docs").mkdir(exist_ok=True)
    run = await start_admission(rig, monkeypatch)
    observed = []
    try:
        await until(rig, entered["one"].is_set)
        admission = rig.owner.core.admission
        exclusive_pending = admission.exclusive_pending

        def observe():
            value = exclusive_pending()
            observed.append(value)
            return value

        monkeypatch.setattr(admission, "exclusive_pending", observe)
        scans = []
        snapshot = rig.owner.intake_snapshot

        async def sampled():
            value = await snapshot()
            scans.append(value)
            return value

        monkeypatch.setattr(rig.owner, "intake_snapshot", sampled)
        # Commit each non-ticket input independently so either HEAD invalidation is visible.
        for path in ("tickets/one/run.md", "docs/roadmap.md"):
            rig.fs.write(root / path, b"operator record\n")
            await rig.checkout.git.add(root, [path])
            await rig.checkout.git.commit(root, "operator record", only=[path])
        for _ in range(3):
            count = len(scans)
            rig.time.advance(serve.SERVE_POLL_S + 1)
            await until(rig, lambda: len(scans) > count or exclusive_pending())
            # An unconditional HEAD queues maintenance behind the still-held first run.
            assert not observe()
        allow_second.set()
        await until(rig, lambda: entered["two"].is_set() or exclusive_pending())
        # A maintenance waiter or serialized capacity prevents two from entering here.
        assert (entered["two"].is_set(), release.is_set(), any(observed)) == (True, False, False)
        release.set()
        await until(rig, lambda: terminals(rig, "one") and terminals(rig, "two"))
        await until(rig, lambda: rig.owner.upgrade_idle())

        # A missing Context path makes intake refuse while leaving the ticket pending.
        admission_ticket(root, "refused", paths=("docs/refused",))
        ticket = root / "tickets/refused/ticket.md"
        rig.fs.write(ticket, ticket.read_text().replace("- clutch/thing.py", "- clutch/arrived.py").encode())
        await rig.owner.scan()
        status = await rig.checkout.git.status_porcelain(root, "--", "tickets/")
        # A fixture that was already intaken cannot exercise the refused-ticket retry.
        refused = "tickets/refused/" in status
        before = rig.owner.scan_snapshot
        rig.fs.write(root / "clutch/arrived.py", b"arrived = True\n")
        await rig.checkout.git.add(root, ["clutch/arrived.py"])
        await rig.checkout.git.commit(root, "supply refused Context", only=["clutch/arrived.py"])
        # Ignoring HEAD even with pending intake leaves the refused snapshot unchanged.
        invalidated = await rig.owner.intake_snapshot() != before
        await rig.owner.scan()
        # Skipping the retry leaves the ticket untracked after its Context becomes valid.
        pending = await rig.checkout.git.status_porcelain(root, "--", "tickets/refused/")
        _, rc, committed, _ = await rig.checkout.git._call(root, "show", "main:tickets/refused/ticket.md")
        # Clearing status without publishing the actual ticket is not successful intake.
        assert (refused, invalidated, pending, rc, "- clutch/arrived.py" in committed) == (True, True, "", 0, True)
    finally:
        release.set()
        await finish(rig, run)
