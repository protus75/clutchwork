"""Idle maintenance must not reserve the next implementation slot."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify idle poll admission and work detection.
# relates: [clutch/daemon.py, clutch/journal.py, clutch/runner.py, clutch/seams.py, clutch/serve.py, tests/fakes.py]
# owner: engine
# verified: 407dfd0f
# hash: 476ad6b2301ea5c18f40f9852bb434405dda87a7b2578e09a3f96c0acf288216

import asyncio
import hashlib
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import serve
from clutch.daemon import DaemonAdmission
from clutch.journal import EventType
from clutch.runner import Checkout
from clutch.seams import LocalFileSystem
from clutch.serve import Serve
from tests.fakes import FakeClock, FakeJournal


class PollFinished(Exception):
    pass


async def stop_poll(_):
    raise PollFinished


class Response:
    async def wait(self, work):
        return await work


@pytest.fixture
def owner(tmp_path):
    s = Serve.__new__(Serve)
    fs, clock = LocalFileSystem(), FakeClock()
    journal = FakeJournal(clock)
    git = SimpleNamespace(status_porcelain=AsyncMock(return_value=""), rev_parse=AsyncMock(return_value="head"), main_write=asyncio.Lock)
    s.checkout = Checkout(repo=tmp_path, config=None, env={}, exec_=None, fs=fs, clock=clock, journal=journal, git=git, sleep=stop_poll)
    s.scan_snapshot, s.scanned = None, {}
    s.report_arrivals, s.report_retry = set(), None
    s.read, s.stems = lambda stem: "ticket", lambda: []
    s.stopping = False
    s.responses = [Response() for _ in range(5)]
    s.queue = SimpleNamespace(pending={}, active=None, paused=False, hold_id=None, contexts={}, deliveries=[], process=AsyncMock())
    s.writers = {}
    s.control = SimpleNamespace(
        projection=SimpleNamespace(stop_requested=False, kill_requested=False, released_hold_ids=set()),
        inbox=SimpleNamespace(files=lambda: [], settle_admissions=AsyncMock()),
        poll=lambda: None,
        load_config=lambda: SimpleNamespace(report_inbox=tmp_path / "reports"),
    )
    s.storm = SimpleNamespace(_evidence=lambda: ({}, {}, set()))
    s.box = SimpleNamespace(root=tmp_path / "box", messages=lambda: [])
    s.check_upgrade = AsyncMock()
    admission = DaemonAdmission(AsyncMock(), max_runs=2)
    # Stand-ins count both gates while a genuine admission slot is occupied.
    admission._holding = 1
    admission.runs["held"] = SimpleNamespace()
    s.entries = []

    @asynccontextmanager
    async def exclusive():
        s.entries.append("exclusive")
        yield

    @asynccontextmanager
    async def mutations():
        s.entries.append("mutations")
        async with admission.exclusive():
            yield

    real_merging = admission.merging

    @asynccontextmanager
    async def merging():
        s.entries.append("merging")
        async with real_merging():
            yield

    admission.merging = merging
    admission.exclusive, admission.mutations = exclusive, mutations
    s.core = SimpleNamespace(admission=admission, scheduler=SimpleNamespace(_slot=asyncio.Lock()))
    return s


async def poll(owner, name):
    with pytest.raises(PollFinished):
        await getattr(owner, name)()


@pytest.mark.asyncio
async def test_scan_inputs_and_own_writes(owner, monkeypatch):
    async def intake_writes(*args, **kwargs):
        owner.checkout.git.rev_parse.return_value = "intake-committed-head"

    monkeypatch.setattr(serve, "intake", AsyncMock(side_effect=intake_writes))
    await owner.scan()
    owner.entries.clear()
    owner.checkout.journal.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="held")
    owner.checkout.journal.append(EventType.EFFECT_INTENT, {}, ticket="held", key="implement/held")
    await owner.scan()
    # A journal-wide invalidation would acquire both gates here.
    assert owner.entries == []
    owner.checkout.git.rev_parse.return_value = "merged-head"
    await owner.scan()
    # With no pending ticket, a merge does not unblock intake validation.
    assert owner.entries == []
    owner.entries.clear()
    owner.checkout.fs.write(owner.checkout.repo / "tickets/new/ticket.md", b"new")
    owner.stems = lambda: ["new"]
    await owner.scan()
    # Dropping ticket inputs from the snapshot misses this new stem.
    assert owner.entries == []
    owner.entries.clear()
    await owner.scan()
    # Forgetting the post-intake snapshot re-enters on intake's own writes.
    assert owner.entries == []


@pytest.mark.asyncio
async def test_pending_stem_state_retries_intake(owner, monkeypatch):
    monkeypatch.setattr(serve, "intake", AsyncMock())
    owner.checkout.git.status_porcelain.return_value = " M tickets/refused/ticket.md\n"
    await owner.scan()
    owner.entries.clear()
    owner.checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="refused")
    await owner.scan()
    # Omitting pending stems' last states leaves a refusal permanently cached.
    assert owner.entries == []


@pytest.mark.asyncio
async def test_watch_idle_skips_publication_gate(owner):
    owner.scan = AsyncMock(return_value={})

    class Watcher:
        _waits = {}

        async def run(self, changes):
            async for _ in changes:
                raise AssertionError("idle watch published a change")

    owner.core.watcher = Watcher()
    await poll(owner, "watch")
    assert owner.entries == []


@pytest.mark.asyncio
async def test_watch_changed_publication_enters_once(owner):
    owner.scan = AsyncMock(return_value={"changed": "text"})
    published = []

    class Watcher:
        _waits = {}

        async def run(self, changes):
            try:
                published.append(await anext(changes))
            finally:
                await changes.aclose()

    owner.core.watcher = Watcher()
    await owner.watch()
    # Omitting publication or its gate changes this pair.
    assert (published, owner.entries) == (["changed"], [])


@pytest.mark.asyncio
@pytest.mark.parametrize("work", ["idle", "paused", "queue", "decision", "completed", "held-decision", "stale", "inbox", "stop", "kill", "writer", "active", "released"])
async def test_merge_work(owner, work):
    if work in {"paused", "queue"}:
        owner.queue.pending = {"waiting": object()}
        owner.queue.paused = work == "paused"
    if work in {"decision", "completed", "held-decision", "stale"}:
        body = dict(
            kind="control_decision",
            request_id="confirm-1",
            lifecycle_id="life",
            verb="confirm",
            hold_id="hold" if work == "held-decision" else None,
            decision="stale" if work == "stale" else "accepted",
            reason="matching",
            stem="draft",
            actor="operator",
        )
        owner.checkout.journal.append(EventType.SIGNAL, body)
        if work == "completed":
            owner.checkout.journal.append(EventType.EFFECT_COMPLETION, {"result": {}}, key="ticket-plane/draft/confirm/confirm-1")
    if work == "inbox":
        owner.control.inbox.files = lambda: [owner.checkout.repo / "request.json"]
    if work in {"stop", "kill"}:
        setattr(owner.control.projection, f"{work}_requested", True)
    if work == "writer":
        owner.writers["ended"] = SimpleNamespace(continuations={})
    if work == "released":
        owner.queue.paused, owner.queue.hold_id = True, "released-hold"
        owner.control.projection.released_hold_ids.add("released-hold")
    if work == "active":
        owner.queue.active = "merging"
    await poll(owner, "merge")
    # Each row isolates one admission reason; completed/held/stale decisions are idle.
    assert owner.entries == ([] if work in {"idle", "paused", "decision", "completed", "held-decision", "stale", "inbox"} else ["merging"])


@pytest.mark.asyncio
async def test_idle_merge_detects_upgrade(owner):
    owner.trees, owner.upgrade = ("old",), None
    owner.engine_trees = AsyncMock(return_value=("new",))
    owner.check_upgrade = lambda: Serve.check_upgrade(owner)
    await poll(owner, "merge")
    assert (owner.upgrade, owner.entries) == (("new",), [])


@pytest.mark.asyncio
@pytest.mark.parametrize("work", ["idle", "unread", "not-due", "due", "recover"])
async def test_box_work(owner, monkeypatch, work):
    # report_intake's effects remain under the real production poll's gate.
    monkeypatch.setattr(serve, "snapshot_config", lambda config: config)
    intake = []
    monkeypatch.setattr(serve.triage, "report_intake", lambda c: intake.append(c))
    if work in {"unread", "not-due", "due"}:
        path = owner.checkout.repo / "reports/broken.json"
        owner.checkout.fs.write(path, b"broken")
        if work != "unread":
            owner.report_arrivals.add(hashlib.sha256(str(path.resolve()).encode()).hexdigest())
            owner.report_retry = owner.checkout.clock()
            owner.checkout.clock.advance(30 if work == "due" else 29)
    if work == "recover":
        owner.storm._evidence = lambda: ({"trip": ({}, 6)}, {}, set())
    await poll(owner, "box_intake")
    expected = [] if work in {"idle", "not-due"} else ["mutations", "exclusive"]
    # Skipping the gate or skipping ingestion changes this pair.
    assert (owner.entries, len(intake)) == (expected, 0 if not expected else 1)
