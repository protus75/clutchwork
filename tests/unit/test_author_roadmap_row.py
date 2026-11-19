"""Roadmap message and Author policy coverage."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from clutch import author, policy
from clutch.box import Box, Message, RoadmapRow
from clutch.config import BOX_POLICY_DEFAULTS
from clutch.seams import LocalFileSystem
from tests.fakes import FakeJournal


def row():
    return RoadmapRow(number=90, release="0.2", stem="sample-row", owner="engine", kind="feature", priority="P1", content="Build it", plan="docs/sample-plan.md")


def test_roadmap_row_message_shape(tmp_path):
    box = Box(tmp_path / "box", LocalFileSystem())
    id, _ = box.enqueue(message_class="roadmap_row", origin="roadmap/sample-row", summary="row text", roadmap_row=row())
    item = box.get(id)
    assert item.roadmap_row == row()
    data = item.model_dump()
    data["roadmap_row"] = None
    with pytest.raises(ValidationError):
        Message.model_validate(data)
    data.update(message_class="suggestion", roadmap_row=row())
    with pytest.raises(ValidationError):
        Message.model_validate(data)
    data.pop("roadmap_row")
    box.path(item).write_text(Message.model_validate(data).model_dump_json(exclude={"roadmap_row"}))
    assert box.get(id).roadmap_row is None


def test_roadmap_row_ignores_only_the_baseline():
    config = SimpleNamespace(engine_plane_safety_inventory=["config.yaml"], box_policy=dict(BOX_POLICY_DEFAULTS))

    def state(row="roadmap_row", fence=("clutch/author.py",), gate_bypass=(), go=False, reopen=False):
        return policy.start_state(config, row=row, fence=fence, gate_bypass=gate_bypass, go=go, reopen=reopen)

    assert state() == "confirmed"
    assert state(row="failure_report") == "draft"
    assert state(reopen=True) == "draft"
    assert state(gate_bypass=["scope_fence"]) == "draft"
    assert state(fence=["config.yaml"]) == "draft"
    config.engine_plane_safety_inventory = []
    assert state() == "draft"
    config.engine_plane_safety_inventory = ["config.yaml"]
    config.box_policy["roadmap_row"] = "draft"
    assert state(go=True) == "draft"


def test_plan_excerpt():
    short = "a" * 39999
    assert author.plan_excerpt(short) == short
    target = "## Target design\n```\n## Role: x\n```\nafter"
    where = "## Where each piece lives\nhere"
    text = "## Status\n" + "x" * 40000 + "\n" + target + "\n## Risks\nno\n" + where + "\n## Open decisions\nno"
    assert author.plan_excerpt(text) == target + "\n\n" + where
    note = author.plan_excerpt("unique-plan-line\n" * 4000)
    assert all(part in note for part in ("Target design", "Where each piece lives", "40,000"))
    assert "unique-plan-line" not in note


def test_gate_holds_roadmap_row_identity(tmp_path, monkeypatch):
    box = Box(tmp_path / "box", LocalFileSystem())
    id, _ = box.enqueue(message_class="roadmap_row", origin="row", summary="build", roadmap_row=row())
    gate = author.AuthorGate(SimpleNamespace(repo=tmp_path, journal=FakeJournal()), "roadmap_row")
    gate.message = box.get(id)
    monkeypatch.setattr(author, "validate_ticket", lambda stem, text, repo: SimpleNamespace(frontmatter=SimpleNamespace(kind=text.split()[0], priority=text.split()[1])))
    evidence = tmp_path / "tickets/sample-row/evidence/hand.txt"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("evidence")
    for stem, text, expected in [("other-row", "feature P1", "sample-row"), ("sample-row", "chore P1", "feature"), ("sample-row", "feature P2", "P1")]:
        report = gate.check(author.AuthorReply(stem=stem, ticket=text), tmp_path)
        assert report.verdict == "fail" and any(expected in f.message for f in report.findings)
        assert evidence.read_text() == "evidence"
    assert gate.check(author.AuthorReply(stem="sample-row", ticket="feature P1"), tmp_path).verdict == "pass"
    (evidence.parent.parent / "ticket.md").write_text("existing")
    assert any("already exists" in f.message for f in gate.check(author.AuthorReply(stem="sample-row", ticket="feature P1"), tmp_path).findings)
    (evidence.parent.parent / "ticket.md").unlink()
    other = author.AuthorGate(gate.checkout)
    assert any("already exists" in f.message for f in other.check(author.AuthorReply(stem="sample-row", ticket="feature P1"), tmp_path).findings)


@pytest.mark.asyncio
async def test_author_embeds_row_and_plan(tmp_path, monkeypatch):
    from pathlib import Path

    from tests.unit.test_retro_recurrence import message

    plan = tmp_path / "docs/sample-plan.md"
    plan.parent.mkdir()
    plan.write_text("the tracked plan")
    tracked = ["docs/sample-plan.md"]
    seen = []
    calls = []

    async def ls_files(repo):
        return tracked

    async def decline(checkout, driver, box, item, evidence):
        seen.append(evidence)
        return "declined"

    async def run(stage, *args, **kwargs):
        calls.append(stage.render(None, []))
        raise StopAsyncIteration

    async def open_tickets(checkout):
        return "open"

    read_text = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self: "spec" if self.name in {"author.md", "host-authoring.md"} else read_text(self))
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "render", lambda spec, inputs: inputs)
    monkeypatch.setattr(author, "list_open_tickets", open_tickets)
    monkeypatch.setattr(author, "failure_declined", decline)
    checkout = SimpleNamespace(repo=tmp_path, git=SimpleNamespace(ls_files=ls_files), journal=FakeJournal(), config=SimpleNamespace(routing_default_tier="medium"))
    box = SimpleNamespace(root=tmp_path / "box")
    original = message().model_copy(update={"message_class": "roadmap_row", "roadmap_row": row(), "verdict": SimpleNamespace(rationale="row")})
    with pytest.raises(StopAsyncIteration):
        await author.author(checkout, SimpleNamespace(run=run), box, original, 1)
    assert calls[-1]["roadmap_row"] == row().model_dump_json()
    assert calls[-1]["plan"] == "the tracked plan"
    failure = original.model_copy(update={"message_class": "failure_report", "roadmap_row": None})
    with pytest.raises(StopAsyncIteration):
        await author.author(checkout, SimpleNamespace(run=run), box, failure, 1)
    assert calls[-1]["roadmap_row"] == calls[-1]["plan"] == "none"
    tracked.clear()
    assert await author.author(checkout, SimpleNamespace(run=run), box, original, 1) == "declined"
    assert "docs/sample-plan.md" in seen[-1] and "90" in seen[-1] and "sample-row" in seen[-1]
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_author_commit_carries_row_evidence(tmp_path, monkeypatch):
    from pathlib import Path

    from tests.unit.test_retro_recurrence import message

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/sample-plan.md").write_text("plan")
    listings, commits, resolutions = [], [], []

    async def ls_files(repo):
        return ["docs/sample-plan.md"]

    async def git_run(repo, *args):
        listings.append(args)
        return "tickets/sample-row/evidence/hand.txt\0"

    async def commit(repo, msg, *, only):
        commits.append(only)
        return "sha"

    async def run(stage, *args, **kwargs):
        reply = author.AuthorReply(stem="sample-row", ticket="ticket")
        await stage.review(reply, 1)
        return SimpleNamespace(outcome="ok", artifact=reply)

    async def effect(action, **kwargs):
        return await action()

    async def review(*args, **kwargs):
        return SimpleNamespace(verdict="approve", findings=[], calls=1, ticket_sha="sha", provider="fake", model="fake", spec_version="1.0")

    async def open_tickets(checkout):
        return "none"

    read_text = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self: "spec" if self.name in {"author.md", "host-authoring.md"} else read_text(self))
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "list_open_tickets", open_tickets)
    monkeypatch.setattr(author, "review_ticket", review)
    monkeypatch.setattr(author.AuthorGate, "check", lambda *args: SimpleNamespace(verdict="pass"))
    monkeypatch.setattr(author, "stamp", lambda text, *args: text)
    monkeypatch.setattr(author, "validate_ticket", lambda *args: SimpleNamespace(scope_fence=(), frontmatter=SimpleNamespace(gate_bypass=[])))
    monkeypatch.setattr(author, "resolve_baseline", lambda *args, **kwargs: SimpleNamespace(binds=False))
    checkout = SimpleNamespace(
        repo=tmp_path,
        git=SimpleNamespace(ls_files=ls_files, _run=git_run, commit=commit),
        fs=LocalFileSystem(),
        journal=FakeJournal(),
        config=SimpleNamespace(
            state_dir=tmp_path, review=SimpleNamespace(coverage_map=None), routing_default_tier="medium", engine_plane_safety_inventory=["config.yaml"], box_policy=dict(BOX_POLICY_DEFAULTS)
        ),
    )
    box = SimpleNamespace(root=tmp_path / "box", resolve=lambda id, resolution: resolutions.append(resolution))
    driver = SimpleNamespace(run=run, effects=SimpleNamespace(run=effect))
    item = message().model_copy(update={"message_class": "roadmap_row", "roadmap_row": row(), "verdict": SimpleNamespace(rationale="row")})
    await author.author(checkout, driver, box, item, 1)
    assert "--others" in listings[0] and "--exclude-standard" in listings[0]
    assert commits[0] == ["tickets/sample-row/ticket.md", "tickets/sample-row/evidence/hand.txt"]
    assert (resolutions[0].kind, resolutions[0].link) == ("ticket", "sample-row")
    (tmp_path / "tickets/sample-row/ticket.md").unlink()
    await author.author(checkout, driver, box, item.model_copy(update={"message_class": "failure_report", "roadmap_row": None}), 1)
    assert len(listings) == 1
    assert commits[1] == ["tickets/sample-row/ticket.md"]
