# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the roadmap driver step authors rows and sends a digest notification, and that drain calls the driver at start and after each settle
# relates: [clutch/__main__.py, clutch/journal.py, clutch/llm.py, clutch/roadmap.py, tests/integration/test_cli.py, tests/integration/test_drain.py]
# owner: clutch/roadmap.py
# verified: d32c32ad
# hash: 5134096758b0056a184eee811b1ffcb8637ee8a4ebdc3ec884d94d488c0818cd
import asyncio
import sys

import pytest
import yaml

from clutch import __main__ as cli
from clutch import roadmap
from clutch.journal import EventType
from clutch.llm import FakeLLM
from tests.integration.test_cli import ENV, git_out
from tests.integration.test_drain import Clock, Script, commit_ticket, confirmed, make_root, pause_checkout
from tests.integration.test_roadmap_author import setup_repo
from tests.integration.test_triage import author_reply, requisition_reply
from tests.unit.test_phase_events import RecordingLog

pytestmark = pytest.mark.disk_io_skip


def test_driver_step_authors_and_digests(tmp_path, monkeypatch):
    root, _ = setup_repo(tmp_path)
    config = root / "config.yaml"
    data = yaml.safe_load(config.read_text())
    digest = tmp_path / "digest.txt"
    data["notify"] = [sys.executable, "-c", f"import pathlib,sys; pathlib.Path({str(digest)!r}).write_text(sys.argv[1])"]
    config.write_text(yaml.safe_dump(data))
    git_out(root, "add", "config.yaml")
    git_out(root, "commit", "-m", "configure notify")
    c = pause_checkout(root)
    llm = FakeLLM([author_reply("first-row"), requisition_reply("approve")])
    monkeypatch.setattr(cli, "ProviderLLM", lambda *args, **kwargs: llm)
    asyncio.run(cli.build_driver()(c, RecordingLog()))
    assert git_out(root, "log", "-2", "--format=%s").splitlines() == ["clutch(roadmap): author first-row", "clutch(first-row): ticket"]
    text = digest.read_text()
    assert text.startswith("roadmap digest 0\n") and "roadmap: authored row 1 first-row" in text
    assert "next:" in text and text.splitlines()[-1].startswith("spend: $")
    assert any(e.type == EventType.EFFECT_COMPLETION and e.key == "notify/roadmap/digest/0" for e in c.journal.read())
    head = git_out(root, "rev-parse", "HEAD")
    digest.write_text("sentinel")
    empty = FakeLLM([])
    monkeypatch.setattr(cli, "ProviderLLM", lambda *args, **kwargs: empty)
    asyncio.run(cli.build_driver()(c, RecordingLog()))
    assert not empty.requests and digest.read_text() == "sentinel" and git_out(root, "rev-parse", "HEAD") == head


@pytest.mark.parametrize("present", [True, False])
def test_drain_calls_driver_at_start_and_after_each_settle(tmp_path, monkeypatch, present):
    root = make_root(tmp_path)
    commit_ticket(root, "one", confirmed(priority="P1"))
    commit_ticket(root, "two", confirmed(priority="P2"))
    if present:
        (root / "docs").mkdir(exist_ok=True)
        (root / roadmap.ROADMAP).write_text("roadmap\n")
        git_out(root, "add", roadmap.ROADMAP)
        git_out(root, "commit", "-m", "roadmap")
    calls = []
    script = Script()

    async def driver(c, log):
        events = c.journal.read()
        terminal = [e.ticket for e in events if e.type == EventType.STATE_TRANSITION and e.body.get("to") == "merged"]
        calls.append((roadmap.settles(events), terminal[-1] if terminal else None, list(script.calls)))

    monkeypatch.setattr(cli, "build_driver", lambda: driver)
    assert cli.main(["engine", "drain"], cwd=root, env=ENV, clock=Clock(), pipeline=script) == 0
    assert calls == ([(0, None, []), (1, "one", ["one"]), (2, "two", ["one", "two"])] if present else [])
