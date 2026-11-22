# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for loop_helpers: exports, Rig file writes, fake Time deadlines, ticket text formatting, turn and import closure
# relates: [tests/fakes.py, tests/loop_helpers.py]
# owner: engine
# verified: 82d23237
# hash: 38b78fb2336cc4d89849331dad6ef552987ecaed764e6e9fba4b398a023e7373
import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from tests import fakes, loop_helpers
from tests.loop_helpers import Rig, Time, scheduler_import_closure, text, turn


def test_exports():
    assert all(
        getattr(loop_helpers, name) is value
        for name, value in {
            "Rig": Rig,
            "Time": Time,
            "text": text,
            "turn": turn,
            "scheduler_import_closure": scheduler_import_closure,
        }.items()
    )


def test_rig_writes_under_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    rig = Rig(root)
    ticket = rig.add("example", priority="P0")
    assert ticket.stem == "example"
    assert (root / "tickets/example/ticket.md").read_text() == rig.files["example"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["root"]


@pytest.mark.asyncio
async def test_time_wakes_at_deadline():
    clock = Time()
    start = clock()
    sleeper = asyncio.create_task(clock.sleep(5))
    await turn()
    clock.advance(4)
    assert not clock.waits[0][1].done()
    clock.advance(1)
    await turn()
    assert sleeper.done()
    assert clock() == start + timedelta(seconds=5) == datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=5)
    await sleeper


def test_text_formats_parameters():
    result = text("P0", "draft", "- parent")
    assert "state: draft\nsource: human\npriority: P0" in result
    assert "## Depends on\n- parent" in result


@pytest.mark.asyncio
async def test_turn_is_shared_and_yields():
    assert turn is fakes.turn
    events = []
    asyncio.get_running_loop().call_soon(events.append, "callback")
    await turn()
    assert events == ["callback"]


def test_scheduler_import_closure_uses_supplied_sources():
    sources = {"clutch.__main__": "from clutch import a", "clutch": "", "clutch.a": "import clutch.b", "clutch.b": "", "clutch.unused": ""}
    assert scheduler_import_closure(sources) == {"clutch.__main__", "clutch", "clutch.a", "clutch.b"}
