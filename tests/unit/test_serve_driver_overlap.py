import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from clutch import roadmap, serve
from clutch.journal import EventType
from tests.fakes import FakeJournal


@dataclass(frozen=True)
class Checkout:
    repo: object
    journal: object
    config: object
    git: object = None


@pytest.fixture
def owner(tmp_path, monkeypatch):
    s = object.__new__(serve.Serve)
    s.checkout = Checkout(tmp_path, FakeJournal(), "old")
    s.driven, s.stopping, s.upgrade = None, False, None
    s.writers = {}
    s.log = object()
    s.control = SimpleNamespace(
        poll=lambda: None,
        load_config=lambda: "snapshot",
        projection=SimpleNamespace(kill_requested=False, stop_requested=False, pause_id=None, released_hold_ids=set()),
        providers=SimpleNamespace(active=False),
        admission=None,
    )
    s.storm = SimpleNamespace(held_stages=lambda: {})
    s.retro_pending = lambda: False
    monkeypatch.setattr(serve, "snapshot_config", lambda value: value)
    return s


def test_select_admits_while_pass_pending(owner):
    (owner.checkout.repo / "docs").mkdir()
    (owner.checkout.repo / roadmap.ROADMAP).touch()
    ticket = SimpleNamespace(stem="new")
    # The old driver_pending admission hold rejects this otherwise eligible ticket.
    assert owner.select(ticket, "implement")
    owner.retro_pending = lambda: True
    # Removing both holds would admit this same ticket during a retro.
    assert not owner.select(ticket, "implement")


@pytest.mark.asyncio
async def test_run_driver_does_not_take_mutations(owner):
    entered = []

    @asynccontextmanager
    async def mutations():
        entered.append(True)
        yield

    async def driver(c, log):
        # Moving the settle snapshot after the await leaves driven at None here.
        assert owner.driven == 2
        # Passing the original checkout or log loses the configuration snapshot.
        assert (c.config, log) == ("snapshot", owner.log)

    for stem in ("one", "two"):
        owner.checkout.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket=stem)
    owner.mutations, owner.driver = mutations, driver
    await owner.run_driver()
    # Wrapping run_driver in mutations records an entry even if the driver succeeds.
    assert entered == []


@pytest.mark.asyncio
async def test_main_write_orders_pass_and_merge(owner):
    lock = asyncio.Lock()
    owner.checkout = Checkout(owner.checkout.repo, owner.checkout.journal, "old", SimpleNamespace(main_write=lambda: lock))
    entered, release, merging = (asyncio.Event() for _ in range(3))
    order = []

    async def driver(c, log):
        async with c.git.main_write():
            order.append("pass")
            entered.set()
            await release.wait()
            order.append("release")

    async def merge():
        merging.set()
        async with owner.checkout.git.main_write():
            order.append("merge")

    owner.driver = driver
    passing = asyncio.create_task(owner.run_driver())
    await entered.wait()
    merging_task = asyncio.create_task(merge())
    try:
        await merging.wait()
        # A merge bypassing the shared gate has already appended its entry here.
        assert order == ["pass"]
    finally:
        release.set()
        await asyncio.gather(passing, merging_task)
    # A merge using a different lock enters before the pass releases main.
    assert order == ["pass", "release", "merge"]


@pytest.mark.asyncio
async def test_upgrade_idle_and_wait_driver(owner):
    owner.core = SimpleNamespace(admission=SimpleNamespace(idle=lambda: True), scheduler=SimpleNamespace(occupied=lambda: False))
    owner.queue = None
    # The class default also supports Serve instances built without __init__.
    assert owner.upgrade_idle()
    release = asyncio.Event()
    owner.driver_task = asyncio.create_task(release.wait())
    # Omitting the task check lets an upgrade or retro start beside the pass.
    assert not owner.upgrade_idle()
    release.set()
    # Returning the task result rather than None leaks Event.wait's True.
    assert await owner.wait_driver() is None
    # Merely awaiting without clearing leaves a stale task and blocks idle forever.
    assert owner.driver_task is None
    assert owner.upgrade_idle()

    error = RuntimeError("driver failed")

    async def failing():
        raise error

    owner.driver_task = asyncio.create_task(failing())
    # Swallowing or replacing the error hides the original driver failure.
    assert await owner.wait_driver() is error
    assert owner.driver_task is None
    assert await owner.wait_driver() is None
