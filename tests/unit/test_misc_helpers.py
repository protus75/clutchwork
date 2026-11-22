"""Moved helpers keep their data contracts while using the shared fake seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that each shared helper in tests/misc_helpers.py keeps its data contract and wires the in-memory fake seams
# relates: [clutch/control.py, clutch/journal.py, clutch/llm.py, clutch/seams.py, tests/config_fixture.py, tests/fakes.py, tests/git_fake.py]
# owner: engine
# verified: ff6ac88d
# hash: 70b770d7c17623e142c29499b4e65ca54a6a3edac8e96d7138d5cc9e46b678aa

import asyncio
import json

import yaml

from clutch.control import ControlProjection
from clutch.journal import EventType
from clutch.llm import FakeLLM
from clutch.seams import LocalFileSystem
from tests import misc_helpers as helpers
from tests.config_fixture import build_config
from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeJournal
from tests.git_fake import GitFake
from tests.misc_helpers import (
    PROPOSAL,
    Rig,
    _box,
    _events,
    _failure,
    _routes,
    _run,
    arrival,
    block,
    bug_reply,
    commit_lock,
    completed,
    decision,
    merged,
    raw_report,
    requisition_reply,
    rig,
)
from tests.stage_replies import requisition_reply as shared_requisition_reply


def test_imports():
    """A missing export or copied requisition builder changes this identity list."""
    names = (
        "PROPOSAL",
        "Rig",
        "_box",
        "_events",
        "_failure",
        "_routes",
        "_run",
        "arrival",
        "block",
        "bug_reply",
        "commit_lock",
        "completed",
        "decision",
        "merged",
        "raw_report",
        "requisition_reply",
        "rig",
    )
    assert tuple(getattr(helpers, name) for name in names) == (
        PROPOSAL,
        Rig,
        _box,
        _events,
        _failure,
        _routes,
        _run,
        arrival,
        block,
        bug_reply,
        commit_lock,
        completed,
        decision,
        merged,
        raw_report,
        shared_requisition_reply,
        rig,
    )


def test_commit_lock(tmp_path):
    """The old real CommitLock creates a lock file when entered."""
    lock = commit_lock(tmp_path / "state")

    async def enter():
        async with lock:
            return isinstance(lock, asyncio.Lock), lock.locked(), list(tmp_path.rglob("*"))

    assert asyncio.run(enter()) == (True, True, [])


def test_arrival(tmp_path):
    """Writing outside the supplied root or ignoring report updates changes this snapshot."""
    root = tmp_path / "host"
    path = arrival(root, summary="arrival marker")
    report = json.loads(path.read_text())
    assert (
        path,
        sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()),
        report,
        json.loads((root / "replay.json").read_text()),
        (root / "log.txt").read_text(),
    ) == (
        root / "inbox/a.json",
        ["host/inbox/a.json", "host/log.txt", "host/replay.json"],
        {**raw_report(), "summary": "arrival marker", "evidence": {"replay": "replay.json", "log": "log.txt"}},
        {"initial_state": {"score": 0}, "actions": []},
        "structured log\n",
    )


def test_raw_report():
    """Dropping self-diagnosis fields or overwriting caller updates changes this report."""
    assert raw_report("self_diagnosed", app_version="9.8", summary="distinct") == {
        "schema_version": 1,
        "origin": "self_diagnosed",
        "summary": "distinct",
        "app_commit": "host-supplied-evidence",
        "app_version": "9.8",
        "game_slug": "score2",
        "anomaly_code": "illegal42",
        "location": "app/view.py:123",
    }


def test_block():
    """Selecting the first block instead of the named block returns the decoy."""
    prompt = "<<clutch-data:begin other>>\ndecoy\n<<clutch-data:end other>>\n<<clutch-data:begin chosen>>\nmarker\nline two\n<<clutch-data:end chosen>>"
    assert block(prompt, "chosen") == "marker\nline two"


def test_box(tmp_path):
    """A different box root loses the queued report instead of preserving its caller-owned files."""
    first = _box(tmp_path)
    id = _failure(first)
    second = _box(tmp_path)
    assert (isinstance(first.fs, LocalFileSystem), second.get(id).summary, second.root) == (
        True,
        "current broken behavior",
        tmp_path / ".clutch/state/box",
    )


def test_events(tmp_path):
    """Reading a new journal instead of the root's retained journal loses the marker."""
    _, journal, _ = helpers._state(tmp_path)
    event = journal.append(EventType.SIGNAL, {"kind": "marker"}, ticket="distinct")
    assert _events(tmp_path) == [event]


def test_failure(tmp_path):
    """Enqueuing a suggestion instead of a check failure changes its routing fields."""
    box = _box(tmp_path)
    message = box.get(_failure(box))
    assert (message.message_class, message.origin, message.summary, message.stage, message.outcome) == (
        "failure_report",
        "test",
        "current broken behavior",
        "check",
        "gate_failed",
    )


def test_routes(tmp_path):
    """Replacing existing routes or omitting any author/review tier changes this list."""
    path = tmp_path / "config.yaml"
    original = build_config(routing=[{"tier": "high", "surface": "implement", "candidates": [{"provider": "claude"}]}])
    path.write_text(original)
    _routes(tmp_path)
    config = yaml.safe_load(path.read_text())
    expected = yaml.safe_load(original)
    expected["routing"] += [{"tier": tier, "surface": surface, "candidates": [{"provider": "claude"}]} for surface in ("author", "review") for tier in ("low", "medium", "high", "max")]
    assert config == expected


def test_run(tmp_path, monkeypatch):
    """An unpatched CLI constructor or wrong invocation breaks the captured wiring."""
    llm = FakeLLM(["distinct"])
    fs, journal, git = helpers._state(tmp_path)
    calls = []

    def main(argv, **kwargs):
        m = helpers.main_module
        calls.append((argv, kwargs["cwd"], kwargs["env"], kwargs["clock"], m.ProviderLLM(), m.LocalFileSystem(), m.Journal(), m.Git(), type(m.SubprocessExec()), type(m.CommitLock())))
        return 37

    monkeypatch.setattr(helpers.main_module, "main", main)
    assert (_run(tmp_path, monkeypatch, llm), calls) == (
        37,
        [
            (["box", "triage"], tmp_path, helpers.ENV, journal.clock, llm, fs, journal, git, FakeExec, asyncio.Lock),
        ],
    )


def test_bug_reply():
    """Leaving feature kind or failing to carry the stem's evidence changes the ticket."""
    data = json.loads(bug_reply("distinct-bug", prose="unique explanation"))
    text = data["ticket"]
    assert (
        data["stem"],
        "kind: bug" in text,
        "kind: feature" in text,
        "- tickets/distinct-bug/evidence/replay.json" in text,
        "- tests/report_regression.py" in text.split("## Scope fence\n")[1].split("\n## ")[0],
        text.endswith("## Regression\n```\npython tests/report_regression.py\n```\n- carries: tests/report_regression.py\n"),
        "unique explanation" in text,
    ) == ("distinct-bug", True, False, True, True, True, True)


def test_requisition_reply():
    """A wrapper or copy instead of the canonical builder fails identity and shaped values."""
    assert (requisition_reply is shared_requisition_reply, json.loads(requisition_reply("snag", [{"message": "distinct"}], ["child"]))) == (
        True,
        {"verdict": "snag", "summary": "reviewed", "findings": [{"message": "distinct"}], "dependents": ["child"]},
    )


def test_proposal():
    """Losing non-ASCII evidence or either ordered spec path changes the proposal."""
    assert PROPOSAL == {"fixed_failure": "Observed café failure", "overcorrection_risk": "Rejecting useful inputs", "proposed_spec_paths": ["specs/review.md", "specs/author.md"]}


def test_completed():
    """Hardcoding sequence 1 or emitting an intent produces a different event."""
    journal = FakeJournal()
    event = completed(journal, 7)
    assert (event.type, event.key, event.body, journal.read()) == (
        EventType.EFFECT_COMPLETION,
        "retro/7",
        {"result": {"commit": "receipt"}},
        [event],
    )


def test_merged():
    """Ignoring the caller's stem/commit or emitting the wrong state changes the event."""
    journal = FakeJournal()
    event = merged(journal, "distinct-ticket", "unique-sha")
    assert (event.type, event.ticket, event.body, journal.read()) == (
        EventType.STATE_TRANSITION,
        "distinct-ticket",
        {"to": "merged", "commit": "unique-sha"},
        [event],
    )


def test_rig(tmp_path):
    """The old checkout uses a real journal; ignoring script, clock or fs breaks wiring."""
    c, writer, hook, llm = rig(tmp_path, ["distinct reply"])
    asyncio.run(c.sleep(19))
    assert (
        type(c.git),
        type(c.exec_),
        type(c.fs),
        type(c.journal),
        type(c.clock),
        c.clock().second,
        c.journal.clock is c.clock,
        writer.stages.driver.journal is c.journal,
        writer.stages.driver.spool._fs is c.fs,
        writer.stages.driver.retry_cap,
        hook.checkout is c,
        hook.pipeline is writer,
        writer.stages.driver.llm is llm,
        asyncio.run(llm.call(None)).text,
        list(tmp_path.iterdir()),
    ) == (
        GitFake,
        FakeExec,
        FakeFileSystem,
        FakeJournal,
        FakeClock,
        19,
        True,
        True,
        True,
        0,
        True,
        True,
        True,
        "distinct reply",
        [],
    )


def test_decision():
    """Ignoring any caller override produces the default kill decision instead."""
    assert decision("distinct", life="life-9", verb="resume", hold="hold-2", result="stale", reason="unique reason") == {
        "kind": helpers.control.CONTROL_DECISION,
        "request_id": "distinct",
        "lifecycle_id": "life-9",
        "verb": "resume",
        "hold_id": "hold-2",
        "decision": "stale",
        "reason": "unique reason",
    }


def test_control_rig(tmp_path):
    """Real filesystem/journal seams write disk; broken enumeration loses a kill request."""
    r = Rig(tmp_path, life="distinct-life")
    path = r.publish("kill-marker")
    r.inbox.consume()
    r.reconstruct().consume()
    assert (type(r.fs), type(r.journal), json.loads(r.fs.read_bytes(path)), r.decisions(), r.changes, r.applications, list(tmp_path.iterdir())) == (
        FakeFileSystem,
        FakeJournal,
        {"request_id": "kill-marker", "lifecycle_id": "distinct-life", "verb": "kill", "hold_id": None},
        [decision("kill-marker", life="distinct-life")],
        [ControlProjection("distinct-life", kill_requested=True)],
        [ControlProjection("distinct-life", kill_requested=True)] * 2,
        [],
    )
