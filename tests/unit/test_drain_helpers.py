# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for tests/drain_helpers.py exports: fake clock and exec, root and ticket fixtures, drain and reentry runners, Script dispatch and journal query helpers.
# relates: [clutch/caps.py, clutch/journal.py, clutch/runner.py, tests/cli_helpers.py, tests/drain_helpers.py, tests/fakes.py]
# owner: tests/drain_helpers.py
# verified: 7ad3c1c2
# hash: 3dafb9579a97385ead6c87fd5faba6964657d1c369e2f25592331d890bbc2999
import asyncio
from types import SimpleNamespace

import pytest

from clutch.journal import EventType
from tests import drain_helpers as h
from tests.cli_helpers import git_fake
from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeJournal


def test_exports():
    assert all(
        hasattr(h, n) for n in ("Clock NoChild START Script commit_ticket confirmed drain journal make_root mechanical_first offer_events pause_checkout reentry_drain retry_draws root tos").split()
    )
    assert h.drain is not h.reentry_drain


def test_clock():
    assert h.Clock is FakeClock


def test_no_child():
    assert h.NoChild is FakeExec


def test_start():
    assert h.START.isoformat() == "2026-01-01T00:00:00+00:00"


def test_make_root(tmp_path):
    root = h.make_root(tmp_path, "\n# caps\n")
    assert not (root / ".git").exists()
    assert (root / "config.yaml").read_text().endswith("# caps\n")


def test_root_fixture(tmp_path):
    assert h.root.__wrapped__(tmp_path) == tmp_path / "repo"


def test_commit_ticket(tmp_path):
    h.commit_ticket(tmp_path, "work", "ticket text")
    assert (tmp_path / "tickets/work/ticket.md").read_text() == "ticket text"
    assert [c[0] for c in git_fake(tmp_path).calls] == ["add", "commit"]


def test_confirmed():
    assert "state: confirmed\nsource: human\npriority: P1" in h.confirmed("none", "P1")


def test_journal(tmp_path):
    assert isinstance(h.journal(tmp_path), FakeJournal)


def test_drain(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(h.main_module, "main", lambda argv, **kw: calls.append((argv, kw)) or 17)
    script = h.Script()
    assert h.drain(tmp_path, script) == 17
    assert calls[0][0] == ["engine", "drain"] and calls[0][1]["pipeline"] is script


def test_reentry_drain(tmp_path, monkeypatch):
    (tmp_path / "clutch").mkdir()
    monkeypatch.setattr(h.main_module, "main", lambda argv, **kw: 13)
    code, llm = h.reentry_drain(tmp_path, [])
    assert code == 13 and llm.requests == []
    assert (tmp_path / "clutch/thing.py").read_text() == "ok base\n"
    assert git_fake(tmp_path).calls[0][0] == "commit"


def test_script(tmp_path):
    clock = FakeClock()
    journal = FakeJournal(clock)
    checkout = SimpleNamespace(config=SimpleNamespace(state_dir=tmp_path), clock=clock, journal=journal)
    script = h.Script({"work": ["gate_failed"]})
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(h, "with_retro_driver", lambda checkout, dispatch: dispatch)
        result = asyncio.run(script(checkout)(SimpleNamespace(stem="work")))
    assert result == "gate_failed" and journal.read()[0].ticket == "work"
    assert script.calls == ["work"] and script.lock_held == [False]


def test_retry_draws(tmp_path, monkeypatch):
    from clutch.caps import consume

    j = FakeJournal()
    consume(j, "work", "retry", "one")
    monkeypatch.setattr(h, "journal", lambda root: j)
    assert h.retry_draws(tmp_path, "work") == 1


def test_tos(tmp_path, monkeypatch):
    j = FakeJournal()
    j.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="work")
    j.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="other")
    monkeypatch.setattr(h, "journal", lambda root: j)
    assert h.tos(tmp_path, "work") == ["running"]


def test_offer_events(tmp_path, monkeypatch):
    j = FakeJournal()
    event = j.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="work")
    j.append(EventType.CHECKPOINT, {"unrelated": True})
    monkeypatch.setattr(h, "journal", lambda root: j)
    assert h.offer_events(tmp_path) == [event]


def test_pause_checkout(tmp_path):
    root = h.make_root(tmp_path)
    checkout = h.pause_checkout(root)
    assert checkout.git is git_fake(root) and isinstance(checkout.exec_, FakeExec)
    assert isinstance(checkout.fs, FakeFileSystem)


def test_mechanical_first(monkeypatch):
    from clutch import runner

    called = h.mechanical_first(monkeypatch, "work", workspace=False)
    result = asyncio.run(runner.run_stages(None, SimpleNamespace(stem="work")))
    assert called == ["work"] and result.results["implement"].outcome == "premise_failed"


def test_drain_in_process(tmp_path):
    root = h.make_root(tmp_path)
    assert h.drain(root, h.Script()) == 0


def test_reentry_in_process(tmp_path):
    root = h.make_root(tmp_path)
    code, llm = h.reentry_drain(root, [])
    assert code == 0 and llm.requests == []
