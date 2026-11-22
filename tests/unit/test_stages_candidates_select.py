# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks how stages.check_candidates picks graphics candidates per artifact. Covers the evidence commit message, parking an undecided or partial selection, forbidden diff paths, rubric criteria, and the missing-baseline park.
# relates: [clutch/artifacts.py, clutch/baseline.py, clutch/llmeffect.py, clutch/stages.py, clutch/visual.py]
# owner: engine
# verified: 73ec5da9
# hash: 673df889176e7a2bccc9144585cbbcfdc4037bc9befcefce216e363412cae111
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import stages, visual
from clutch.artifacts import Cost, StageResult
from clutch.baseline import BaselineResolution
from clutch.llmeffect import llm_key, scoped_seq
from tests.git_fake import GitFake


def fixture(monkeypatch, replies, artifacts=("out.png",), changed=()):
    root = Path("/virtual")
    work = root / "work"
    files = {root / "tickets/work/ticket.md": b"ticket"}
    for i in range(len(artifacts)):
        for k in range(3):
            files[work / f".clutch/renders/work/a{i}/cand-{k}.png"] = f"{i}-{k}".encode()
    writes = {}

    def read(path):
        if path not in files and path not in writes:
            raise FileNotFoundError(path)
        return writes.get(path, files.get(path))

    fs = SimpleNamespace(read_bytes=read, write=lambda path, data: writes.update({path: data}))
    git = GitFake(diff_names=list(changed))
    scopes = []

    async def run(stage, consumed, **kwargs):
        scopes.append(kwargs["key_scope"])
        verdict, count, attempts = replies.pop(0)
        rows = [visual.Row(id=str(j), verdict="pass" if j < count else "fail", observation="observed") for j in range(5)]
        return StageResult(outcome="ok", artifact=visual.Reply(rows=rows, verdict=verdict, reason="observed"), findings=[], cost=Cost(attempts=attempts))

    driver = SimpleNamespace(run=run, journal=SimpleNamespace(read=lambda: []), spool=SimpleNamespace(root=root / "spool"))
    ctx = SimpleNamespace(repo=root, worktree=lambda _: work, fs=fs, git=git, driver=driver, config=SimpleNamespace(state_dir=root, graphics=SimpleNamespace(judge_samples=1)), specs_dir=None)
    ticket = SimpleNamespace(
        stem="work",
        sections={"Render": "- mode: generate\n" + "".join(f"- artifact: {a}\n" for a in artifacts), "Acceptance criteria": "", "Goal / Why": "goal"},
        frontmatter=SimpleNamespace(kind="graphics", agent_tier="medium", agent_effort="medium"),
        expected_minutes=2,
        stuck_minutes=4,
    )
    monkeypatch.setattr(stages, "resolve_visual_baseline", lambda *args, **kwargs: BaselineResolution("GO"))
    monkeypatch.setattr(stages, "_spec", lambda *args: None)
    monkeypatch.setattr(stages.images, "judge", lambda path, inputs: ["bad"] if path.name == "cand-2.png" else [])
    monkeypatch.setattr(stages.images, "scores", lambda *args: (0.8, None))
    monkeypatch.setattr(stages.images, "side_by_side", lambda *args: b"preview")
    return ctx, ticket, writes, scopes


def test_select_two_artifacts_and_evidence(monkeypatch):
    ctx, ticket, writes, scopes = fixture(monkeypatch, [("accept", 4, 2), ("reject", 1, 1), ("reject", 1, 1), ("accept", 3, 1)], ("one.png", "two.png"))
    assert asyncio.run(stages.check_candidates(ctx, ticket, 0)) == []
    assert scopes == ["a0c0s0", "a0c1s0", "a1c0s0", "a1c1s0"]
    assert writes[Path("/virtual/work/one.png")] == b"0-0"
    assert writes[Path("/virtual/work/two.png")] == b"1-1"
    [(_, args, kwargs)] = [call for call in ctx.git.calls if call[0] == "commit"]
    message = args[1]
    assert "one.png: candidate 0, evidence " + llm_key("work", scoped_seq("a0c0s0", 0), "review_visual", 0, 2) in message
    assert "two.png: candidate 1, evidence " + llm_key("work", scoped_seq("a1c1s0", 0), "review_visual", 0, 1) in message
    assert kwargs["only"] == ["one.png", "two.png"]
    assert len([call for call in ctx.git.calls if call[0] == "commit"]) == 1


@pytest.mark.parametrize("replies", [[("accept", 4, 1), ("accept", 4, 1)], [("accept", 4, 1), ("unsure", 1, 1)]])
def test_park_without_commit(monkeypatch, replies):
    ctx, ticket, writes, _ = fixture(monkeypatch, replies)
    findings = asyncio.run(stages.check_candidates(ctx, ticket, 0))
    assert [f.code for f in findings] == ["visual_undecided"]
    assert "out.png" in findings[0].message
    assert not [call for call in ctx.git.calls if call[0] == "commit"]
    assert Path("/virtual/work/out.png") not in writes


def test_partial_selection_parks(monkeypatch):
    ctx, ticket, writes, _ = fixture(monkeypatch, [("accept", 4, 1), ("reject", 1, 1), ("accept", 4, 1), ("accept", 4, 1)], ("one.png", "two.png"))
    findings = asyncio.run(stages.check_candidates(ctx, ticket, 0))
    assert "two.png" in findings[0].message and "one.png" not in findings[0].message
    assert not [call for call in ctx.git.calls if call[0] == "commit"] and Path("/virtual/work/one.png") not in writes


def test_no_survivors_and_forbidden_diff(monkeypatch):
    ctx, ticket, _, _ = fixture(monkeypatch, [])
    monkeypatch.setattr(stages.images, "judge", lambda *args: ["bad"])
    assert asyncio.run(stages.check_candidates(ctx, ticket, 0))[0].code == "visual_undecided"
    for forbidden in ("out.png", ".clutch/renders/work/a0/cand-0.png"):
        ctx.git._overrides["diff_names"] = [forbidden]
        assert asyncio.run(stages.check_candidates(ctx, ticket, 0))[0].code == "candidate_paths"
    assert not [call for call in ctx.git.calls if call[0] == "commit"]


def test_rubric_uses_numbered_and_continued_criteria_for_each_artifact(monkeypatch):
    ctx, ticket, _, _ = fixture(monkeypatch, [])
    ticket.sections["Acceptance criteria"] = "1. visual: out.png: red\n   square\n2. visual: other.png: blue circle"
    seen = []

    async def run(stage, consumed, **kwargs):
        ids = ["red square", "identity", "placement", "lighting", "unchanged", "artifacts"]
        reply = visual.Reply(rows=[visual.Row(id=i, verdict="pass", observation="seen") for i in ids], verdict="accept", reason="seen")
        seen.append((await stage.review(reply, 1)).verdict)
        return StageResult(outcome="ok", artifact=reply, findings=[], cost=Cost(attempts=1))

    ctx.driver.run = run
    asyncio.run(stages.check_candidates(ctx, ticket, 0))
    assert seen == ["pass", "pass"]


def test_missing_baseline_parks_before_judging(monkeypatch):
    ctx, ticket, writes, scopes = fixture(monkeypatch, [])
    monkeypatch.setattr(stages, "resolve_visual_baseline", lambda *args, **kwargs: BaselineResolution("ABSENT"))
    findings = asyncio.run(stages.check_candidates(ctx, ticket, 0))
    assert [f.code for f in findings] == ["visual_undecided"]
    assert "visual_baseline" in findings[0].message
    assert not scopes and not writes and not [call for call in ctx.git.calls if call[0] == "commit"]


def test_forbidden_paths_precede_baseline(monkeypatch):
    ctx, ticket, _, _ = fixture(monkeypatch, [], changed=("out.png",))

    def unexpected(*args, **kwargs):
        raise AssertionError("baseline read before forbidden paths")

    monkeypatch.setattr(stages, "resolve_visual_baseline", unexpected)
    assert asyncio.run(stages.check_candidates(ctx, ticket, 0))[0].code == "candidate_paths"
