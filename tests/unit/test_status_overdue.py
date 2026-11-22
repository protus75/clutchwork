"""Journal-only overdue thresholds and the status rendering."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for journal-only retro and calibration overdue thresholds, their resets and master switch, and their rendering in view status
# relates: [clutch/__main__.py, clutch/config.py, clutch/git.py, clutch/journal.py, clutch/retro.py, clutch/specs/__init__.py, clutch/status.py, tests/fakes.py]
# owner: engine
# verified: 45e4e081
# hash: 111f437c3db5a6ad5e085cb971ce1974821c4340e32c8b4a748194de37601c26

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import status
from clutch.config import Calibration, Retro
from clutch.journal import EventType
from tests.fakes import FakeJournal


def history(*, settled=0, merges=0, calls=0):
    journal = FakeJournal()
    for n in range(settled):
        journal.append(EventType.STATE_TRANSITION, {"to": "already_satisfied"}, ticket=f"settled-{n}")
    for n in range(merges):
        journal.append(EventType.STATE_TRANSITION, {"to": "merged", "commit": f"sha-{n}"}, ticket=f"merged-{n}")
    for n in range(calls):
        journal.append(EventType.EFFECT_COMPLETION, {}, key=f"llm/call-{n}/1/implement/1/1")
    return journal


def settings(**retro):
    return SimpleNamespace(retro=Retro(**retro), calibration=Calibration())


@pytest.mark.parametrize("count,enabled,expected", [(39, True, {}), (40, True, {"retro": "retro overdue: 40 tickets settled since the last retro; run `clutch engine retro`"}), (40, False, {})])
def test_settled_threshold_and_master_switch(count, enabled, expected):
    # Wrong: off-by-one threshold or ignore the master switch.
    assert status.overdue(history(settled=count).read(), settings(enabled=enabled)) == expected


def test_settled_counts_distinct_stems_and_resets_only_at_completed_report():
    journal = history(settled=39)
    journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="settled-0")
    # Wrong: count transitions rather than distinct stems.
    assert status.overdue(journal.read(), settings()) == {}
    journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="last")
    journal.append(EventType.EFFECT_INTENT, {}, key="retro/1")
    # Wrong: reset at report intent rather than completion.
    assert status.overdue(journal.read(), settings()) == {"retro": "retro overdue: 40 tickets settled since the last retro; run `clutch engine retro`"}
    journal.append(EventType.EFFECT_COMPLETION, {}, key="retro/1")
    # Wrong: retain counts across completed reports.
    assert status.overdue(journal.read(), settings()) == {}


@pytest.mark.parametrize("count", [99, 100])
def test_calibration_threshold_and_reset(count):
    journal = history(calls=count)
    expected = {"calibration": "calibration overdue: 100 Implement calls completed since the last calibration; run `clutch engine calibrate`"} if count == 100 else {}
    # Wrong: off-by-one threshold, wrong count or verb.
    assert status.overdue(journal.read(), settings()) == expected
    journal.append(EventType.SIGNAL, {"signal": "estimate_calibration"})
    # Wrong: ignore the calibration boundary.
    assert status.overdue(journal.read(), settings()) == {}


@pytest.mark.parametrize("kind,count", [("merges", 24), ("merges", 25), ("gate-failure", 4), ("gate-failure", 5)])
def test_other_retro_thresholds(kind, count):
    journal = history(merges=count if kind == "merges" else 0)
    if kind == "gate-failure":
        for n in range(count):
            journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed"}, ticket=f"failed-{n}")
    detail = "25 tickets merged" if kind == "merges" else "5 gate-failure events"
    expected = {"retro": f"retro overdue: {detail} since the last retro; run `clutch engine retro`"} if count in (25, 5) else {}
    # Wrong: use settled count for merges/spikes, ignore a trigger or an off-by-one threshold.
    assert status.overdue(journal.read(), settings()) == expected


def test_overdue_is_journal_only_and_renders_once(monkeypatch):
    from clutch import git, retro

    def forbidden(*args, **kwargs):
        raise AssertionError("overdue read git or production evidence")

    monkeypatch.setattr(git.Git, "_run", forbidden)
    monkeypatch.setattr(retro, "production_evidence", forbidden)
    lines = status.overdue(history(merges=25, calls=100).read(), settings())
    rendered = status.render(status.project([], overdue=lines.values()))
    # Wrong: omit or duplicate either reminder, or omit the list markers.
    assert rendered.split("overdue:\n", 1)[1].split("\n\n", 1)[0].splitlines() == [
        "- retro overdue: 25 tickets merged since the last retro; run `clutch engine retro`",
        "- calibration overdue: 100 Implement calls completed since the last calibration; run `clutch engine calibrate`",
    ]
    # Wrong: emit an empty overdue block for existing constructors.
    assert "overdue:" not in status.render(status.project([]))


@pytest.mark.asyncio
async def test_status_command_supplies_overdue_lines(monkeypatch):
    from pathlib import Path

    from clutch import __main__ as cli
    from clutch import retro, specs
    from tests.fakes import FakeClock, FakeFileSystem
    from tests.git_fake import GitFake

    config = settings()
    config.state_dir = Path("/state")
    config.box_policy = {}
    checkout = SimpleNamespace(config=config, repo=Path("/repo"), journal=history(merges=25, calls=100), fs=FakeFileSystem(), git=GitFake(rev_parse="head"), clock=FakeClock())
    monkeypatch.setattr(retro, "production_evidence", AsyncMock())
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: "spec fixture")
    monkeypatch.setattr(specs, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(version=1)))
    monkeypatch.setattr(cli.observe, "lock_holder", lambda path: None)
    projected = await cli._status(checkout)
    # Wrong: omit overdue at the command boundary, even though the pure helper works.
    assert projected.overdue == (
        "retro overdue: 25 tickets merged since the last retro; run `clutch engine retro`",
        "calibration overdue: 100 Implement calls completed since the last calibration; run `clutch engine calibrate`",
    )
