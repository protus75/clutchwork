# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that queue.json records idle free-slot reasons (fence overlap waiting, max_unmerged hold) only on change and that the snapshot and watch queue show them as row status while the engine is alive
# relates: [clutch/box.py, clutch/config.py, clutch/drain.py, clutch/observe.py, clutch/status.py, tests/config_fixture.py, tests/dispatch_settle.py]
# owner: engine
# verified: 5a90be6a
# hash: d308fd0d2482b0b3d9237ddf234d8c93ce7505691da22618787bbc76add5c934
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import observe, status
from clutch.box import Box
from clutch.config import Parallel
from clutch.drain import write_queue
from tests.config_fixture import build_config
from tests.unit.test_menu_admission import dispatch_ticket, fake_snapshot_inputs
from tests.unit.test_scheduler_parallel_fill import rig, ticket


def test_write_queue_optional_fields():
    writes = []
    fs = NS(write=lambda path, data: writes.append(json.loads(data)))

    def clock():
        return datetime(2026, 1, 1, tzinfo=UTC)

    write_queue(Path("/state"), fs, clock, [ticket("b")], {"b": ["a"]}, None)
    assert writes[-1]["waiting"] == {"b": ["a"]}
    assert "hold" not in writes[-1]
    write_queue(Path("/state"), fs, clock, [ticket("b")], {}, None)
    assert set(writes[-1]) == {"at", "order", "runs_before"}


@pytest.mark.asyncio
async def test_overlap_idle_changes_only():
    obj, writes, _, _ = rig([ticket("x-stem", path="src/x")], Parallel(enabled=True, max_runs=3))
    obj.flying["in-flight-stem"] = ticket("in-flight-stem", path="src")
    assert await obj.dispatch_next() is None
    assert writes[-1]["waiting"] == {"x-stem": ["in-flight-stem"]}
    assert await obj.dispatch_next() is None
    assert len(writes) == 1
    obj.flying["another"] = ticket("another", path="src/x")
    assert await obj.dispatch_next() is None
    assert len(writes) == 2
    assert writes[-1]["waiting"] == {"x-stem": ["another", "in-flight-stem"]}


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_merge_hold(enabled):
    obj, writes, _, _ = rig([ticket("ready")], Parallel(enabled=enabled, max_runs=2))
    obj.completed_unmerged = lambda: 1
    assert await obj.dispatch_next() is None
    assert writes[-1]["hold"] == "max_unmerged"
    assert writes[-1]["order"] == ["ready"]


@pytest.mark.parametrize(
    "reason,expected,key",
    [
        ({"waiting": {"queued": ["busy"]}}, "waits for a free slot: overlaps busy", "slot_overlap"),
        ({"hold": "max_unmerged"}, "waits for merges: max_unmerged finished tickets wait to merge", "merge_wait"),
    ],
)
def test_observe_reasons(tmp_path, monkeypatch, reason, expected, key):
    root = tmp_path
    (root / "config").write_text(build_config())
    state = root / "state"
    state.mkdir()
    (state / "queue.json").write_text(json.dumps({"order": ["queued"], "runs_before": {}, **reason}))
    item = NS(**{**vars(dispatch_ticket()), "stem": "queued"})
    monkeypatch.setattr(observe, "help_payload", lambda: ({k: {"what": k, "text": k} for k in __import__("clutch.help", fromlist=["TOPICS"]).TOPICS}, []))
    monkeypatch.setattr(Box, "messages", lambda self: [])
    monkeypatch.setattr(observe, "journal", lambda *a: [])
    monkeypatch.setattr(observe, "journal_facts", lambda state, events: status.admission_facts(events))
    monkeypatch.setattr(observe, "load_tickets", lambda *a: ({"queued": item}, {}))
    monkeypatch.setattr(observe, "uncommitted_tickets", lambda *a: (set(), set()))
    monkeypatch.setattr(observe, "committed_ticket_shas", lambda *a: {"queued": "blob"})
    monkeypatch.setattr(observe, "commits", lambda *a: {})
    monkeypatch.setattr(observe, "held", lambda *a: set())
    monkeypatch.setattr(observe, "operator_holds", lambda *a: set())
    monkeypatch.setattr(observe, "running_stems", lambda *a: [])
    monkeypatch.setattr(observe, "ticket_menu_inputs", fake_snapshot_inputs)
    monkeypatch.setattr(observe, "lock_holder", lambda *a: datetime(2026, 1, 1, tzinfo=UTC))
    monkeypatch.setattr(observe, "lock_display", lambda state, name: ("held", "serve") if name == "clutch.lock" else ("", None))
    ctx = observe.Context(root, state, root / "config", None, None, None)
    row = observe.snapshot(ctx)["rows"][0]
    assert row["status"] == expected
    assert row["help"]["status"] == "status." + key
    monkeypatch.setattr(observe, "lock_holder", lambda *a: None)
    monkeypatch.setattr(observe, "lock_display", lambda *a: ("", None))
    row = observe.snapshot(ctx)["rows"][0]
    assert row["status"] == "ready"
    assert row["help"]["status"] == "status.ready"
    monkeypatch.setattr(Path, "glob", lambda *a: [root / "tickets/queued/ticket.md"])
    monkeypatch.setattr(observe, "frontmatter", lambda *a: {"state": "confirmed", "priority": "P1"})
    monkeypatch.setattr(observe, "depends", lambda *a: [])
    assert observe.queue(ctx, [], {}, set(), set(), alive=True) == [("P1", "queued", expected)]
    assert observe.queue(ctx, [], {}, set(), set()) == [("P1", "queued", "ready, not run yet")]


@pytest.mark.asyncio
async def test_barrier_and_dispatching_pass():
    from clutch.drain import SKIP_LIMIT
    from tests.dispatch_settle import dispatch_settled

    first = ticket("first", "P0", path="src/a")
    second = ticket("second", "P1", path="src/a/deep")
    disjoint = ticket("disjoint", path="docs")
    obj, writes, _, _ = rig([first, second, disjoint], Parallel(enabled=True, max_runs=2))
    obj.flying["busy"] = ticket("busy", path="src/a/file")
    obj.skips["first"] = SKIP_LIMIT
    assert await dispatch_settled(obj) is disjoint
    assert writes[-1]["waiting"] == {"first": ["busy"], "second": ["first"]}
