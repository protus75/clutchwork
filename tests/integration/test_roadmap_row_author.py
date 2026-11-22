"""Recorded roadmap verdict travels through Author with its evidence."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that a recorded triage verdict on a roadmap_row goes through Author with its plan and evidence and produces a confirmed ticket under NO_GO
# relates: [clutch/__main__.py, clutch/box.py, clutch/config.py, clutch/journal.py, clutch/llm.py, clutch/policy.py, clutch/seams.py, clutch/specs/__init__.py]
# owner: clutch/author.py
# verified: 79efeedb
# hash: d7d9c21b8455ae9ab405b5b8984af9bea20fb2c21be286cbdcf5100cdab3d900

import json
from pathlib import Path

import pytest

from clutch.__main__ import main
from clutch.box import Box, Resolution, RoadmapRow, Verdict
from clutch.config import load_config
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM
from clutch.policy import baseline_identity
from clutch.seams import LocalFileSystem
from clutch.specs import load_spec
from tests.cli_helpers import ENV, git_out
from tests.drain_helpers import Clock, make_root
from tests.integration.test_author import _routes, block, requisition_reply
from tests.loop_helpers import author_reply

pytestmark = pytest.mark.disk_io_skip


def test_triage_authors_roadmap_row_confirmed_under_no_go(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    _routes(root)
    config = root / "config.yaml"
    config.write_text(config.read_text().replace("engine_plane_safety_inventory: []", "engine_plane_safety_inventory: [config.yaml]"))
    plan = root / "docs/sample-plan.md"
    plan.parent.mkdir()
    plan.write_text("A unique plan.\n")
    git_out(root, "add", "docs/sample-plan.md")
    git_out(root, "commit", "-m", "plan")
    evidence = root / "tickets/sample-row/evidence/hand.txt"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("hand evidence")
    cfg = load_config(None, cwd=root)
    journal = Journal(cfg.state_dir, Clock())
    journal.append(EventType.SIGNAL, {"signal": "review_baseline", "verdict": "NO_GO", "identity": baseline_identity(cfg)})
    box = Box(cfg.state_dir / "box", LocalFileSystem())
    row = RoadmapRow(number=90, release="0.2", stem="sample-row", owner="engine", kind="feature", priority="P2", content="Build it", plan="docs/sample-plan.md")
    id, _ = box.enqueue(message_class="roadmap_row", origin="roadmap/sample-row", summary="build it", roadmap_row=row)
    version = load_spec((Path(__file__).resolve().parents[2] / "clutch/specs/triage.md").read_text()).meta.version
    box.record_verdict(id, Verdict(verdict="author", produced_by_spec_version=version, rationale="approved row"))
    llm = FakeLLM([author_reply("sample-row"), requisition_reply("approve")])
    monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *args, **kwargs: llm)
    assert main(["box", "triage", id], cwd=root, env=ENV, clock=Clock()) == 0
    prompt = next(r.rendered for r in llm.requests if r.surface == "author")
    assert json.loads(block(prompt, "roadmap_row")) == row.model_dump()
    assert block(prompt, "plan") == "A unique plan."
    assert git_out(root, "log", "-1", "--format=%s").strip() == "clutch(sample-row): ticket"
    assert set(git_out(root, "show", "--format=", "--name-only", "HEAD").split()) == {"tickets/sample-row/ticket.md", "tickets/sample-row/evidence/hand.txt"}
    text = (root / "tickets/sample-row/ticket.md").read_text()
    assert "state: confirmed" in text and "source: box:roadmap_row" in text
    assert box.get(id).resolution == Resolution(kind="ticket", link="sample-row")
    assert all(request.surface != "triage" for request in llm.requests)
