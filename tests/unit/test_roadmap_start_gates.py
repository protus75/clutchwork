import asyncio
from types import SimpleNamespace

import pytest

from clutch import roadmap
from clutch.runner import Refusal
from clutch.seams import ExecutableNotFound
from tests.unit.test_retro_recurrence import MemoryJournal
from tests.unit.test_roadmap_gate import RecordingExec


def test_fences_and_refusals():
    text = '### 0.5.0\n```start\ntool "a b"\n```\n```gate\nother arg\n```\n'
    assert roadmap.gates(text, "start") == {"0.5.0": (("tool", "a b"),)}
    assert roadmap.gates(text, "gate") == {"0.5.0": (("other", "arg"),)}
    for bad in ("```start\ntool\n```", "### 0.5.0\n```start\n\n```"):
        with pytest.raises(Refusal, match="start"):
            roadmap.gates(bad, "start")


def test_choose_held():
    row = roadmap.Row(1, "0.5.0", "target", "roadmap", "feature", "P1", "", (), "work", False, False, 1)
    held = roadmap.choose([row], states={}, files=set(), held={"0.5.0": "x"})
    assert held.ready == ()
    assert [(w.row, w.reason, w.road) for w in held.waits] == [(row, "start gate of 0.5.0 fails: x", "make the release's start block pass")]
    free = roadmap.choose([row], states={}, files=set())
    assert free.ready == (row,)
    assert free.waits == ()


@pytest.mark.parametrize("answer,passed", [((2, "", ""), False), (TimeoutError(), False), (ExecutableNotFound("check"), False), ((0, "", ""), True)])
def test_run_start(tmp_path, monkeypatch, answer, passed):
    path = tmp_path / roadmap.ROADMAP
    path.parent.mkdir()
    path.write_text("### 0.5.0\n```start\ncheck value\n```\n")
    c = SimpleNamespace(repo=tmp_path, exec_=RecordingExec([answer]), env={}, config=SimpleNamespace(drain=SimpleNamespace(max_ticket_minutes=7)), journal=MemoryJournal())
    monkeypatch.setattr(roadmap, "child_env", lambda *args: {"SAFE": "yes"})
    assert asyncio.run(roadmap.run_start(c, "0.5.0")) == (passed, ["check value"])
    assert c.exec_.calls == [(["check", "value"], {"cwd": tmp_path, "env": {"SAFE": "yes"}, "timeout": 420.0})]
    assert asyncio.run(roadmap.run_start(c, "0.6.0")) == (True, [])
    assert c.journal.events == []
